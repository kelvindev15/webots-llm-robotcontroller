#!/usr/bin/env python3
"""
Path generation utilities: single paths, oracle paths, and frontier-oracle combined paths.

Subcommands
-----------
path              Plan a single obstacle-avoiding path between two coordinates.
oracle            Generate oracle (optimal) paths for all experiment JSON files.
frontier-oracle   Extend frontier exploration paths with oracle paths to targets.

Replaces: generate_path.py, generate_oracle_paths.py, generate_frontier_oracle_paths.py
"""

import os
import json
import csv
import glob
import argparse
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Environment constants (shared by all sub-tools)
# ---------------------------------------------------------------------------

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

# Named target positions used for prompt matching
NAMED_TARGETS: List[Tuple[float, float, str]] = [
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

TABLE_OBSTACLE = None  # built below after Rectangle is defined


# ---------------------------------------------------------------------------
# Geometry primitives (shared)
# ---------------------------------------------------------------------------

class Rectangle:
    """Represents a rectangular obstacle."""

    def __init__(self, x: float, y: float, width: float, height: float):
        self.x = x          # Lower-left corner x
        self.y = y          # Lower-left corner y
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


TABLE_OBSTACLE = Rectangle(x=-2.489, y=-5.59, width=4.5, height=1.5)
obstacles: List[Rectangle] = [TABLE_OBSTACLE]


def segments_intersect(p1: Tuple[float, float], p2: Tuple[float, float],
                       p3: Tuple[float, float], p4: Tuple[float, float]) -> bool:
    """Check if line segment p1-p2 intersects with segment p3-p4 (cross-product method)."""
    def ccw(A, B, C):
        return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])
    return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)


def line_intersects_rectangle(p1: Tuple[float, float], p2: Tuple[float, float],
                               rect: Rectangle, margin: float = 0.3) -> bool:
    """Return True if segment p1-p2 intersects rect (expanded by margin)."""
    x1, y1 = p1
    x2, y2 = p2
    rx_min = rect.x - margin
    rx_max = rect.x + rect.width + margin
    ry_min = rect.y - margin
    ry_max = rect.y + rect.height + margin

    if (rx_min <= x1 <= rx_max and ry_min <= y1 <= ry_max) or \
       (rx_min <= x2 <= rx_max and ry_min <= y2 <= ry_max):
        return True

    edges = [
        ((rx_min, ry_min), (rx_max, ry_min)),
        ((rx_max, ry_min), (rx_max, ry_max)),
        ((rx_max, ry_max), (rx_min, ry_max)),
        ((rx_min, ry_max), (rx_min, ry_min)),
    ]
    return any(segments_intersect(p1, p2, e1, e2) for e1, e2 in edges)


def get_waypoints_around_obstacle(start: Tuple[float, float], goal: Tuple[float, float],
                                  rect: Rectangle, margin: float = 0.3) -> List[Tuple[float, float]]:
    """Generate minimal-length waypoints to navigate around a rectangular obstacle."""
    mid_x = (start[0] + goal[0]) / 2
    mid_y = (start[1] + goal[1]) / 2
    step_size = 0.5
    max_iter = 100
    valid_paths = []

    for direction in ['horizontal', 'vertical']:
        for sign in [1, -1]:
            for i in range(1, max_iter):
                intermediate = (
                    (mid_x + sign * i * step_size, mid_y) if direction == 'horizontal'
                    else (mid_x, mid_y + sign * i * step_size)
                )
                if (not line_intersects_rectangle(start, intermediate, rect, margin) and
                        not line_intersects_rectangle(intermediate, goal, rect, margin)):
                    length = (np.linalg.norm(np.array(intermediate) - np.array(start)) +
                              np.linalg.norm(np.array(goal) - np.array(intermediate)))
                    valid_paths.append((length, intermediate))
                    break

    if valid_paths:
        return [start, min(valid_paths, key=lambda x: x[0])[1], goal]

    # Fallback: route via nearest clear corner
    corners = [
        (rect.x - margin, rect.y - margin),
        (rect.x + rect.width + margin, rect.y - margin),
        (rect.x + rect.width + margin, rect.y + rect.height + margin),
        (rect.x - margin, rect.y + rect.height + margin),
    ]
    best_path = None
    best_dist = float('inf')
    for corner in corners:
        if (not line_intersects_rectangle(start, corner, rect, margin) and
                not line_intersects_rectangle(corner, goal, rect, margin)):
            dist = (np.linalg.norm(np.array(start) - np.array(corner)) +
                    np.linalg.norm(np.array(corner) - np.array(goal)))
            if dist < best_dist:
                best_dist = dist
                best_path = [start, corner, goal]
    return best_path if best_path else [start, goal]


