#!/usr/bin/env python3
"""
Path metrics pipeline: calculate, analyze, and export experiment path metrics.

Subcommands
-----------
calculate   Compute robot vs oracle path metrics for experiment folders.
analyze     Print detailed analysis and cross-folder comparison.
export      Write metrics to CSV for spreadsheet applications.

With no subcommand all three stages run in sequence.

Replaces: calculate_path_metrics.py, analyze_path_metrics.py, export_metrics_to_csv.py
"""

import os
import json
import csv
import glob
import argparse
import numpy as np
from typing import Dict, List, Tuple


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def distanceBetweenPoints(p1: List[float], p2: List[float]) -> float:
    """Euclidean distance between two points."""
    return float(np.linalg.norm(np.array(p1) - np.array(p2)))


# ---------------------------------------------------------------------------
# calculate  –  originally calculate_path_metrics.py
# ---------------------------------------------------------------------------

def calculate_path_length(waypoints: List[Dict[str, float]]) -> float:
    """
    Total length of a path given a list of ``{'x': …, 'y': …}`` dicts.
    """
    if len(waypoints) < 2:
        return 0.0
    total = 0.0
    for i in range(len(waypoints) - 1):
        p1 = [waypoints[i]['x'], waypoints[i]['y']]
        p2 = [waypoints[i + 1]['x'], waypoints[i + 1]['y']]
        total += distanceBetweenPoints(p1, p2)
    return total


def extract_robot_path(experiment_data: dict) -> List[Dict[str, float]]:
    """Extract the robot's actual path from experiment iterations."""
    waypoints = []
    initial_pose = experiment_data.get('initialRobotPose', {})
    if 'position' in initial_pose:
        pos = initial_pose['position']
        waypoints.append({'x': pos['x'], 'y': pos['y']})

    for iteration in experiment_data.get('iterations', []):
        if 'endRobotStatus' in iteration and 'position' in iteration['endRobotStatus']:
            pos = iteration['endRobotStatus']['position']
            waypoints.append({'x': pos['x'], 'y': pos['y']})
        elif 'robotPose' in iteration and 'position' in iteration['robotPose']:
            pos = iteration['robotPose']['position']
            waypoints.append({'x': pos['x'], 'y': pos['y']})
    return waypoints


def calculate_final_distance_to_target(robot_path: List[Dict[str, float]],
                                       target_position: Dict[str, float]) -> float:
    """Distance from the final robot position to the target."""
    if not robot_path:
        return float('inf')
    final_pos = robot_path[-1]
    return distanceBetweenPoints(
        [final_pos['x'], final_pos['y']],
        [target_position['x'], target_position['y']],
    )


def calculate_path_length_ratio(robot_path: List[Dict[str, float]],
                                oracle_path: List[Dict[str, float]]) -> float:
    """Robot path length / oracle path length (1.0 = equal, >1.0 = robot detoured)."""
    robot_length = calculate_path_length(robot_path)
    oracle_length = calculate_path_length(oracle_path)
    if oracle_length == 0:
        return float('inf') if robot_length > 0 else 1.0
    return robot_length / oracle_length


def process_experiment(experiment_file: str, oracle_file: str) -> Dict:
    """Compute path metrics for a single experiment / oracle file pair."""
    with open(experiment_file, 'r') as f:
        experiment_data = json.load(f)
    with open(oracle_file, 'r') as f:
        oracle_data = json.load(f)

    robot_path = extract_robot_path(experiment_data)
    oracle_path = oracle_data.get('waypoints', [])
    target_position = oracle_data.get('targetPosition') or oracle_data.get('goal', {})

    robot_length = calculate_path_length(robot_path)
    oracle_length = calculate_path_length(oracle_path)
    path_length_ratio = calculate_path_length_ratio(robot_path, oracle_path)
    final_distance = calculate_final_distance_to_target(robot_path, target_position)

    return {
        'experiment_file': os.path.basename(experiment_file),
        'experiment_id': experiment_data.get('id', 'unknown'),
        'prompt': experiment_data.get('prompt', '').strip(),
        'goal_completed': experiment_data.get('goalCompleted', False),
        'num_iterations': experiment_data.get('numberOfIterations', 0),
        'robot_path_length': round(robot_length, 3),
        'oracle_path_length': round(oracle_length, 3),
        'path_length_ratio': round(path_length_ratio, 3),
        'final_distance_to_target': round(final_distance, 3),
        'oracle_metrics': oracle_data.get('metrics', {}),
    }


