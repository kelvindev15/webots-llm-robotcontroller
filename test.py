import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

experiment = {}

with open('experiments/Lidar3Section/272_pos_3_experiment_gemini-2_0-flash_20251116-113645.json', 'r') as f:
    import json
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

# Start / end
ax.scatter(xs[0], ys[0], s=120, marker='o')
ax.scatter(xs[-1], ys[-1], s=120, marker='x')

x = -2.489           # lower-left corner x
y = -5.59           # lower-left corner y
width = 4.5
height = 1.5
rect = patches.Rectangle(
    (x, y),
    width,
    height,
    linewidth=2,
    fill=False,
    color="saddlebrown"   # keep transparent
)

ax.add_patch(rect)

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
fig.savefig("robot_path.png",
            dpi=300,
            transparent=False,
            bbox_inches='tight',
            pad_inches=0)

plt.close(fig)