def generate_path(start: Tuple[float, float], goal: Tuple[float, float],
                  obstacle_list: List[Rectangle], margin: float = 0.3) -> List[Tuple[float, float]]:
    """
    Generate an efficient obstacle-avoiding path from start to goal.

    Returns a list of (x, y) waypoints.
    """
    for obstacle in obstacle_list:
        if line_intersects_rectangle(start, goal, obstacle, margin):
            return get_waypoints_around_obstacle(start, goal, obstacle, margin)
    return [start, goal]


def calculate_path_length_tuples(path: List[Tuple[float, float]]) -> float:
    """Total path length from a list of (x, y) tuples."""
    if len(path) < 2:
        return 0.0
    return sum(
        ((path[i + 1][0] - path[i][0]) ** 2 + (path[i + 1][1] - path[i][1]) ** 2) ** 0.5
        for i in range(len(path) - 1)
    )


# ---------------------------------------------------------------------------
# Shared prompt / target helpers
# ---------------------------------------------------------------------------

def extract_target_from_prompt(prompt: str) -> Optional[str]:
    """Return the target name matching the prompt, or None."""
    prompt_lower = prompt.lower()
    for keyword, target_name in TARGET_MAP.items():
        if keyword in prompt_lower:
            return target_name
    return None


def find_target_position(experiment_data: Dict,
                         target_name: Optional[str]) -> Optional[Tuple[float, float]]:
    """
    Look up the target's (x, y) position from the experiment JSON data.

    Falls back to searching NAMED_TARGETS for known positions.
    """
    if target_name is None:
        return None
    for x, y, name in NAMED_TARGETS:
        if name == target_name:
            return (x, y)
    targets = experiment_data.get('targets', [])
    for target in targets:
        if target.get('name') == target_name:
            return (target['x'], target['y'])
    return None


# ---------------------------------------------------------------------------
# sub-tool: path  –  originally generate_path.py
# ---------------------------------------------------------------------------

def visualize_single_path(start: Tuple[float, float], goal: Tuple[float, float],
                          path: List[Tuple[float, float]],
                          obstacle_list: List[Rectangle],
                          save_path: Optional[str] = None) -> None:
    """Visualize a single planned path with obstacles."""
    fig, ax = plt.subplots(figsize=(12, 10))

    for obstacle in obstacle_list:
        ax.add_patch(patches.Rectangle(
            (obstacle.x, obstacle.y), obstacle.width, obstacle.height,
            linewidth=2, fill=True, facecolor='saddlebrown', edgecolor='black',
            alpha=0.6, label='Table (Obstacle)',
        ))

    if len(path) > 1:
        path_x = [p[0] for p in path]
        path_y = [p[1] for p in path]
        ax.plot(path_x, path_y, 'b-', linewidth=2, marker='o', markersize=8, label='Path', zorder=5)
        for i, (x, y) in enumerate(path):
            if i == 0:
                ax.scatter(x, y, s=200, marker='o', color='green', edgecolors='black',
                           linewidths=2, label='Start', zorder=10)
            elif i == len(path) - 1:
                ax.scatter(x, y, s=200, marker='*', color='red', edgecolors='black',
                           linewidths=2, label='Goal', zorder=10)
            else:
                ax.scatter(x, y, s=150, marker='s', color='yellow', edgecolors='black',
                           linewidths=2, zorder=10)
                ax.text(x + 0.2, y + 0.2, f'W{i}', fontsize=10, fontweight='bold')

    ax.plot([start[0], goal[0]], [start[1], goal[1]], 'r--', linewidth=1, alpha=0.5,
            label='Direct path')

    path_length = calculate_path_length_tuples(path)
    direct_length = float(np.linalg.norm(np.array(goal) - np.array(start)))
    ax.set_title(
        f'Path Planning with Obstacle Avoidance\n'
        f'Path length: {path_length:.2f}m | Direct: {direct_length:.2f}m | '
        f'Efficiency: {(direct_length / path_length) * 100:.1f}%',
        fontsize=14, fontweight='bold',
    )
    ax.set_xlabel('X (meters)', fontsize=12)
    ax.set_ylabel('Y (meters)', fontsize=12)
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')
    ax.set_xlim(-9, 10)
    ax.set_ylim(-13, 4)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Visualization saved to: {save_path}")
    else:
        plt.show()
    plt.close()