def process_experiment_folder(folder_path: str, output_file: str = None):
    """Process all experiments in one folder and write a metrics JSON if requested."""
    experiment_files = glob.glob(os.path.join(folder_path, '*.json'))

    results = []
    processed = 0
    skipped = 0

    for exp_file in sorted(experiment_files):
        basename = os.path.basename(exp_file)
        oracle_basename = basename.replace('.json', '_oracle.json')
        oracle_file = os.path.join('experiments/oracles', oracle_basename)

        if not os.path.exists(oracle_file):
            print(f"Warning: No oracle file for {basename}, skipping")
            skipped += 1
            continue

        try:
            metrics = process_experiment(exp_file, oracle_file)
            results.append(metrics)
            processed += 1
            if processed % 10 == 0:
                print(f"Processed {processed} experiments…")
        except Exception as e:
            print(f"Error processing {basename}: {e}")
            skipped += 1

    print(f"\nProcessed {processed} experiments, skipped {skipped}")

    if not results:
        return None

    completed_results = [r for r in results if r['goal_completed']]

    def _mean(vals):
        return float(np.mean(vals)) if vals else 0.0

    summary = {
        'folder': os.path.basename(folder_path),
        'total_experiments': len(results),
        'completed_experiments': len(completed_results),
        'average_robot_path_length': round(_mean([r['robot_path_length'] for r in results]), 3),
        'average_oracle_path_length': round(_mean([r['oracle_path_length'] for r in results]), 3),
        'average_path_length_ratio': round(_mean([r['path_length_ratio'] for r in results]), 3),
        'average_final_distance_to_target': round(_mean([r['final_distance_to_target'] for r in results]), 3),
        'average_robot_path_length_completed_only': round(_mean([r['robot_path_length'] for r in completed_results]), 3),
        'average_oracle_path_length_completed_only': round(_mean([r['oracle_path_length'] for r in completed_results]), 3),
        'average_path_length_ratio_completed_only': round(_mean([r['path_length_ratio'] for r in completed_results]), 3),
        'average_final_distance_to_target_completed_only': round(_mean([r['final_distance_to_target'] for r in completed_results]), 3),
    }

    output = {'summary': summary, 'experiments': results}

    if output_file:
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        print(f"\nResults saved to {output_file}")

    s = summary
    print(f"\n{'='*80}")
    print(f"Summary for {s['folder']}")
    print(f"{'='*80}")
    print(f"Total experiments:              {s['total_experiments']}")
    print(f"Completed experiments:          {s['completed_experiments']}")
    print(f"Average robot path length:      {s['average_robot_path_length']}")
    print(f"Average oracle path length:     {s['average_oracle_path_length']}")
    print(f"Average path length ratio:      {s['average_path_length_ratio']}")
    print(f"Average final distance:         {s['average_final_distance_to_target']}")
    print(f"\nCompleted experiments only:")
    print(f"  Average robot path length:    {s['average_robot_path_length_completed_only']}")
    print(f"  Average oracle path length:   {s['average_oracle_path_length_completed_only']}")
    print(f"  Average path length ratio:    {s['average_path_length_ratio_completed_only']}")
    print(f"  Average final distance:       {s['average_final_distance_to_target_completed_only']}")

    return output


