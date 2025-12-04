from flask import Flask, render_template, request, jsonify
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor
from tasks import process_text
import json
import requests

POETREE_API_BASE = "https://versologie.cz/poetree/api"

app = Flask(__name__)

# Store task results and status in memory
task_results = {}
task_status = {}

# Thread pool for background tasks
executor = ThreadPoolExecutor(max_workers=4)

# Load poem metadata for dropdown labels
poems_metadata = {}
try:
    with open("static/poems.json", "r", encoding="utf-8") as f:
        poems_metadata = json.load(f)
        print(f"Loaded {len(poems_metadata)} poems metadata entries")
except Exception as e:
    print(f"Could not load poems metadata: {e}")


def fetch_poem_text_from_poetree(title: str, author: str) -> str:
    """Fetch full poem text from PoeTree API by title/author.

    This looks up poems via `/poems` to find the ID, then requests `/poem/{id}`
    and returns the `body` field. Returns empty string if not found or on error.
    """
    try:
        list_url = f"{POETREE_API_BASE}/poems"
        resp = requests.get(list_url, timeout=20)
        resp.raise_for_status()
        poems = resp.json()
        if not isinstance(poems, list):
            return ""

        t_norm = (title or "").strip().lower()
        a_norm = (author or "").strip().lower()

        match_id = None
        for p in poems:
            pt = (p.get("title") or "").strip().lower()
            pa = (p.get("author") or "").strip().lower()
            if pt == t_norm and (not a_norm or pa == a_norm):
                match_id = p.get("id")
                break

        if match_id is None:
            return ""

        detail_url = f"{POETREE_API_BASE}/poem/{match_id}"
        dresp = requests.get(detail_url, timeout=20)
        dresp.raise_for_status()
        detail = dresp.json()
        body = detail.get("body", "")
        return body if isinstance(body, str) else ""
    except Exception as e:
        print(f"PoeTree fetch error: {e}")
        return ""


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/submit", methods=["POST"])
def submit_task():
    """Submit a computational task to the background worker"""
    data = request.get_json()
    user_input = data.get("input", "")

    if not user_input:
        return jsonify({"error": "No input provided"}), 400

    # If input is a dropdown label, try to resolve to full text
    resolved_text = user_input
    meta = poems_metadata.get(user_input)
    if meta:
        text_field = meta.get("text")
        if isinstance(text_field, str) and text_field.strip():
            resolved_text = text_field
        else:
            # Parse title and author from label "Title - Author"
            try:
                title, author = user_input.split(" - ", 1)
            except ValueError:
                title, author = user_input, ""
            fetched = fetch_poem_text_from_poetree(title, author)
            if fetched.strip():
                resolved_text = fetched

    # Generate unique task ID
    task_id = str(uuid.uuid4())

    # Mark task as processing
    task_status[task_id] = "processing"

    # Submit task to thread pool
    executor.submit(process_text, resolved_text, task_id, task_results, task_status)

    return jsonify({"task_id": task_id, "status": "processing"})


@app.route("/result/<task_id>")
def get_result(task_id):
    """Get the result of a computational task"""
    # Check if result is available
    result = task_results.get(task_id)
    status = task_status.get(task_id, "unknown")

    if result:
        return jsonify({"task_id": task_id, "status": "completed", "result": result})
    else:
        return jsonify({"task_id": task_id, "status": status})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
