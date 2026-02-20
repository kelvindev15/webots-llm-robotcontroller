#!/usr/bin/env python3
"""
Experiment analysis tools that query the Ablation_* experiment directories.

Subcommands
-----------
iterations   Report iteration counts per task, position, and run.
scores       Compute and print scoring data (distance + heading) per experiment.

Replaces: analyze_iterations.py, get_scores.py
"""

import json
import os
import argparse
import numpy as np
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# iterations  –  originally analyze_iterations.py
# ---------------------------------------------------------------------------

def extract_experiment_info(filename: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Extract (position, model, timestamp) from a standard experiment filename.

    Expected pattern: ``<id>_pos_<n>_experiment_<model>_<timestamp>.json``
    Returns (None, None, None) on parse failure.
    """
    parts = filename.replace('.json', '').split('_')
    if len(parts) >= 4 and parts[1] == 'pos':
        position = parts[2]
        remaining = '_'.join(parts[3:])
        if 'experiment_' in remaining:
            model_timestamp = remaining.split('experiment_')[1]
            model_parts = model_timestamp.rsplit('_', 1)
            if len(model_parts) == 2:
                return position, model_parts[0], model_parts[1]
            return position, model_timestamp, ''
    return None, None, None


def collect_iteration_counts(experiments_dir: Path) -> Dict:
    """
    Walk Ablation_* directories and collect iteration counts.

    Returns a nested dict: task → position → list of run_info dicts.
    """
    results = defaultdict(lambda: defaultdict(list))

    task_dirs = sorted(d for d in experiments_dir.iterdir()
                       if d.is_dir() and d.name.startswith('Ablation_'))

    for task_dir in task_dirs:
        for json_file in task_dir.glob('*_pos_*.json'):
            try:
                position, model, timestamp = extract_experiment_info(json_file.name)
                if position is None:
                    continue
                with open(json_file, 'r') as f:
                    data = json.load(f)
                results[task_dir.name][position].append({
                    'filename': json_file.name,
                    'model': model,
                    'timestamp': timestamp,
                    'iterations': data.get('numberOfIterations', 0),
                })
            except Exception as e:
                print(f"Error reading {json_file}: {e}")

    return results


def print_iteration_results(results: Dict) -> None:
    print("=" * 50)
    print("EXPERIMENT ITERATIONS PER RUN")
    print("=" * 50)

    for task_name in sorted(results):
        print(f"\n{task_name}")
        print("=" * 50)
        for position in sorted(results[task_name], key=lambda x: int(x)):
            runs = sorted(results[task_name][position], key=lambda r: r['timestamp'])
            for run in runs:
                print(run['iterations'])
        print()


def print_iteration_summary(results: Dict) -> None:
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)

    for task_name in sorted(results):
        positions = results[task_name]
        total_runs = sum(len(runs) for runs in positions.values())
        total_iters = sum(r['iterations'] for runs in positions.values() for r in runs)
        avg = total_iters / total_runs if total_runs > 0 else 0

        print(f"\n{task_name}:")
        print(f"  Total runs: {total_runs}")
        print(f"  Total iterations: {total_iters}")
        print(f"  Average per run: {avg:.2f}")

        for position in sorted(positions, key=lambda x: int(x)):
            runs = positions[position]
            pos_iters = sum(r['iterations'] for r in runs)
            pos_avg = pos_iters / len(runs) if runs else 0
            print(f"    Position {position}: {len(runs)} runs, "
                  f"{pos_iters} total, {pos_avg:.2f} avg")


def cmd_iterations(experiments_dir: Path) -> None:
    print(f"Analyzing experiments in: {experiments_dir}\n")
    results = collect_iteration_counts(experiments_dir)
    print_iteration_results(results)
    print_iteration_summary(results)


# ---------------------------------------------------------------------------
# scores  –  originally get_scores.py
# ---------------------------------------------------------------------------

def calculate_distance_score(distance: float) -> float:
    if distance <= 2.5:
        return 1.0
    return float(1.5 ** -(distance - 2.5))


def calculate_heading_score(angle: Optional[float]) -> float:
    if angle is None:
        return 0.0
    return (np.pi - np.deg2rad(angle)) / np.pi


def calculate_score(distance: float, angle: Optional[float]) -> float:
    return calculate_distance_score(distance) * calculate_heading_score(angle)


def cmd_scores(experiments_dir: Path) -> None:
    task_dirs = sorted(d for d in experiments_dir.iterdir()
                       if d.is_dir() and d.name.startswith('Ablation_'))

    heading_printed = False

    for task_dir in task_dirs:
        json_files = sorted(
            task_dir.glob('*_pos_*_experiment_gemini-2_0-*.json'),
            key=lambda x: int(x.name.split('_')[0]),
        )

        if json_files:
            print(f"\n{task_dir.name}:")

        for json_file in json_files:
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                iterations = data.get('iterations', [])
                if not iterations:
                    print()
                    continue

                scoring_data = sorted(
                    iterations[-1].get('scoringData', []),
                    key=lambda x: x.get('target', {}).get('name', ''),
                )

                if not heading_printed:
                    print('\t'.join(
                        entry.get('target', {}).get('name', 'unknown')
                        for entry in scoring_data
                    ))
                    heading_printed = True

                for entry in scoring_data:
                    distance = entry.get('distance')
                    angle = entry.get('angle')
                    d_score = calculate_distance_score(distance)
                    h_score = calculate_heading_score(angle)
                    score = calculate_score(distance, angle)
                    print(f"{d_score:.4f}", f"{h_score:.4f}", f"{score:.4f}",
                          sep='\t', end='\t')
                print()

            except Exception as e:
                print(f"Error processing {json_file.name}: {e}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description='Analyze Ablation_* experiment directories.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python analyze_experiments.py iterations
  python analyze_experiments.py iterations --dir experiments
  python analyze_experiments.py scores
  python analyze_experiments.py scores --dir experiments
""",
    )
    parser.add_argument('--dir', type=str, default=None,
                        help='Path to the experiments directory '
                             '(default: <script_dir>/experiments).')
    sub = parser.add_subparsers(dest='command')

    sub.add_parser('iterations',
                   help='Report iteration counts per task, position, and run.')
    sub.add_parser('scores',
                   help='Compute distance + heading scores for the last iteration of each run.')

    args = parser.parse_args()

    if args.dir:
        experiments_dir = Path(args.dir)
    else:
        experiments_dir = Path(__file__).parent / 'experiments'

    if not experiments_dir.exists():
        print(f"Error: Directory not found: {experiments_dir}")
        return

    if args.command == 'iterations':
        cmd_iterations(experiments_dir)
    elif args.command == 'scores':
        cmd_scores(experiments_dir)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