def process_all_folders(experiments_dir: str = 'experiments'):
    """Process every experiment folder and write a combined summary JSON."""
    folders = [
        d for d in os.listdir(experiments_dir)
        if os.path.isdir(os.path.join(experiments_dir, d))
        and d not in ['oracles', 'paths', 'frontier_paths', 'frontier_oracle', 'comparison']
    ]

    all_results = {}
    for folder in sorted(folders):
        folder_path = os.path.join(experiments_dir, folder)
        output_file = os.path.join(experiments_dir, f"{folder}_metrics.json")

        print(f"\n{'#'*60}")
        print(f"Processing folder: {folder}")
        print(f"{'#'*60}")

        result = process_experiment_folder(folder_path, output_file)
        if result:
            all_results[folder] = result['summary']

    if all_results:
        combined_output = os.path.join(experiments_dir, 'all_metrics_summary.json')
        with open(combined_output, 'w') as f:
            json.dump(all_results, f, indent=2)
        print(f"\n\nCombined summary saved to {combined_output}")

        print(f"\n{'='*140}")
        print(f"Comparison Across All Folders")
        print(f"{'='*140}")
        print(f"{'Folder':<40} {'Exp':<8} {'Comp':<8} {'Robot Len':<12} {'Oracle Len':<12} "
              f"{'Ratio':<10} {'Final Dist':<12}")
        print(f"{'-'*140}")
        for folder, s in sorted(all_results.items()):
            print(f"{folder:<40} {s['total_experiments']:<8} {s['completed_experiments']:<8} "
                  f"{s['average_robot_path_length']:<12} {s['average_oracle_path_length']:<12} "
                  f"{s['average_path_length_ratio']:<10} {s['average_final_distance_to_target']:<12}")


# ---------------------------------------------------------------------------
# analyze  –  originally analyze_path_metrics.py
# ---------------------------------------------------------------------------

def print_detailed_analysis(metrics_file: str):
    """Print detailed analysis for a single metrics JSON file."""
    with open(metrics_file, 'r') as f:
        data = json.load(f)

    summary = data['summary']
    experiments = data['experiments']

    print(f"\n{'='*80}")
    print(f"DETAILED ANALYSIS: {summary['folder']}")
    print(f"{'='*80}\n")

    print(f"Overall Statistics:")
    print(f"  Total experiments: {summary['total_experiments']}")
    print(f"  Completed: {summary['completed_experiments']} "
          f"({summary['completed_experiments']/summary['total_experiments']*100:.1f}%)")
    print(f"  Failed: {summary['total_experiments'] - summary['completed_experiments']}")

    completed = [e for e in experiments if e['goal_completed']]
    failed = [e for e in experiments if not e['goal_completed']]

    if completed:
        robot_lengths = [e['robot_path_length'] for e in completed]
        oracle_lengths = [e['oracle_path_length'] for e in completed]
        ratios = [e['path_length_ratio'] for e in completed]
        final_distances = [e['final_distance_to_target'] for e in completed]
        iterations = [e['num_iterations'] for e in completed]

        def _stats(vals, label):
            print(f"  {label}:")
            print(f"    Mean: {sum(vals)/len(vals):.3f}")
            print(f"    Min:  {min(vals):.3f}")
            print(f"    Max:  {max(vals):.3f}")

        print(f"\nCompleted Experiments Metrics:")
        _stats(robot_lengths, "Robot Path Length")
        _stats(oracle_lengths, "Oracle Path Length")
        _stats(ratios, "Path Length Ratio")
        _stats(final_distances, "Final Distance to Target")

        print(f"  Iterations:")
        print(f"    Mean: {sum(iterations)/len(iterations):.1f}")
        print(f"    Min:  {min(iterations)}")
        print(f"    Max:  {max(iterations)}")

        print(f"\nPath Length Ratio Distribution (Completed):")
        excellent = len([e for e in completed if e['path_length_ratio'] < 1.2])
        good = len([e for e in completed if 1.2 <= e['path_length_ratio'] < 1.5])
        fair = len([e for e in completed if 1.5 <= e['path_length_ratio'] < 2.0])
        poor = len([e for e in completed if e['path_length_ratio'] >= 2.0])
        n = len(completed)
        print(f"  Excellent (<1.2):    {excellent} ({excellent/n*100:.1f}%)")
        print(f"  Good (1.2-1.5):      {good} ({good/n*100:.1f}%)")
        print(f"  Fair (1.5-2.0):      {fair} ({fair/n*100:.1f}%)")
        print(f"  Poor (>=2.0):        {poor} ({poor/n*100:.1f}%)")

        print(f"\nFinal Distance to Target Distribution (Completed):")
        very_close = len([e for e in completed if e['final_distance_to_target'] < 0.5])
        close = len([e for e in completed if 0.5 <= e['final_distance_to_target'] < 1.0])
        moderate = len([e for e in completed if 1.0 <= e['final_distance_to_target'] < 2.0])
        far = len([e for e in completed if e['final_distance_to_target'] >= 2.0])
        print(f"  Very Close (<0.5):   {very_close} ({very_close/n*100:.1f}%)")
        print(f"  Close (0.5-1.0):     {close} ({close/n*100:.1f}%)")
        print(f"  Moderate (1.0-2.0):  {moderate} ({moderate/n*100:.1f}%)")
        print(f"  Far (>=2.0):         {far} ({far/n*100:.1f}%)")

        print(f"\nTop 3 Best Performers (by Path Length Ratio):")
        sorted_by_ratio = sorted(completed, key=lambda e: e['path_length_ratio'])
        for i, exp in enumerate(sorted_by_ratio[:3], 1):
            print(f"  {i}. {exp['experiment_file']}")
            print(f"     Ratio: {exp['path_length_ratio']}, Final Dist: {exp['final_distance_to_target']}, Iterations: {exp['num_iterations']}")
            print(f"     Robot/Oracle Length: {exp['robot_path_length']}/{exp['oracle_path_length']}")
            print(f"     Prompt: {exp['prompt'][:60]}…")

        print(f"\nTop 3 Worst Performers (by Path Length Ratio):")
        for i, exp in enumerate(sorted_by_ratio[-3:], 1):
            print(f"  {i}. {exp['experiment_file']}")
            print(f"     Ratio: {exp['path_length_ratio']}, Final Dist: {exp['final_distance_to_target']}, Iterations: {exp['num_iterations']}")
            print(f"     Robot/Oracle Length: {exp['robot_path_length']}/{exp['oracle_path_length']}")
            print(f"     Prompt: {exp['prompt'][:60]}…")

    if failed:
        print(f"\nFailed Experiments:")
        for exp in failed:
            print(f"  - {exp['experiment_file']}")
            print(f"    Prompt: {exp['prompt'][:60]}…")
            print(f"    Iterations: {exp['num_iterations']}")

    print(f"\n{'='*80}\n")


