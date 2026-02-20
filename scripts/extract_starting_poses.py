#!/usr/bin/env python3
"""
Extract robot starting poses from experiment files and save them to a JSON file.
Each experiment is saved with its task, target position, and starting pose.
"""

import os
import json
import glob
from pathlib import Path

# Target positions and labels
targets = [ 
    (9.157059997836008, -3.477350015014757, "FIRE_EXTINGUISHER"),
    (-4.3, 1.41119, "PLASTIC_CRATE"),
    (8.4218847, 2.1373536, "OIL_BARREL"),
    (-3.05, -12.1, "WOODEN_PALLET"),
    (-5.2560137, -11.74814, "PALLET_STACK"),
    (-0.23882837, -4.8402928, "TABLE"),
    (0.070787217, -11.12746, "WOODEN_BOX"),
    (-0.46, 3.84, "OPEN_CABINET"),
    (1.49, 3.84, "CLOSED_CABINET"),
    (9.201, 0.17, "STAIRS"),
]

target_map = {
        'pile of pallets': 'PALLET_STACK',
        'carry some beers': 'PLASTIC_CRATE',
        'red box': 'PLASTIC_CRATE',
        'oil barrels': 'OIL_BARREL',
        'some stairs': 'STAIRS',
        'dark brown boxes': 'WOODEN_BOX',
        'fire extinguisher': 'FIRE_EXTINGUISHER',
        'fire': 'FIRE_EXTINGUISHER',
    }

def extract_simulation_id(filename: str) -> int:
    """
    Extract the simulation ID (first number) from the experiment filename.
    
    Example: "1_pos_1_experiment_gemini-2_0-flash_20251118-095910.json" -> 1
    """
    basename = os.path.basename(filename)
    # Extract the first number before the first underscore
    first_part = basename.split('_')[0]
    return int(first_part)


def extract_experiment_id(filename: str) -> str:
    """
    Extract a unique experiment ID from the filename.
    Uses the full filename (without extension) to keep experiments distinct.
    
    Example: "1_pos_1_experiment_gemini-2_0-flash_20251118-095910.json" 
             -> "1_pos_1_experiment_gemini-2_0-flash_20251118-095910"
    """
    basename = os.path.basename(filename)
    return os.path.splitext(basename)[0]


def extract_task_from_path(filepath: str) -> str:
    """
    Extract the task name from the parent directory path.
    
    Example: ".../TASK_01_go_to_the_pile_of_pallets/..." -> "TASK_01_go_to_the_pile_of_pallets"
    """
    parent_dir = os.path.basename(os.path.dirname(filepath))
    return parent_dir


def find_target_for_task(task_name: str, prompt: str) -> dict:
    """
    Find the target position based on the task using the global target_map.
    
    Args:
        task_name: The task folder name (e.g., "TASK_01_go_to_the_pile_of_pallets")
        prompt: The prompt text (e.g., "Go to the pile of pallets")
    
    Returns a dict with the target name and position, or None if not found.
    """
    # Convert prompt to lowercase for matching
    prompt_lower = prompt.lower()
    
    # Try to find matching target using the target_map
    for keyword, target_name in target_map.items():
        if keyword in prompt_lower:
            # Find the target coordinates from the targets list
            for x, y, name in targets:
                if name == target_name:
                    return {
                        'name': name,
                        'x': x,
                        'y': y
                    }
    
    # If no specific target found, return None (for tasks like "look around", "360 turn")
    return None


def poses_are_similar(pose1: dict, pose2: dict, position_threshold: float = 0.01, rotation_threshold: float = 0.01) -> bool:
    """
    Check if two poses are similar using fuzzy comparison.
    
    Args:
        pose1, pose2: Dicts with 'position' and 'rotation' keys (each containing 3-4 element lists)
        position_threshold: Maximum distance between positions to consider them equal (in meters)
        rotation_threshold: Maximum difference in rotation components to consider them equal
    
    Returns True if poses are similar enough to be considered the same.
    """
    pos1 = pose1['position']
    pos2 = pose2['position']
    rot1 = pose1['rotation']
    rot2 = pose2['rotation']
    
    # Check position similarity (Euclidean distance)
    position_distance = sum((p1 - p2) ** 2 for p1, p2 in zip(pos1, pos2)) ** 0.5
    if position_distance > position_threshold:
        return False
    
    # Check rotation similarity (component-wise difference)
    rotation_distance = sum((r1 - r2) ** 2 for r1, r2 in zip(rot1, rot2)) ** 0.5
    if rotation_distance > rotation_threshold:
        return False
    
    return True


