"""
Cut frontier paths when the robot gets within 2.5m of the target.
Uses the target_map to determine target coordinates based on prompt keywords.
"""

import json
import os
import math
from pathlib import Path

# Target map with keywords and their coordinates
target_map = {
    'pile of pallets': (-5.2560137, -11.74814),
    'carry some beers': (-4.3, 1.41119),
    'red box': (-4.3, 1.41119),
    'oil barrels': (-3.05, -12.1),
    'some stairs': (9.201, 0.17),
    'dark brown boxes': (0.070787217, -11.12746),
    'fire extinguisher': (9.157059997836008, -3.477350015014757),
    'fire': (9.157059997836008, -3.477350015014757),
}

DISTANCE_THRESHOLD = 2.5  # meters


def calculate_distance(x1, y1, x2, y2):
    """Calculate Euclidean distance between two points."""
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def find_target_coordinates(prompt):
    """Find target coordinates based on prompt keywords."""
    prompt_lower = prompt.lower()
    for keyword, coords in target_map.items():
        if keyword in prompt_lower:
            return coords
    return None


def cut_path_at_target(path, target_x, target_y, threshold=DISTANCE_THRESHOLD):
    """
    Cut the path when the robot gets within threshold distance of the target.
    Returns the cut path and the index where it was cut.
    """
    for i, waypoint in enumerate(path):
        x = waypoint['x']
        y = waypoint['y']
        distance = calculate_distance(x, y, target_x, target_y)
        
        if distance <= threshold:
            # Cut the path at this point (include this waypoint)
            return path[:i + 1], i
    
    # If never within threshold, return the full path
    return path, len(path) - 1


def process_frontier_paths():
    """Process all frontier path files and cut them at target proximity."""
    
    # Load experiments list to get simulation_id to prompt mapping
    experiments_file = 'experiments/frontier_experiments_list.json'
    with open(experiments_file, 'r') as f:
        experiments = json.load(f)
    
    # Create a mapping from simulation_id to prompt
    sim_id_to_prompt = {}
    for exp in experiments:
        # Extract base simulation_id (without _pos_X suffix)
        sim_id = exp['simulation_id']
        sim_id_to_prompt[sim_id] = exp['prompt']
    
    # Process each frontier path file
    frontier_paths_dir = Path('experiments/frontier_paths')
    
    stats = {
        'total_files': 0,
        'files_cut': 0,
        'files_not_cut': 0,
        'files_no_target': 0,
        'waypoints_removed': 0
    }
    
    for filepath in sorted(frontier_paths_dir.glob('frontier_exploration_*.json')):
        stats['total_files'] += 1
        
        # Load the frontier path file
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Extract simulation_id from the filename or simulation_id field
        simulation_id_str = data.get('simulation_id', '')
        
        # Extract the numeric ID from strings like "1_pos_1_experiment_gemini-2_0-flash_20251118-095910"
        sim_id = int(simulation_id_str.split('_')[0])
        
        # Get the prompt for this simulation
        prompt = sim_id_to_prompt.get(sim_id)
        
        if not prompt:
            print(f"Warning: No prompt found for simulation_id {sim_id} in {filepath.name}")
            stats['files_no_target'] += 1
            continue
        
        # Find target coordinates based on prompt
        target_coords = find_target_coordinates(prompt)
        
        if not target_coords:
            print(f"Warning: No target found for prompt '{prompt}' in {filepath.name}")
            stats['files_no_target'] += 1
            continue
        
        target_x, target_y = target_coords
        
        # Get the original path
        original_path = data['path']
        original_length = len(original_path)
        
        # Cut the path
        cut_path, cut_index = cut_path_at_target(original_path, target_x, target_y)
        
        if len(cut_path) < original_length:
            waypoints_removed = original_length - len(cut_path)
            stats['files_cut'] += 1
            stats['waypoints_removed'] += waypoints_removed
            
            print(f"Cut {filepath.name}: {original_length} -> {len(cut_path)} waypoints "
                  f"(removed {waypoints_removed}) for prompt: '{prompt}'")
            
            # Update the data
            data['path'] = cut_path
            data['total_waypoints'] = len(cut_path)
            data['cut_at_index'] = cut_index
            data['cut_reason'] = f"Within {DISTANCE_THRESHOLD}m of target"
            data['target_coordinates'] = {'x': target_x, 'y': target_y}
            data['prompt'] = prompt
            
            # Save the modified file
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
        else:
            stats['files_not_cut'] += 1
            print(f"No cut needed for {filepath.name} (never within {DISTANCE_THRESHOLD}m of target)")
    
    # Print summary statistics
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total files processed: {stats['total_files']}")
    print(f"Files cut: {stats['files_cut']}")
    print(f"Files not cut (never close enough): {stats['files_not_cut']}")
    print(f"Files with no target found: {stats['files_no_target']}")
    print(f"Total waypoints removed: {stats['waypoints_removed']}")
    
    if stats['files_cut'] > 0:
        avg_removed = stats['waypoints_removed'] / stats['files_cut']
        print(f"Average waypoints removed per cut file: {avg_removed:.1f}")


if __name__ == '__main__':
    process_frontier_paths()