def compare_folders():
    """Compare metrics across all experiment folders using all_metrics_summary.json."""
    summary_file = 'experiments/all_metrics_summary.json'
    if not os.path.exists(summary_file):
        print(f"Error: {summary_file} not found. Run: python path_metrics.py calculate")
        return

    with open(summary_file, 'r') as f:
        all_summaries = json.load(f)

    print(f"\n{'='*100}")
    print(f"COMPARISON ACROSS ALL FOLDERS")
    print(f"{'='*100}\n")

    sorted_folders = sorted(
        all_summaries.items(),
        key=lambda x: x[1]['average_path_length_ratio_completed_only'],
    )

    print("Ranked by Path Length Ratio (lower is better):\n")
    print(f"{'Rank':<6} {'Folder':<40} {'Completed':<12} {'Ratio':<12} {'Final Dist':<12}")
    print(f"{'-'*100}")
    for rank, (folder, s) in enumerate(sorted_folders, 1):
        pct = s['completed_experiments'] / s['total_experiments'] * 100
        print(f"{rank:<6} {folder:<40} "
              f"{s['completed_experiments']}/{s['total_experiments']} ({pct:.0f}%)  "
              f"{s['average_path_length_ratio_completed_only']:<12.3f} "
              f"{s['average_final_distance_to_target_completed_only']:<12.3f}")

    sorted_by_completion = sorted(
        all_summaries.items(),
        key=lambda x: x[1]['completed_experiments'] / x[1]['total_experiments'],
        reverse=True,
    )

    print("\n\nRanked by Completion Rate:\n")
    print(f"{'Rank':<6} {'Folder':<40} {'Completion Rate':<20} {'Total':<10}")
    print(f"{'-'*100}")
    for rank, (folder, s) in enumerate(sorted_by_completion, 1):
        pct = s['completed_experiments'] / s['total_experiments'] * 100
        print(f"{rank:<6} {folder:<40} "
              f"{s['completed_experiments']}/{s['total_experiments']} ({pct:.1f}%)       "
              f"{s['total_experiments']:<10}")

    best_ratio_folder, best_ratio = min(
        all_summaries.items(),
        key=lambda x: x[1]['average_path_length_ratio_completed_only'] if x[1]['completed_experiments'] > 0 else float('inf'),
    )
    best_completion_folder, best_completion = max(
        all_summaries.items(),
        key=lambda x: x[1]['completed_experiments'] / x[1]['total_experiments'],
    )
    best_distance_folder, best_distance = min(
        all_summaries.items(),
        key=lambda x: x[1]['average_final_distance_to_target_completed_only'] if x[1]['completed_experiments'] > 0 else float('inf'),
    )

    print("\n\nKey Insights:")
    if best_ratio['completed_experiments'] > 0:
        print(f"\n  Best Path Length Ratio: {best_ratio_folder}")
        print(f"     {best_ratio['average_path_length_ratio_completed_only']:.3f} average ratio")
    completion_rate = best_completion['completed_experiments'] / best_completion['total_experiments'] * 100
    print(f"\n  Best Completion Rate: {best_completion_folder}")
    print(f"     {best_completion['completed_experiments']}/{best_completion['total_experiments']} ({completion_rate:.1f}%) completed")
    if best_distance['completed_experiments'] > 0:
        print(f"\n  Closest to Target: {best_distance_folder}")
        print(f"     {best_distance['average_final_distance_to_target_completed_only']:.3f} average final distance")

    print(f"\n{'='*100}\n")


