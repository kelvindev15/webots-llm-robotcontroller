from datetime import datetime
import json
from langsmith import Client
import dotenv
import numpy as np

dotenv.load_dotenv()

client = Client()
def calculate_duration(start_time: datetime, end_time: datetime):
    """
    Calculate the duration between start_time and end_time in seconds.
    """

    duration = (end_time - start_time).total_seconds()
    return duration

def get_iteration_duration_by_experiment_id(experiment_id: str):
    """
    Get iteration durations for runs with the specified experiment_id.
    """
    runs = list(client.list_runs(project_name="webots-robot-controllers", filter=f'and(eq(metadata_key, "experiment_id"), eq(metadata_value, "{experiment_id}"))'))
    return np.array([calculate_duration(run.start_time, run.end_time) for run in runs])


def get_experiment_data(directory):
    """
    Read all JSON files in the given directory and extract experiment data.
    """
    import json
    from pathlib import Path
    from collections import defaultdict
    import re

    def extract_experiment_info(filename):
        """
        Extract position, model, and timestamp from the filename.
        Expected filename format: {id}_pos_{position}_experiment_{model}_{timestamp}.json
        """
        try:
            parts = filename.rstrip('.json').split('_')
            # Find the index of 'pos' to get the position
            pos_index = parts.index('pos')
            position = parts[pos_index + 1]
            
            # Find the index of 'experiment' to get the model
            experiment_index = parts.index('experiment')
            # Model is everything from experiment_index + 1 to the last part (timestamp)
            # Join model parts (e.g., gemini-2, 0-flash)
            model_parts = parts[experiment_index + 1:-1]
            model = '_'.join(model_parts)
            
            # Timestamp is the last part
            timestamp = parts[-1]
            return position, model, timestamp
        except (IndexError, ValueError):
            return None, None, None

    results = defaultdict(lambda: defaultdict(list))
    base_path = Path(directory)

    for task_dir in sorted(base_path.iterdir()):
        if not task_dir.is_dir() or not(task_dir.name in ["Ablation_ZeroImage"]):
            continue
        task_name = task_dir.name
        
        # Get all JSON files in this task directory
        pattern = re.compile(r'^(\d+)_pos_.*\.json$')
        json_files = []
        for p in task_dir.glob('*_pos_*.json'):
            m = pattern.match(p.name)
            if m:
                num = int(m.group(1))
                if 380 <= num <= 500:
                    json_files.append(p)
        print("--------------------------------------------")
        print("Task name:", task_name)
        print("--------------------------------------------")
        for json_file in sorted(json_files):
            try:
                # Extract position and run info from filename
                position, model, timestamp = extract_experiment_info(json_file.name)
                if position is None:
                    continue
                
                # Read the JSON file
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                # Get number of iterations
                num_iterations = data.get('numberOfIterations', 0)
                durations = get_iteration_duration_by_experiment_id(data.get('id', '')) if data.get('id') else np.array([])
                average_duration = np.mean(durations) if durations.size > 0 else None
                total_duration = np.sum(durations) if durations.size > 0 else None
                duration_std = np.std(durations) if durations.size > 0 else None
                json_errors = data.get("jsonErrors", None)
                safety_triggers = data.get("safetyTriggers", None)
                goal_completed = data.get("goalCompleted", None)
                abortion_reason = data.get("abortionReason", None)
                # Store the result
                run_info = {
                    'filename': json_file.name,
                    'timestamp': timestamp,
                    'iterations': num_iterations,
                    'model': model,
                    'average_duration': np.mean(durations) if durations.size > 0 else None,
                    'total_duration': np.sum(durations) if durations.size > 0 else None,
                    'duration_std': np.std(durations) if durations.size > 0 else None,
                    'json_errors': data.get("jsonErrors", None),
                    'safety_triggers': data.get("safetyTriggers", None),
                    'goal_completed': data.get("goalCompleted", None),
                    'abortion_reason': data.get("abortionReason", None),
                }
                
                results[task_name][position].append(run_info)
                print(average_duration, duration_std, total_duration, json_errors, safety_triggers, goal_completed, abortion_reason, sep="\t")
            except Exception as e:
                print(f"Error processing {json_file}: {e}")
    
    return results

json.dump(get_experiment_data('experiments'), open('experiment_data.json', 'w'), indent=4)

