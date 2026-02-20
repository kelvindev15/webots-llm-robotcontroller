#!/bin/bash

# Script to run frontier exploration experiments with different starting poses
# For each robot pose in the JSON file, sets the robot pose and runs frontier exploration.
# Usage: ./run_frontier_exploration.sh

set -e  # Exit on error

JSON_FILE="frontier_exploration_starting_poses.json"
CONTROLLER="/Applications/Webots.app/Contents/MacOS/webots-controller"
PYTHON_SCRIPT="g_frontier_exploration.py"

# Check if JSON file exists
if [ ! -f "$JSON_FILE" ]; then
    echo "Error: $JSON_FILE not found!"
    exit 1
fi

# Check if Webots controller exists
if [ ! -f "$CONTROLLER" ]; then
    echo "Error: Webots controller not found at $CONTROLLER"
    exit 1
fi

# Check if Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Error: $PYTHON_SCRIPT not found!"
    exit 1
fi

echo "=== Frontier Exploration - Multiple Starting Poses ==="
echo ""

# Load experiment configurations
echo "Loading experiment configurations from $JSON_FILE..."

# Get all experiment keys from JSON file
experiments=$(python3 -c "
import json
with open('$JSON_FILE', 'r') as f:
    data = json.load(f)
    for key in data.keys():
        print(key)
")

# Counter for experiments
count=0
total=$(echo "$experiments" | wc -l | xargs)

echo "Found $total experiments to run"
echo ""
echo "=================================================="

# Iterate through each experiment
for experiment_key in $experiments; do
    count=$((count + 1))
    echo ""
    echo "[$count/$total] Running experiment: $experiment_key"
    
    # Extract starting pose data using Python
    pose_data=$(python3 -c "
import json
with open('$JSON_FILE', 'r') as f:
    data = json.load(f)
    exp = data['$experiment_key']
    pose = exp['starting_pose']
    pos = pose['position']
    rot = pose['rotation']
    print(f'{pos[0]},{pos[1]},{pos[2]},{rot[0]},{rot[1]},{rot[2]},{rot[3]}')
    print(f\"Task: {exp['task']}\")
    print(f\"Prompt: {exp['prompt']}\")
")
    
    # Parse the pose data
    pose_line=$(echo "$pose_data" | head -1)
    task_line=$(echo "$pose_data" | sed -n '2p')
    prompt_line=$(echo "$pose_data" | sed -n '3p')
    
    IFS=',' read -r pos_x pos_y pos_z rot_x rot_y rot_z rot_w <<< "$pose_line"
    
    echo "  $task_line"
    echo "  $prompt_line"
    echo "  Position: [$pos_x, $pos_y, $pos_z]"
    echo "  Rotation: [$rot_x, $rot_y, $rot_z, $rot_w]"
    
    # Run the Webots controller with the Python script and experiment key as arguments
    echo "  Starting frontier exploration..."
    "$CONTROLLER" "$PYTHON_SCRIPT" "$experiment_key"
    
    echo "  ✓ Experiment $experiment_key completed!"
    echo "--------------------------------------------------"
done

echo ""
echo "=================================================="
echo "All experiments completed: $count/$total"
echo "=================================================="
echo ""
echo "Script finished."
