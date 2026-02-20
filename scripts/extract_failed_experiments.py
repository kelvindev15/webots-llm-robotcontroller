import json
import os
from pathlib import Path

# Directory containing the experiment files
experiments_dir = Path("/Users/kelvin/Documents/Projects/webots_robot_controllers/experiments")

# List to store failed experiments
failed_experiments = []

# Get all JSON files starting with "experiment_gemini-2_0-flash"
json_files = sorted(experiments_dir.glob("experiment_gemini-2_0-flash*.json"))

print(f"Found {len(json_files)} files to process...")

for json_file in json_files:
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Extract required information
        experiment_info = {
            "filename": json_file.name,
            "id": data.get("id"),
            "model": data.get("model"),
            "prompt": data.get("prompt"),
            "initialRobotPose": data.get("initialRobotPose"),
            "abortionReason": data.get("abortionReason"),
            "simulationAborted": data.get("simulationAborted"),
            "goalCompleted": data.get("goalCompleted"),
            "numIterations": len(data.get("iterations", []))
        }
        
        failed_experiments.append(experiment_info)
        
    except Exception as e:
        print(f"Error processing {json_file.name}: {e}")

# Save to failed_experiment.json
output_file = experiments_dir.parent / "failed_experiment.json"
with open(output_file, 'w') as f:
    json.dump(failed_experiments, f, indent=2)

print(f"\nProcessed {len(failed_experiments)} experiments")
print(f"Results saved to: {output_file}")

# Print summary statistics
aborted_count = sum(1 for exp in failed_experiments if exp.get("simulationAborted"))
completed_count = sum(1 for exp in failed_experiments if exp.get("goalCompleted"))
print(f"\nSummary:")
print(f"- Simulations aborted: {aborted_count}")
print(f"- Goals completed: {completed_count}")
print(f"- Total experiments: {len(failed_experiments)}")