# ---------------------------------------------------------------------------
# export  –  originally export_metrics_to_csv.py
# ---------------------------------------------------------------------------

def export_folder_to_csv(metrics_file: str, output_csv: str = None):
    """Export metrics from one folder JSON to CSV."""
    with open(metrics_file, 'r') as f:
        data = json.load(f)

    if output_csv is None:
        output_csv = metrics_file.replace('_metrics.json', '_metrics.csv')

    fieldnames = [
        'experiment_file', 'experiment_id', 'prompt', 'goal_completed',
        'num_iterations', 'robot_path_length', 'oracle_path_length',
        'path_length_ratio', 'final_distance_to_target', 'folder',
    ]

    with open(output_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for exp in data['experiments']:
            row = dict(exp)
            row['folder'] = data['summary']['folder']
            writer.writerow({k: row.get(k, '') for k in fieldnames})

    print(f"Exported to {output_csv}")


def export_all_to_csv(output_csv: str = 'experiments/all_experiments_metrics.csv'):
    """Export all experiment metrics across all folders to a single CSV."""
    metrics_files = glob.glob('experiments/*_metrics.json')
    metrics_files = [f for f in metrics_files if 'all_metrics_summary.json' not in f]

    if not metrics_files:
        print("No metrics files found. Run: python path_metrics.py calculate")
        return

    all_experiments = []
    for metrics_file in metrics_files:
        with open(metrics_file, 'r') as f:
            data = json.load(f)
        folder = data['summary']['folder']
        for exp in data['experiments']:
            exp = dict(exp)
            exp['folder'] = folder
            all_experiments.append(exp)

    def extract_sort_keys(exp):
        folder = exp.get('folder', '')
        exp_file = exp.get('experiment_file', '')
        task_num = 999
        if 'TASK_' in folder:
            try:
                task_num = int(folder.split('TASK_')[1].split('_')[0])
            except (IndexError, ValueError):
                pass
        exp_num = 999
        try:
            exp_num = int(os.path.basename(exp_file).split('_')[0])
        except (IndexError, ValueError):
            pass
        return (task_num, exp_num, folder, exp_file)

    all_experiments.sort(key=extract_sort_keys)

    fieldnames = [
        'folder', 'experiment_file', 'experiment_id', 'prompt', 'goal_completed',
        'num_iterations', 'robot_path_length', 'oracle_path_length',
        'path_length_ratio', 'final_distance_to_target',
    ]

    with open(output_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for exp in all_experiments:
            writer.writerow({k: exp.get(k, '') for k in fieldnames})

    print(f"\nExported {len(all_experiments)} experiments to {output_csv}")
    print(f"Total folders: {len(metrics_files)}")


def export_summary_to_csv(output_csv: str = 'experiments/folders_summary.csv'):
    """Export per-folder summary statistics to CSV."""
    summary_file = 'experiments/all_metrics_summary.json'
    if not os.path.exists(summary_file):
        print(f"Error: {summary_file} not found. Run: python path_metrics.py calculate")
        return

    with open(summary_file, 'r') as f:
        all_summaries = json.load(f)

    fieldnames = [
        'folder', 'total_experiments', 'completed_experiments',
        'completion_rate_percent',
        'average_robot_path_length', 'average_oracle_path_length',
        'average_path_length_ratio', 'average_final_distance_to_target',
        'average_robot_path_length_completed_only',
        'average_oracle_path_length_completed_only',
        'average_path_length_ratio_completed_only',
        'average_final_distance_to_target_completed_only',
    ]

    with open(output_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for folder, s in sorted(all_summaries.items()):
            completion_rate = s['completed_experiments'] / s['total_experiments'] * 100
            row = dict(s)
            row['folder'] = folder
            row['completion_rate_percent'] = round(completion_rate, 2)
            writer.writerow({k: row.get(k, '') for k in fieldnames})

    print(f"\nExported {len(all_summaries)} folder summaries to {output_csv}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Path metrics pipeline: calculate → analyze → export.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python path_metrics.py                              # run all three stages
  python path_metrics.py calculate                    # compute metrics for all folders
  python path_metrics.py calculate experiments/TASK_01_go_to_the_pile_of_pallets
  python path_metrics.py analyze                      # compare all folders
  python path_metrics.py analyze experiments/TASK_01_go_to_the_pile_of_pallets_metrics.json
  python path_metrics.py export                       # write CSV files
  python path_metrics.py export experiments/TASK_01_go_to_the_pile_of_pallets_metrics.json
""",
    )
    sub = parser.add_subparsers(dest='command')

    # calculate
    calc_p = sub.add_parser('calculate', help='Compute path metrics for experiment folders.')
    calc_p.add_argument('folder', nargs='?', help='Specific experiment folder (default: all).')
    calc_p.add_argument('output', nargs='?', help='Output JSON file (only with <folder>).')

    # analyze
    anl_p = sub.add_parser('analyze', help='Analyze and compare path metrics.')
    anl_p.add_argument('metrics_file', nargs='?',
                       help='Specific metrics JSON file (default: compare all folders).')

    # export
    exp_p = sub.add_parser('export', help='Export metrics to CSV.')
    exp_p.add_argument('metrics_file', nargs='?',
                       help='Specific folder metrics JSON (default: export everything).')
    exp_p.add_argument('output_csv', nargs='?', help='Output CSV file path.')

    args = parser.parse_args()

    if args.command == 'calculate':
        if args.folder:
            process_experiment_folder(args.folder, args.output)
        else:
            process_all_folders()

    elif args.command == 'analyze':
        if args.metrics_file:
            if os.path.exists(args.metrics_file):
                print_detailed_analysis(args.metrics_file)
            else:
                print(f"Error: File {args.metrics_file} not found")
        else:
            compare_folders()
            print("\nFor detailed analysis of a specific folder, run:")
            print("  python path_metrics.py analyze experiments/<folder>_metrics.json")

    elif args.command == 'export':
        if args.metrics_file:
            if os.path.exists(args.metrics_file):
                export_folder_to_csv(args.metrics_file, args.output_csv)
            else:
                print(f"Error: File {args.metrics_file} not found")
        else:
            print("Exporting all metrics to CSV files…")
            export_all_to_csv()
            export_summary_to_csv()
            print("\nCSV files created:")
            print("  - experiments/all_experiments_metrics.csv")
            print("  - experiments/folders_summary.csv")

    else:
        # No subcommand → run all three stages
        print("Running full pipeline: calculate → analyze → export")
        print("\n--- CALCULATE ---")
        process_all_folders()
        print("\n--- ANALYZE ---")
        compare_folders()
        print("\n--- EXPORT ---")
        export_all_to_csv()
        export_summary_to_csv()


if __name__ == '__main__':
    main()
