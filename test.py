import os
import json
import glob
import matplotlib.pyplot as plt
import matplotlib.patches as patches


def generate_path_image(experiment_path, output_path):
    """
    Generate a robot path visualization from an experiment JSON file.
    
    Args:
        experiment_path: Path to the experiment JSON file
        output_path: Path where the output image should be saved
    """
    with open(experiment_path, 'r') as f:
        experiment = json.load(f)

    xs = []
    ys = []

    starting_pos = experiment['initialRobotPose']['position']
    xs.append(starting_pos['x'])
    ys.append(starting_pos['y'])

    for iteration in experiment['iterations']:
        pose = iteration['endRobotStatus']['position']
        xs.append(pose['x'])
        ys.append(pose['y'])

    targets = [ 
        (9.157059997836008, -3.477350015014757, "FE"),
        (-4.3, 1.41119, "PC"),
        (8.4218847, 2.1373536, "OB"),
        (-3.05, -12.1, "WP"),
        (-5.2560137, -11.74814, "PS"),
        (-0.23882837, -4.8402928, "T"),
        (0.070787217, -11.12746, "WB"),
        (-0.46, 3.84, "OC"),
        (1.49, 3.84, "CC"),
        (9.201, 0.17, "S"),
    ]
            
    fig, ax = plt.subplots()

    # Path
    ax.plot(xs, ys, linewidth=3)

    # Table obstacle
    x = -2.489           # lower-left corner x
    y = -5.59           # lower-left corner y
    width = 4.5
    height = 1.5
    table = patches.Rectangle(
        (x, y),
        width,
        height,
        linewidth=2,
        fill=False,
        color="saddlebrown"
    )

    ax.add_patch(table)

    # Target labels
    for x, y, label in targets:
        ax.scatter(x, y, s=250, marker='o', color='gray')
        ax.text(
            x, y,
            label,
            fontsize=10,
            ha="center",
            va="center"
        )

    # Mark positions and number them
    min_distance = 1  # Minimum distance threshold for aggregation
    aggregated_positions = []
    i = 0

    while i < len(xs):
        x, y = xs[i], ys[i]
        positions_to_aggregate = [i + 1]  # Start with current position (1-indexed)
        
        # Check subsequent positions within threshold
        j = i + 1
        while j < len(xs):
            dist = ((xs[j] - x) ** 2 + (ys[j] - y) ** 2) ** 0.5
            if dist < min_distance:
                positions_to_aggregate.append(j + 1)  # Add 1-indexed position
                j += 1
            else:
                break
        
        # Calculate average position for aggregated points
        avg_x = sum(xs[k] for k in range(i, i + len(positions_to_aggregate))) / len(positions_to_aggregate)
        avg_y = sum(ys[k] for k in range(i, i + len(positions_to_aggregate))) / len(positions_to_aggregate)
        
        aggregated_positions.append((avg_x, avg_y, positions_to_aggregate))
        i += len(positions_to_aggregate)

    # Plot aggregated positions
    for i, (avg_x, avg_y, pos_nums) in enumerate(aggregated_positions):
        # Color: green for first, red for last, blue for others
        if 1 in pos_nums:
            color = 'green'
        elif len(xs) in pos_nums:
            color = 'red'
        else:
            color = 'lightskyblue'
        
        ax.scatter(avg_x, avg_y, s=150, marker='o', color=color)
        
        # Create label with aggregated numbers, abbreviating consecutive sequences
        label_parts = []
        if pos_nums:
            start = pos_nums[0]
            end = pos_nums[0]
            
            for num in pos_nums[1:]:
                if num == end + 1:
                    end = num
                else:
                    # Add the current range/number
                    if start == end:
                        label_parts.append(str(start))
                    elif end == start + 1:
                        label_parts.append(f"{start}, {end}")
                    else:
                        label_parts.append(f"{start}-{end}")
                    start = end = num
            
            # Add the final range/number
            if start == end:
                label_parts.append(str(start))
            elif end == start + 1:
                label_parts.append(f"{start}, {end}")
            else:
                label_parts.append(f"{start}-{end}")
        
        label = ', '.join(label_parts)
        ax.text(
            avg_x, avg_y,
            label,
            fontsize=8,
            ha="center",
            va="center",
        )

    # Collect all x and y coordinates
    all_xs = xs + [t[0] for t in targets]
    all_ys = ys + [t[1] for t in targets]

    # Set limits to show everything with some margin
    margin = 1.0
    ax.set_xlim(min(all_xs) - margin, max(all_xs) + margin)
    ax.set_ylim(min(all_ys) - margin, max(all_ys) + margin)

    # Remove axes and padding
    ax.set_axis_off()
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

    # Save without margins
    fig.savefig(output_path,
                dpi=300,
                transparent=False,
                bbox_inches='tight',
                pad_inches=0)

    plt.close(fig)


def process_all_experiments():
    """Process all experiment JSON files and generate path images."""
    experiments_dir = 'experiments'
    output_dir = 'experiments/paths'
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all JSON files in experiments directory and subdirectories
    experiment_files = []
    for root, dirs, files in os.walk(experiments_dir):
        # Skip the paths directory itself
        if 'paths' in root:
            continue
        for file in files:
            if file.endswith('.json'):
                experiment_files.append(os.path.join(root, file))
    
    print(f"Found {len(experiment_files)} experiment files")
    
    # Process each experiment file
    for i, exp_file in enumerate(experiment_files, 1):
        try:
            # Get the experiment filename without extension
            filename = os.path.basename(exp_file)
            output_filename = filename.replace('.json', '.png')
            output_path = os.path.join(output_dir, output_filename)
            
            print(f"[{i}/{len(experiment_files)}] Processing {filename}...")
            generate_path_image(exp_file, output_path)
            print(f"  ✓ Saved to {output_path}")
            
        except Exception as e:
            print(f"  ✗ Error processing {exp_file}: {e}")
    
    print(f"\nDone! Generated {len(experiment_files)} path images in {output_dir}")


if __name__ == "__main__":
    process_all_experiments()