# ---------------------------------------------------------------------------
# sub-tool: oracle  –  originally generate_oracle_paths.py
# ---------------------------------------------------------------------------

def visualize_oracle_path(start: Tuple[float, float], goal: Tuple[float, float],
                          path: List[Tuple[float, float]],
                          obstacle_list: List[Rectangle],
                          save_path: str,
                          experiment_data: Dict = None,
                          title: str = "Oracle Path") -> None:
    """Visualize an oracle path, optionally with the actual robot path overlaid."""
    fig, ax = plt.subplots()

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

    if len(path) > 1:
        ax.plot([p[0] for p in path], [p[1] for p in path],
                linewidth=3, color='red', linestyle='--', alpha=0.8, label='Oracle Path', zorder=5)

    _draw_environment(ax, obstacle_list)

    _set_axis_limits(ax,
                     [p[0] for p in path] + ([e for e in xs] if experiment_data else []),
                     [p[1] for p in path] + ([e for e in ys] if experiment_data else []))

    ax.legend(loc='best', fontsize=10)
    ax.set_axis_off()
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.savefig(save_path, dpi=300, transparent=False, bbox_inches='tight', pad_inches=0)
    plt.close(fig)


def generate_oracle_path_for_experiment(experiment_path: str, output_dir: str,
                                        margin: float = 0.3,
                                        visualize: bool = True) -> Dict:
    """Generate and save the oracle path for a single experiment file."""
    with open(experiment_path, 'r') as f:
        experiment = json.load(f)

    start_pos = experiment['initialRobotPose']['position']
    start = (start_pos['x'], start_pos['y'])

    prompt = experiment.get('prompt', '')
    target_name = extract_target_from_prompt(prompt)
    target_pos = find_target_position(experiment, target_name)

    if target_pos is None:
        if experiment.get('iterations'):
            final_pos = experiment['iterations'][-1]['endRobotStatus']['position']
            target_pos = (final_pos['x'], final_pos['y'])
        else:
            raise ValueError(f"Could not determine target position for {experiment_path}")

    goal = target_pos
    path = generate_path(start, goal, obstacles, margin=margin)
    path_length = calculate_path_length_tuples(path)
    direct_length = float(np.linalg.norm(np.array(goal) - np.array(start)))

    oracle_data = {
        "experiment_id": experiment.get('id'),
        "experiment_file": os.path.basename(experiment_path),
        "prompt": prompt,
        "target": target_name,
        "start": {"x": start[0], "y": start[1]},
        "goal": {"x": goal[0], "y": goal[1]},
        "waypoints": [{"x": p[0], "y": p[1]} for p in path],
        "metrics": {
            "path_length": path_length,
            "direct_distance": direct_length,
            "efficiency_percent": (direct_length / path_length * 100) if path_length > 0 else 100,
            "num_waypoints": len(path),
        },
    }

    filename = os.path.basename(experiment_path).replace('.json', '_oracle.json')
    output_path = os.path.join(output_dir, filename)
    with open(output_path, 'w') as f:
        json.dump(oracle_data, f, indent=2)

    if visualize:
        viz_path = output_path.replace('.json', '.png')
        visualize_oracle_path(start, goal, path, obstacles, viz_path,
                              experiment_data=experiment,
                              title=f"Oracle Path: {prompt.strip()}")
    return oracle_data


