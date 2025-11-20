from poetry_analysis.rhyme_detection import tag_text
from poetry_analysis.alliteration import extract_alliteration, find_line_alliterations
from poetry_analysis.anaphora import extract_poem_anaphora


def process_text(user_input, task_id, task_results, task_status):
    """Annotate the input text with lyrical repetition patterns."""
    print(f"Processing task {task_id} with input: {user_input}")
    try:
        result = {
            "text": user_input,
            "end_rhymes": list(tag_text(user_input)),
            "alliteration": list(extract_alliteration(user_input.split("\n"))),
            "anaphora": list(extract_poem_anaphora(user_input)),
        }
        # Store result
        task_results[task_id] = result
        task_status[task_id] = "completed"

        print(f"Task {task_id} completed successfully")
        return result
    except Exception as e:
        error_result = {"error": str(e), "original_input": user_input}
        task_results[task_id] = error_result
        task_status[task_id] = "error"
        return error_result
