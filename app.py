from flask import Flask, render_template, request, jsonify
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor
from tasks import process_text

app = Flask(__name__)

# Store task results and status in memory
task_results = {}
task_status = {}

# Thread pool for background tasks
executor = ThreadPoolExecutor(max_workers=4)


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

    # Generate unique task ID
    task_id = str(uuid.uuid4())

    # Mark task as processing
    task_status[task_id] = "processing"

    # Submit task to thread pool
    executor.submit(process_text, user_input, task_id, task_results, task_status)

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