def generate_all_oracle_paths(experiments_dir: str = 'experiments',
                              output_dir: str = 'experiments/oracles',
                              margin: float = 0.3,
                              visualize: bool = True) -> None:
    """Generate oracle paths for every experiment JSON in experiments_dir."""
    os.makedirs(output_dir, exist_ok=True)

    experiment_files = []
    for root, dirs, files in os.walk(experiments_dir):
        if 'oracles' in root or 'paths' in root:
            continue
        for file in files:
            if file.endswith('.json') and not file.endswith('_oracle.json'):
                experiment_files.append(os.path.join(root, file))

    print(f"Found {len(experiment_files)} experiment files")
    print(f"Output: {output_dir} | Margin: {margin}m | Visualize: {visualize}")
    print("-" * 80)

    success = 0
    errors = 0
    for i, exp_file in enumerate(experiment_files, 1):
        filename = os.path.basename(exp_file)
        print(f"[{i}/{len(experiment_files)}] {filename}…")
        try:
            oracle_data = generate_oracle_path_for_experiment(
                exp_file, output_dir, margin=margin, visualize=visualize)
            print(f"  ✓ {oracle_data['metrics']['num_waypoints']} waypoints, "
                  f"{oracle_data['metrics']['path_length']:.2f}m")
            success += 1
        except Exception as e:
            print(f"  ✗ {e}")
            errors += 1

    print("-" * 80)
    print(f"Done! {success} succeeded, {errors} errors")


# ---------------------------------------------------------------------------
# sub-tool: frontier-oracle  –  originally generate_frontier_oracle_paths.py
# ---------------------------------------------------------------------------

