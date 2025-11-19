import time
import math


def process_computation(user_input, task_id, task_results, task_status):
    """
    Perform computational operations on user input.
    This is a placeholder - customize based on your needs.
    """
    print(f"Processing task {task_id} with input: {user_input}")

    # Simulate complex computation
    time.sleep(3)

    try:
        # Example: Parse input and perform calculations
        # This assumes user_input is a number or mathematical expression

        # Convert to float if possible
        try:
            value = float(user_input)
            result = {
                "original_input": user_input,
                "square": value**2,
                "square_root": math.sqrt(abs(value)) if value >= 0 else None,
                "factorial": math.factorial(int(value))
                if value >= 0 and value == int(value) and value <= 20
                else None,
                "sine": math.sin(value),
                "cosine": math.cos(value),
            }
        except ValueError:
            # If not a number, perform text analysis
            result = {
                "original_input": user_input,
                "length": len(user_input),
                "word_count": len(user_input.split()),
                "uppercase": user_input.upper(),
                "reversed": user_input[::-1],
                "char_frequency": {
                    char: user_input.count(char) for char in set(user_input)
                },
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
