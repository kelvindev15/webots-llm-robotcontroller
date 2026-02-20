import json
import os
import csv
from pathlib import Path
from typing import Dict, List, Tuple
from scripts.visualize_paths import visualize_frontier_path, obstacles

def load_json(filepath: str) -> Dict:
    """Load JSON data from file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def extract_pos_from_filename(filename: str) -> str:
    """Extract position number from filename (e.g., 'pos_1')."""
    parts = filename.split('_')
    for i, part in enumerate(parts):
        if part == 'pos' and i + 1 < len(parts):
            return f"pos_{parts[i+1]}"
    return None

def find_matching_frontier(task_filename: str, frontier_dir: Path) -> str:
    """Find the matching frontier exploration file for a task experiment.
    
    Mapping logic:
    - Experiments [1-4]_pos_1 -> frontier_exploration_1_pos_1
    - Experiments [5-8]_pos_2 -> frontier_exploration_5_pos_2
    - Experiments [9-12]_pos_3 -> frontier_exploration_9_pos_3
    - Experiments [13-16]_pos_4 -> frontier_exploration_13_pos_4
    - Experiments [17-20]_pos_5 -> frontier_exploration_17_pos_5
    And so on for subsequent groups...
    """
    # Extract experiment number from filename
    # Example: "1_pos_1_experiment_gemini-2_0-flash_20251118-095910.json"
    exp_num_str = task_filename.split('_')[0]
    
    try:
        exp_num = int(exp_num_str)
    except ValueError:
        return None
    
    # Calculate the base frontier number
    # For exp 1-4: base = 1, for exp 5-8: base = 5, etc.
    base_frontier_num = ((exp_num - 1) // 4) * 4 + 1
    
    # Extract position from filename (e.g., "pos_1")
    parts = task_filename.split('_')
    pos_idx = None
    for i, part in enumerate(parts):
        if part == 'pos' and i + 1 < len(parts):
            pos_idx = parts[i + 1]
            break
    
    if pos_idx is None:
        return None
    
    # Look for frontier file matching the pattern
    pattern = f"frontier_exploration_{base_frontier_num}_pos_{pos_idx}_experiment_*"
    matching_files = list(frontier_dir.glob(pattern))
    
    if matching_files:
        return str(matching_files[0])
    
    return None

def extract_path_from_frontier(frontier_data: Dict) -> List[Tuple[float, float]]:
    """Extract path waypoints from frontier exploration data."""
    if 'path' in frontier_data:
        return [(point['x'], point['y']) for point in frontier_data['path']]
    return []

def get_start_goal_from_frontier(frontier_data: Dict) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    """Extract start and goal positions from frontier data."""
    path = frontier_data.get('path', [])
    if len(path) >= 2:
        start = (path[0]['x'], path[0]['y'])
        goal = (path[-1]['x'], path[-1]['y'])
        return start, goal
    return (0, 0), (0, 0)

def calculate_path_length(path: List[Tuple[float, float]]) -> float:
    """Calculate total path length from waypoints."""
    if len(path) < 2:
        return 0.0
    
    total_length = 0.0
    for i in range(len(path) - 1):
        x1, y1 = path[i]
        x2, y2 = path[i + 1]
        distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        total_length += distance
    
    return total_length

def calculate_robot_path_length(experiment_data: Dict) -> float:
    """Calculate total path length from robot experiment data."""
    positions = []
    
    # Add starting position
    starting_pos = experiment_data['initialRobotPose']['position']
    positions.append((starting_pos['x'], starting_pos['y']))
    
    # Add all iteration end positions
    for iteration in experiment_data['iterations']:
        pose = iteration['endRobotStatus']['position']
        positions.append((pose['x'], pose['y']))
    
    return calculate_path_length(positions)

def generate_all_comparisons():
    """Generate comparison images for all TASK experiments."""
    base_dir = Path('/Users/kelvin/Documents/Projects/webots_robot_controllers/experiments')
    frontier_dir = base_dir / 'frontier_paths'
    output_dir = base_dir / 'comparison'
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    # Find all TASK folders
    task_folders = sorted([d for d in base_dir.iterdir() if d.is_dir() and d.name.startswith('TASK_')])
    
    print(f"Found {len(task_folders)} TASK folders")
    
    total_processed = 0
    total_matched = 0
    
    # Prepare CSV data
    csv_data = []
    
    for task_folder in task_folders:
        print(f"\nProcessing {task_folder.name}...")
        
        # Get all experiment JSON files in this task folder
        experiment_files = sorted(task_folder.glob('*.json'))
        
        for exp_file in experiment_files:
            # Find matching frontier file
            frontier_file = find_matching_frontier(exp_file.name, frontier_dir)
            
            if not frontier_file:
                print(f"  ⚠️  No matching frontier for {exp_file.name}")
                continue
            
            try:
                # Load data
                experiment_data = load_json(exp_file)
                frontier_data = load_json(frontier_file)
                
                # Extract path information
                frontier_path = extract_path_from_frontier(frontier_data)
                start, goal = get_start_goal_from_frontier(frontier_data)
                
                # Calculate path lengths
                robot_path_length = calculate_robot_path_length(experiment_data)
                frontier_path_length = calculate_path_length(frontier_path)
                
                # Add to CSV data
                csv_data.append({
                    'TASK': task_folder.name,
                    'simulation_id': exp_file.stem,
                    'robot_path_length': round(robot_path_length, 4),
                    'frontier_path_length': round(frontier_path_length, 4)
                })
                
                # Generate output filename
                output_filename = f"{task_folder.name}_{exp_file.stem}.png"
                output_path = output_dir / output_filename
                
                # Generate visualization
                title = f"{task_folder.name} - {exp_file.stem}"
                visualize_frontier_path(
                    start=start,
                    goal=goal,
                    path=frontier_path,
                    obstacles=obstacles,
                    save_path=str(output_path),
                    experiment_data=experiment_data,
                    title=title
                )
                
                print(f"  ✓ Generated: {output_filename}")
                total_matched += 1
                
            except Exception as e:
                print(f"  ✗ Error processing {exp_file.name}: {e}")
            
            total_processed += 1
    
    # Write CSV file
    csv_path = output_dir / 'path_lengths_comparison.csv'
    with open(csv_path, 'w', newline='') as csvfile:
        fieldnames = ['TASK', 'simulation_id', 'robot_path_length', 'frontier_path_length']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_data)
    
    print(f"\n{'='*60}")
    print(f"Processed: {total_processed} experiments")
    print(f"Successfully matched and generated: {total_matched} images")
    print(f"Output directory: {output_dir}")
    print(f"CSV file: {csv_path}")
    print(f"{'='*60}")

if __name__ == '__main__':
    generate_all_comparisons()