def find_matching_frontier(task_filename: str, frontier_dir: Path) -> Optional[str]:
    """
    Find the matching frontier exploration JSON for a task experiment file.

    Mapping: experiments [1-4]_pos_1 → frontier_exploration_1_pos_1, etc.
    """
    exp_num_str = task_filename.split('_')[0]
    try:
        exp_num = int(exp_num_str)
    except ValueError:
        return None

    base_frontier_num = ((exp_num - 1) // 4) * 4 + 1

    parts = task_filename.split('_')
    pos_idx = None
    for i, part in enumerate(parts):
        if part == 'pos' and i + 1 < len(parts):
            pos_idx = parts[i + 1]
            break
    if pos_idx is None:
        return None

    pattern = f"frontier_exploration_{base_frontier_num}_pos_{pos_idx}_experiment_*"
    matching = list(frontier_dir.glob(pattern))
    return str(matching[0]) if matching else None


def visualize_combined_path(start: Tuple[float, float],
                            frontier_path: List[Tuple[float, float]],
                            oracle_extension: List[Tuple[float, float]],
                            goal: Tuple[float, float],
                            obstacle_list: List[Rectangle],
                            save_path: str,
                            experiment_data: Dict = None,
                            title: str = "Frontier + Oracle Path") -> None:
    """Visualize the combined frontier and oracle paths (+ optional actual robot path)."""
    fig, ax = plt.subplots()

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

    if len(frontier_path) > 1:
        ax.plot([p[0] for p in frontier_path], [p[1] for p in frontier_path],
                linewidth=3, color='red', linestyle='--', alpha=0.8,
                label='Frontier Path', zorder=5)

    if len(oracle_extension) > 1:
        ax.plot([p[0] for p in oracle_extension], [p[1] for p in oracle_extension],
                linewidth=3, color='green', linestyle='--', alpha=0.8,
                label='Shortest Path', zorder=5)

    _draw_environment(ax, obstacle_list)

    all_xs = [p[0] for p in frontier_path] + [p[0] for p in oracle_extension]
    all_ys = [p[1] for p in frontier_path] + [p[1] for p in oracle_extension]
    if experiment_data:
        all_xs.extend(xs)
        all_ys.extend(ys)
    _set_axis_limits(ax, all_xs, all_ys)

    ax.legend(loc='best', fontsize=10)
    ax.set_axis_off()
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.savefig(save_path, dpi=300, transparent=False, bbox_inches='tight', pad_inches=0)
    plt.close(fig)


def generate_all_frontier_oracle_paths(
        base_dir: str = 'experiments',
        frontier_subdir: str = 'frontier_paths',
        output_subdir: str = 'frontier_oracle',
        margin: float = 0.3) -> None:
    """
    Process all TASK experiment folders, match them with frontier paths, and
    generate combined frontier+oracle paths saved to experiments/frontier_oracle/.
    """
    base_path = Path(base_dir)
    frontier_dir = base_path / frontier_subdir
    output_dir = base_path / output_subdir
    output_dir.mkdir(exist_ok=True)

    task_folders = sorted(d for d in base_path.iterdir()
                           if d.is_dir() and d.name.startswith('TASK_'))

    print(f"Found {len(task_folders)} TASK folders")
    print(f"Output: {output_dir}")
    print("-" * 80)

    total_processed = 0
    total_matched = 0
    csv_data = []

    for task_folder in task_folders:
        print(f"\nProcessing {task_folder.name}…")
        for exp_file in sorted(task_folder.glob('*.json')):
            frontier_file = find_matching_frontier(exp_file.name, frontier_dir)
            if not frontier_file:
                print(f"  ⚠  No matching frontier for {exp_file.name}")
                continue

            try:
                with open(exp_file, 'r') as f:
                    experiment_data = json.load(f)
                with open(frontier_file, 'r') as f:
                    frontier_data = json.load(f)

                frontier_path = [(pt['x'], pt['y']) for pt in frontier_data['path']]
                if not frontier_path:
                    print(f"  ⚠  Empty frontier path for {exp_file.name}")
                    continue

                prompt = experiment_data.get('prompt', '')
                target_name = extract_target_from_prompt(prompt)
                target_pos = find_target_position(experiment_data, target_name)
                if target_pos is None:
                    print(f"  ⚠  No target found for {exp_file.name}")
                    continue

                oracle_extension = generate_path(frontier_path[-1], target_pos, obstacles, margin)

                frontier_len = calculate_path_length_tuples(frontier_path)
                oracle_len = calculate_path_length_tuples(oracle_extension)
                total_len = frontier_len + oracle_len

                csv_data.append({
                    'TASK': task_folder.name,
                    'simulation_id': exp_file.stem,
                    'frontier_path_length': round(frontier_len, 4),
                    'oracle_extension_length': round(oracle_len, 4),
                    'total_path_length': round(total_len, 4),
                    'num_frontier_waypoints': len(frontier_path),
                    'num_oracle_waypoints': len(oracle_extension),
                })

                output_stem = f"{task_folder.name}_{exp_file.stem}"
                viz_path = str(output_dir / f"{output_stem}.png")
                json_path = output_dir / f"{output_stem}.json"

                visualize_combined_path(
                    start=frontier_path[0],
                    frontier_path=frontier_path,
                    oracle_extension=oracle_extension,
                    goal=target_pos,
                    obstacle_list=obstacles,
                    save_path=viz_path,
                    experiment_data=experiment_data,
                    title=output_stem,
                )

                combined_data = {
                    "simulation_id": exp_file.stem,
                    "task": task_folder.name,
                    "prompt": prompt,
                    "target": target_name,
                    "frontier_path": [{"x": p[0], "y": p[1]} for p in frontier_path],
                    "oracle_extension": [{"x": p[0], "y": p[1]} for p in oracle_extension],
                    "metrics": {
                        "frontier_path_length": frontier_len,
                        "oracle_extension_length": oracle_len,
                        "total_path_length": total_len,
                        "num_frontier_waypoints": len(frontier_path),
                        "num_oracle_waypoints": len(oracle_extension),
                    },
                }
                with open(json_path, 'w') as f:
                    json.dump(combined_data, f, indent=2)

                print(f"  ✓ {output_stem}.png  |  Frontier: {frontier_len:.2f}m, Oracle ext: {oracle_len:.2f}m")
                total_matched += 1

            except Exception as e:
                print(f"  ✗ Error processing {exp_file.name}: {e}")
                import traceback; traceback.print_exc()

            total_processed += 1

    csv_path = output_dir / 'segment_lengths.csv'
    fieldnames = ['TASK', 'simulation_id', 'frontier_path_length',
                  'oracle_extension_length', 'total_path_length',
                  'num_frontier_waypoints', 'num_oracle_waypoints']
    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_data)

    print(f"\n{'='*80}")
    print(f"Processed: {total_processed} | Matched/generated: {total_matched}")
    print(f"Output: {output_dir}")
    print(f"CSV: {csv_path}")


