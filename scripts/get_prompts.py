import os
import json


def find_experiment_jsons(base_dir="experiments"):
    prompts = []

    # Get sorted list of experiment directories
    experiment_dirs = sorted(
        [d for d in os.listdir(base_dir) if d.startswith(
            "experiment_") and os.path.isdir(os.path.join(base_dir, d))],
        key=lambda x: int(x.split("_")[-1])  # Extract numeric part for sorting
    )

    # Iterate over sorted directories
    for folder in experiment_dirs:
        json_path = os.path.join(base_dir, folder, "experiment.json")

        # Check if the file exists
        if os.path.isfile(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                    # Extract the 'prompt' field if available
                    if "prompt" in data:
                        prompts.append(len(data["plans"]))
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error reading {json_path}: {e}")

    return prompts


if __name__ == "__main__":
    extracted_prompts = find_experiment_jsons()
    for prompt in extracted_prompts:
        print(prompt)