def extract_experiment_data(experiment_file: str) -> dict:
    """
    Extract all relevant data from an experiment JSON file.
    
    Returns a dict with pose, task, prompt, and target information.
    """
    with open(experiment_file, 'r') as f:
        experiment_data = json.load(f)
    
    initial_pose = experiment_data['initialRobotPose']['pose']
    task = extract_task_from_path(experiment_file)
    prompt = experiment_data.get('prompt', '')
    
    # Find the target for this task using the prompt
    target = find_target_for_task(task, prompt)
    
    return {
        'task': task,
        'prompt': prompt,
        'starting_pose': {
            'position': initial_pose['position'],
            'rotation': initial_pose['rotation']
        },
        'target': target
    }


def extract_all_experiments(experiments_dir: str) -> dict:
    """
    Extract data from all experiment files in the experiments directory.
    Only keeps experiments with simulation IDs in range(1, 320, 4): 1, 5, 9, 13, ..., 317
    
    Returns a dict mapping unique experiment ID to experiment data.
    """
    experiments = {}
    
    # Define the allowed simulation IDs
    allowed_sim_ids = set(range(1, 200, 4))
    
    # Find all JSON files in subdirectories (but not the metrics files in root)
    experiment_files = []
    for root, dirs, files in os.walk(experiments_dir):
        # Skip the root experiments directory
        if root == experiments_dir:
            continue
        
        for file in files:
            if file.endswith('.json') and not file.endswith('_metrics.json'):
                experiment_files.append(os.path.join(root, file))
    
    # Sort files to ensure consistent ordering
    experiment_files.sort()
    
    print(f"Found {len(experiment_files)} experiment files")
    print(f"Filtering to keep only simulation IDs: 1, 5, 9, 13, ... (every 4th)")
    
    skipped_count = 0
    for experiment_file in experiment_files:
        try:
            sim_id = extract_simulation_id(experiment_file)
            
            # Only process if simulation ID is in our allowed set
            if sim_id not in allowed_sim_ids:
                skipped_count += 1
                continue
            
            exp_id = extract_experiment_id(experiment_file)
            exp_data = extract_experiment_data(experiment_file)
            
            experiments[exp_id] = exp_data
            print(f"  Extracted data for experiment {exp_id} (sim_id: {sim_id})")
        except Exception as e:
            print(f"  Error processing {experiment_file}: {e}")
            continue
    
    print(f"\nSkipped {skipped_count} experiments (not in selected range)")
    
    return experiments


def main():
    # Path to the experiments directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    experiments_dir = project_root / "experiments"
    output_file = project_root / "frontier_exploration_starting_poses.json"
    
    print(f"Extracting experiment data from: {experiments_dir}")
    print(f"Output file: {output_file}")
    print()
    
    # Extract all experiment data
    experiments = extract_all_experiments(str(experiments_dir))
    
    # Sort by experiment ID for cleaner output
    sorted_experiments = dict(sorted(experiments.items()))
    
    # Save to JSON file
    with open(output_file, 'w') as f:
        json.dump(sorted_experiments, f, indent=2)
    
    print()
    print(f"Successfully extracted {len(sorted_experiments)} experiments")
    print(f"Saved to: {output_file}")
    print()
    
    # Print summary by task
    tasks = {}
    for exp_id, exp_data in sorted_experiments.items():
        task = exp_data['task']
        tasks[task] = tasks.get(task, 0) + 1
    
    print("Experiments by task:")
    for task, count in sorted(tasks.items()):
        print(f"  {task}: {count} experiments")


if __name__ == "__main__":
    main()
