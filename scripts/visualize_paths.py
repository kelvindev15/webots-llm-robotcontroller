#!/usr/bin/env python3
"""
Path visualization tools for experiment and frontier exploration data.

Subcommands
-----------
experiment   Render the robot's trajectory from experiment JSON file(s).
frontier     Render frontier exploration path(s) from JSON file(s).

Both subcommands accept a single file or ``--batch`` to process all files.
The ``visualize_frontier_path`` and ``obstacles`` names are preserved as
module-level exports so that other scripts (e.g. generate_comparison_images.py)
can continue to import them unchanged.

Replaces: test.py, visualize_frontier_paths.py
"""

import os
import json
import glob
import argparse
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import matplotlib.patches as patches


# ---------------------------------------------------------------------------
# Shared environment data
# ---------------------------------------------------------------------------

class Rectangle:
    """Represents a rectangular obstacle."""

    def __init__(self, x: float, y: float, width: float, height: float):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def get_corners(self) -> List[Tuple[float, float]]:
        return [
            (self.x, self.y),
            (self.x + self.width, self.y),
            (self.x + self.width, self.y + self.height),
            (self.x, self.y + self.height),
        ]

    def get_center(self) -> Tuple[float, float]:
        return (self.x + self.width / 2, self.y + self.height / 2)

    def contains_point(self, point: Tuple[float, float], margin: float = 0) -> bool:
        px, py = point
        return (self.x - margin <= px <= self.x + self.width + margin and
                self.y - margin <= py <= self.y + self.height + margin)