# ---------------------------------------------------------------------------
# Shared drawing helpers
# ---------------------------------------------------------------------------

def _draw_environment(ax, obstacle_list: List[Rectangle]) -> None:
    """Draw obstacle rectangles and target markers on ax."""
    for obstacle in obstacle_list:
        ax.add_patch(patches.Rectangle(
            (obstacle.x, obstacle.y), obstacle.width, obstacle.height,
            linewidth=2, fill=False, color='saddlebrown',
        ))
    for x, y, label in TARGETS:
        ax.scatter(x, y, s=250, marker='o', color='gray')
        ax.text(x, y, label, fontsize=10, ha='center', va='center')


def _set_axis_limits(ax, all_xs: List[float], all_ys: List[float],
                     margin: float = 1.0) -> None:
    all_xs = all_xs + [t[0] for t in TARGETS]
    all_ys = all_ys + [t[1] for t in TARGETS]
    if all_xs and all_ys:
        ax.set_xlim(min(all_xs) - margin, max(all_xs) + margin)
        ax.set_ylim(min(all_ys) - margin, max(all_ys) + margin)


def _draw_aggregated_positions(ax, xs: List[float], ys: List[float],
                                min_distance: float = 1.0) -> None:
    """Aggregate nearby steps and draw position markers with compact range labels."""
    aggregated = []
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
        color = 'green' if 1 in pos_nums else ('red' if len(xs) in pos_nums else 'lightskyblue')
        ax.scatter(avg_x, avg_y, s=150, marker='o', color=color)
        label_parts: List[str] = []
        seg_start = pos_nums[0]
        seg_end = pos_nums[0]
        for num in pos_nums[1:]:
            if num == seg_end + 1:
                seg_end = num
            else:
                label_parts.append(str(seg_start) if seg_start == seg_end
                                   else f"{seg_start}, {seg_end}" if seg_end == seg_start + 1
                                   else f"{seg_start}-{seg_end}")
                seg_start = seg_end = num
        label_parts.append(str(seg_start) if seg_start == seg_end
                           else f"{seg_start}, {seg_end}" if seg_end == seg_start + 1
                           else f"{seg_start}-{seg_end}")
        ax.text(avg_x, avg_y, ', '.join(label_parts), fontsize=8, ha='center', va='center')


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description='Path generation: single paths, oracle paths, or frontier-oracle combined.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_paths.py path --start-x 0 --start-y 0 --goal-x 9.2 --goal-y 0.17 --visualize
  python generate_paths.py oracle
  python generate_paths.py oracle --single experiments/TASK_01.../1_pos_1_experiment_...json
  python generate_paths.py frontier-oracle