# Known target locations in the environment
TARGETS: List[Tuple[float, float, str]] = [
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

TABLE_OBSTACLE = Rectangle(x=-2.489, y=-5.59, width=4.5, height=1.5)
obstacles: List[Rectangle] = [TABLE_OBSTACLE]   # exported for external importers

TARGET_MAP: Dict[str, str] = {
    'pile of pallets': 'PALLET_STACK',
    'carry some beers': 'PLASTIC_CRATE',
    'red box': 'PLASTIC_CRATE',
    'oil barrels': 'OIL_BARREL',
    'some stairs': 'STAIRS',
    'dark brown boxes': 'WOODEN_BOX',
    'fire extinguisher': 'FIRE_EXTINGUISHER',
    'fire': 'FIRE_EXTINGUISHER',
}


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def extract_target_from_prompt(prompt: str) -> Optional[str]:
    """Return target name matching prompt keywords, or None."""
    prompt_lower = prompt.lower()
    for keyword, target_name in TARGET_MAP.items():
        if keyword in prompt_lower:
            return target_name
    return None


def _draw_obstacles_and_targets(ax) -> None:
    """Draw obstacle rectangles and target scatter markers on ax."""
    for i, obstacle in enumerate(obstacles):
        ax.add_patch(patches.Rectangle(
            (obstacle.x, obstacle.y), obstacle.width, obstacle.height,
            linewidth=2, fill=True, facecolor='lightgray', edgecolor='saddlebrown',
            label='Table Obstacle' if i == 0 else None,
        ))
    for x, y, label in TARGETS:
        ax.scatter(x, y, s=250, marker='o', color='gray')
        ax.text(x, y, label, fontsize=10, ha='center', va='center')


def _draw_aggregated_positions(ax, xs: List[float], ys: List[float],
                                min_distance: float = 1.0) -> None:
    """
    Aggregate nearby iteration positions and draw markers with compact range labels.
    Green = first, Red = last, LightSkyBlue = intermediate.
    """
    aggregated: List[Tuple[float, float, List[int]]] = []
    i = 0
    while i < len(xs):
        x, y = xs[i], ys[i]
        group = [i + 1]
        j = i + 1
        while j < len(xs):
            if ((xs[j] - x) ** 2 + (ys[j] - y) ** 2) ** 0.5 < min_distance:
                group.append(j + 1)
                j += 1
            else:
                break
        avg_x = sum(xs[k] for k in range(i, i + len(group))) / len(group)
        avg_y = sum(ys[k] for k in range(i, i + len(group))) / len(group)
        aggregated.append((avg_x, avg_y, group))
        i += len(group)

    for avg_x, avg_y, pos_nums in aggregated:
        color = ('green' if 1 in pos_nums
                 else 'red' if len(xs) in pos_nums
                 else 'lightskyblue')
        ax.scatter(avg_x, avg_y, s=150, marker='o', color=color)

        label_parts: List[str] = []
        seg_start = pos_nums[0]
        seg_end = pos_nums[0]
        for num in pos_nums[1:]:
            if num == seg_end + 1:
                seg_end = num
            else:
                label_parts.append(
                    str(seg_start) if seg_start == seg_end
                    else f"{seg_start}, {seg_end}" if seg_end == seg_start + 1
                    else f"{seg_start}-{seg_end}"
                )
                seg_start = seg_end = num
        label_parts.append(
            str(seg_start) if seg_start == seg_end
            else f"{seg_start}, {seg_end}" if seg_end == seg_start + 1
            else f"{seg_start}-{seg_end}"
        )
        ax.text(avg_x, avg_y, ', '.join(label_parts), fontsize=8, ha='center', va='center')


# ---------------------------------------------------------------------------
# Experiment path visualization  –  originally test.py
# ---------------------------------------------------------------------------

def visualize_experiment_path(experiment_path: str, output_path: str) -> None:
    """
    Generate a robot path visualization from an experiment JSON file.

    Args:
        experiment_path: Path to the experiment JSON file.
        output_path:     Where to save the output image.
    """
    with open(experiment_path, 'r') as f:
        experiment = json.load(f)

    xs: List[float] = []
    ys: List[float] = []

    starting_pos = experiment['initialRobotPose']['position']
    xs.append(starting_pos['x'])
    ys.append(starting_pos['y'])

    for iteration in experiment['iterations']:
        pose = iteration['endRobotStatus']['position']
        xs.append(pose['x'])
        ys.append(pose['y'])

    fig, ax = plt.subplots()

    # Robot path
    ax.plot(xs, ys, linewidth=3)

    # Obstacles and target labels
    ax.add_patch(patches.Rectangle(
        (TABLE_OBSTACLE.x, TABLE_OBSTACLE.y),
        TABLE_OBSTACLE.width, TABLE_OBSTACLE.height,
        linewidth=2, fill=False, color='saddlebrown',
    ))
    for x, y, label in TARGETS:
        ax.scatter(x, y, s=250, marker='o', color='gray')
        ax.text(x, y, label, fontsize=10, ha='center', va='center')

    # Aggregated iteration position markers
    _draw_aggregated_positions(ax, xs, ys)

    # Axis limits encompassing all points
    all_xs = xs + [t[0] for t in TARGETS]
    all_ys = ys + [t[1] for t in TARGETS]
    margin = 1.0
    ax.set_xlim(min(all_xs) - margin, max(all_xs) + margin)
    ax.set_ylim(min(all_ys) - margin, max(all_ys) + margin)

    ax.set_axis_off()
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.savefig(output_path, dpi=300, transparent=False,
                bbox_inches='tight', pad_inches=0)
    plt.close(fig)


def process_all_experiment_paths(
        experiments_dir: str = 'experiments',
        output_dir: str = 'experiments/paths') -> None:
    """Batch: generate path images for every experiment JSON file."""
    os.makedirs(output_dir, exist_ok=True)

    experiment_files: List[str] = []
    for root, dirs, files in os.walk(experiments_dir):
        if 'paths' in root:
            continue
        for file in files:
            if file.endswith('.json'):
                experiment_files.append(os.path.join(root, file))

    print(f"Found {len(experiment_files)} experiment files")
    for i, exp_file in enumerate(experiment_files, 1):
        filename = os.path.basename(exp_file)
        output_path = os.path.join(output_dir, filename.replace('.json', '.png'))
        print(f"[{i}/{len(experiment_files)}] {filename}…")
        try:
            visualize_experiment_path(exp_file, output_path)
            print(f"  ✓ {output_path}")
        except Exception as e:
            print(f"  ✗ {e}")
    print(f"\nDone! Images saved to {output_dir}")


# ---------------------------------------------------------------------------
# Frontier path visualization  –  originally visualize_frontier_paths.py
# ---------------------------------------------------------------------------

def visualize_frontier_path_from_file(path_file: str,
                                       output_file: Optional[str] = None) -> None:
    """
    Render a single recorded frontier exploration path from a JSON file.

    Args:
        path_file:   Path to the frontier exploration JSON file.
        output_file: Where to save the image. If None, shows the plot interactively.
    """
    with open(path_file, 'r') as f:
        data = json.load(f)

    xs = [point['x'] for point in data['path']]
    ys = [point['y'] for point in data['path']]
    if not xs or not ys:
        print(f"Warning: No path data in {path_file}")
        return

    fig, ax = plt.subplots(figsize=(12, 10))
    ax.plot(xs, ys, linewidth=2, color='blue', alpha=0.7, label='Robot Path')
    ax.scatter(xs[0], ys[0], s=200, marker='o', color='green', label='Start',
               zorder=10, edgecolors='black', linewidths=2)
    ax.scatter(xs[-1], ys[-1], s=200, marker='s', color='red', label='End',
               zorder=10, edgecolors='black', linewidths=2)

    _draw_obstacles_and_targets(ax)

    for x, y, label in TARGETS:
        ax.text(x, y + 0.5, label, fontsize=9, ha='center', va='bottom', fontweight='bold')

    all_xs = xs + [t[0] for t in TARGETS]
    all_ys = ys + [t[1] for t in TARGETS]
    pad = 2.0
    ax.set_xlim(min(all_xs) - pad, max(all_xs) + pad)
    ax.set_ylim(min(all_ys) - pad, max(all_ys) + pad)

    ax.set_xlabel('X Position (m)', fontsize=12)
    ax.set_ylabel('Y Position (m)', fontsize=12)
    sim_id = data.get('simulation_id', 'Unknown')
    total_waypoints = data.get('total_waypoints', len(xs))
    ax.set_title(
        f'Frontier Exploration Path\nSimulation ID: {sim_id} | Waypoints: {total_waypoints}',
        fontsize=14, fontweight='bold',
    )
    ax.grid(True, alpha=0.3)
    ax.legend(loc='best', fontsize=10)
    ax.set_aspect('equal', adjustable='box')

    if output_file:
        fig.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Saved to {output_file}")
    else:
        plt.show()
    plt.close(fig)


def visualize_frontier_path(start: Tuple[float, float], goal: Tuple[float, float],
                             path: List[Tuple[float, float]],
                             obstacle_list: List[Rectangle],
                             save_path: str,
                             experiment_data: Dict = None,
                             title: str = "Frontier Path") -> None:
    """
    Visualize an oracle/planned frontier path with optional actual robot path overlay.

    This function is exported for use by external scripts (e.g. generate_comparison_images.py).

    Args:
        start:           Starting position (x, y).
        goal:            Goal position (x, y).
        path:            Oracle/planned frontier waypoints.
        obstacle_list:   Rectangle obstacles to draw.
        save_path:       Output image path.
        experiment_data: If provided, overlays the actual robot path in blue.
        title:           Plot title.
    """
    fig, ax = plt.subplots()

    # -- Actual robot path --------------------------------------------------
    if experiment_data:
        xs: List[float] = []
        ys: List[float] = []
        starting_pos = experiment_data['initialRobotPose']['position']
        xs.append(starting_pos['x'])
        ys.append(starting_pos['y'])
        for iteration in experiment_data['iterations']:
            pose = iteration['endRobotStatus']['position']
            xs.append(pose['x'])
            ys.append(pose['y'])
        ax.plot(xs, ys, linewidth=3, color='blue', alpha=0.5, label='Actual Path')
        _draw_aggregated_positions(ax, xs, ys)

    # -- Planned frontier path ----------------------------------------------
    if len(path) > 1:
        ax.plot([p[0] for p in path], [p[1] for p in path],
                linewidth=3, color='red', linestyle='--', alpha=0.8,
                label='Frontier Path', zorder=5)

    # -- Obstacles / targets ------------------------------------------------
    for obstacle in obstacle_list:
        ax.add_patch(patches.Rectangle(
            (obstacle.x, obstacle.y), obstacle.width, obstacle.height,
            linewidth=2, fill=False, color='saddlebrown',
        ))
    for x, y, label in TARGETS:
        ax.scatter(x, y, s=250, marker='o', color='gray')
        ax.text(x, y, label, fontsize=10, ha='center', va='center')

    # -- Axis limits --------------------------------------------------------
    all_xs = [p[0] for p in path] + [t[0] for t in TARGETS]
    all_ys = [p[1] for p in path] + [t[1] for t in TARGETS]
    if experiment_data:
        all_xs.extend(xs)
        all_ys.extend(ys)
    margin = 1.0
    ax.set_xlim(min(all_xs) - margin, max(all_xs) + margin)
    ax.set_ylim(min(all_ys) - margin, max(all_ys) + margin)

    ax.legend(loc='best', fontsize=10)
    ax.set_axis_off()
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.savefig(save_path, dpi=300, transparent=False, bbox_inches='tight', pad_inches=0)
    plt.close(fig)


def process_all_frontier_paths(
        input_dir: str = 'experiments/frontier_paths',
        output_dir: str = 'experiments/frontier_paths/visualizations') -> None:
    """Batch: generate visualization images for all frontier exploration JSON files."""
    os.makedirs(output_dir, exist_ok=True)
    path_files = glob.glob(os.path.join(input_dir, 'frontier_exploration_*.json'))
    if not path_files:
        print(f"No frontier exploration files found in {input_dir}")
        return
    print(f"Found {len(path_files)} frontier files")
    for i, path_file in enumerate(path_files, 1):
        basename = os.path.basename(path_file)
        output_path = os.path.join(output_dir, basename.replace('.json', '.png'))
        print(f"[{i}/{len(path_files)}] {basename}…")
        try:
            visualize_frontier_path_from_file(path_file, output_path)
        except Exception as e:
            print(f"  Error: {e}")
    print(f"\nDone! Visualizations saved to {output_dir}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description='Visualize robot experiment paths or frontier exploration paths.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single experiment file
  python visualize_paths.py experiment path/to/experiment.json

  # Batch – all experiment files
  python visualize_paths.py experiment --batch

  # Single frontier file
  python visualize_paths.py frontier experiments/frontier_paths/frontier_exploration_1_pos_1_experiment_....json

  # Batch – all frontier files
  python visualize_paths.py frontier --batch
""",
    )
    sub = parser.add_subparsers(dest='command')

    # ---- experiment ----
    exp_p = sub.add_parser('experiment', help='Render robot trajectory from experiment JSON(s).')
    exp_p.add_argument('path_file', nargs='?',
                       help='Path to a specific experiment JSON file.')
    exp_p.add_argument('-o', '--output',
                       help='Output image file path (single-file mode).')
    exp_p.add_argument('--batch', action='store_true',
                       help='Process all experiment JSON files.')
    exp_p.add_argument('--experiments-dir', default='experiments',
                       help='Experiments directory for batch mode.')
    exp_p.add_argument('--output-dir', default='experiments/paths',
                       help='Output directory for batch mode.')

    # ---- frontier ----
    fr_p = sub.add_parser('frontier', help='Render frontier exploration path(s).')
    fr_p.add_argument('path_file', nargs='?',
                      help='Path to a specific frontier exploration JSON file.')
    fr_p.add_argument('-o', '--output',
                      help='Output image file path (single-file mode).')
    fr_p.add_argument('--batch', action='store_true',
                      help='Process all frontier exploration JSON files.')
    fr_p.add_argument('--input-dir', default='experiments/frontier_paths',
                      help='Input directory for batch mode.')
    fr_p.add_argument('--output-dir', default='experiments/frontier_paths/visualizations',
                      help='Output directory for batch mode.')

    args = parser.parse_args()

    if args.command == 'experiment':
        if args.batch:
            process_all_experiment_paths(args.experiments_dir, args.output_dir)
        elif args.path_file:
            output = args.output or args.path_file.replace('.json', '.png')
            visualize_experiment_path(args.path_file, output)
        else:
            exp_p.print_help()

    elif args.command == 'frontier':
        if args.batch:
            process_all_frontier_paths(args.input_dir, args.output_dir)
        elif args.path_file:
            visualize_frontier_path_from_file(args.path_file, args.output)
        else:
            fr_p.print_help()

    else:
        parser.print_help()
        print("\nExamples:")
        print("  python visualize_paths.py experiment --batch")
        print("  python visualize_paths.py frontier --batch")


if __name__ == '__main__':
    main()