""",
    )
    sub = parser.add_subparsers(dest='command')

    # ---- path ----
    path_p = sub.add_parser('path', help='Plan a single path between two coordinates.')
    path_p.add_argument('--start-x', type=float, required=True)
    path_p.add_argument('--start-y', type=float, required=True)
    path_p.add_argument('--goal-x', type=float, required=True)
    path_p.add_argument('--goal-y', type=float, required=True)
    path_p.add_argument('--margin', type=float, default=0.3,
                        help='Safety margin around obstacles (default: 0.3 m)')
    path_p.add_argument('--output', type=str, default=None,
                        help='Image output path (requires --visualize)')
    path_p.add_argument('--json', type=str, default=None,
                        help='JSON output path for waypoints')
    path_p.add_argument('--visualize', action='store_true',
                        help='Show/save visualization')

    # ---- oracle ----
    oracle_p = sub.add_parser('oracle', help='Generate oracle paths for experiment files.')
    oracle_p.add_argument('--experiments-dir', default='experiments')
    oracle_p.add_argument('--output-dir', default='experiments/oracles')
    oracle_p.add_argument('--margin', type=float, default=0.3)
    oracle_p.add_argument('--no-visualize', action='store_true',
                          help='Skip generating visualization images')
    oracle_p.add_argument('--single', type=str, default=None,
                          help='Process a single experiment file')

    # ---- frontier-oracle ----
    fo_p = sub.add_parser('frontier-oracle',
                          help='Combine frontier exploration paths with oracle extensions.')
    fo_p.add_argument('--base-dir', default='experiments')
    fo_p.add_argument('--frontier-subdir', default='frontier_paths')
    fo_p.add_argument('--output-subdir', default='frontier_oracle')
    fo_p.add_argument('--margin', type=float, default=0.3)

    args = parser.parse_args()

    # ------------------------------------------------------------------ path
    if args.command == 'path':
        start = (args.start_x, args.start_y)
        goal = (args.goal_x, args.goal_y)
        print(f"Generating path from {start} to {goal}…")
        path = generate_path(start, goal, obstacles, margin=args.margin)
        path_length = calculate_path_length_tuples(path)
        direct_length = float(np.linalg.norm(np.array(goal) - np.array(start)))
        print(f"\nPath: {len(path)} waypoints")
        for i, wp in enumerate(path):
            print(f"  {i}: ({wp[0]:.3f}, {wp[1]:.3f})")
        print(f"\nPath length:     {path_length:.3f} m")
        print(f"Direct distance: {direct_length:.3f} m")
        print(f"Efficiency:      {direct_length / path_length * 100:.1f}%")
        if args.json:
            path_data = {
                "start": {"x": start[0], "y": start[1]},
                "goal": {"x": goal[0], "y": goal[1]},
                "waypoints": [{"x": p[0], "y": p[1]} for p in path],
                "metrics": {
                    "path_length": path_length,
                    "direct_distance": direct_length,
                    "efficiency_percent": direct_length / path_length * 100,
                    "num_waypoints": len(path),
                },
            }
            with open(args.json, 'w') as f:
                json.dump(path_data, f, indent=2)
            print(f"\nPath data saved to: {args.json}")
        if args.visualize:
            visualize_single_path(start, goal, path, obstacles, save_path=args.output)

    # --------------------------------------------------------------- oracle
    elif args.command == 'oracle':
        do_viz = not args.no_visualize
        if args.single:
            os.makedirs(args.output_dir, exist_ok=True)
            print(f"Processing single experiment: {args.single}")
            try:
                oracle_data = generate_oracle_path_for_experiment(
                    args.single, args.output_dir, margin=args.margin, visualize=do_viz)
                print(f"✓  Waypoints: {oracle_data['metrics']['num_waypoints']}, "
                      f"Length: {oracle_data['metrics']['path_length']:.2f} m")
            except Exception as e:
                print(f"✗  Error: {e}")
        else:
            generate_all_oracle_paths(args.experiments_dir, args.output_dir,
                                      margin=args.margin, visualize=do_viz)

    # -------------------------------------------------------- frontier-oracle
    elif args.command == 'frontier-oracle':
        generate_all_frontier_oracle_paths(
            base_dir=args.base_dir,
            frontier_subdir=args.frontier_subdir,
            output_subdir=args.output_subdir,
            margin=args.margin,
        )

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
