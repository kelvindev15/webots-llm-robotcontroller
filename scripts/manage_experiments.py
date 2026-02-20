#!/usr/bin/env python3
"""
Experiment file maintenance utilities.

Subcommands
-----------
update   Add/correct the ``numberOfIterations`` field in experiment JSON files.
rename   Prepend a progressive numeric prefix to experiment JSON filenames.

Replaces: update_experiments.py, rename_experiments.py
"""

import os
import re
import json
import glob
import argparse
from pathlib import Path


# ---------------------------------------------------------------------------
# update  –  originally update_experiments.py
# ---------------------------------------------------------------------------

def update_experiment_file(file_path: Path) -> bool:
    """
    Update a single experiment JSON file by adding/correcting numberOfIterations.

    Returns True if the file was changed, False otherwise.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if 'iterations' not in data:
            print(f"  ⚠  No 'iterations' field in {file_path.name}")
            return False

        iterations_count = len(data['iterations'])
        current_value = data.get('numberOfIterations')

        if current_value == iterations_count:
            print(f"  ✓  {file_path.name} already correct: {current_value}")
            return False

        if current_value is not None:
            print(f"  ↻  Updating {file_path.name}: {current_value} → {iterations_count}")
        data['numberOfIterations'] = iterations_count

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        print(f"  ✓  Updated {file_path.name}: {iterations_count} iterations")
        return True

    except json.JSONDecodeError as e:
        print(f"  ✗  JSON decode error in {file_path.name}: {e}")
        return False
    except Exception as e:
        print(f"  ✗  Error processing {file_path.name}: {e}")
        return False


def update_all_experiments(experiments_dir: Path) -> None:
    """
    Recursively update all experiment JSON files matching the standard naming
    pattern inside experiments_dir.
    """
    if not experiments_dir.exists():
        print(f"Error: Directory not found: {experiments_dir}")
        return

    pattern = re.compile(r'^\d+_pos_\d+_experiment_gemini-2_0-flash_\d{8}-\d{6}\.json$')
    json_files = [f for f in experiments_dir.rglob('*.json') if pattern.match(f.name)]

    if not json_files:
        print(f"No matching experiment files found in {experiments_dir}")
        return

    print(f"Found {len(json_files)} files to process\n")

    updated = sum(update_experiment_file(f) for f in sorted(json_files))

    print(f"\n{'='*60}")
    print(f"Summary: updated {updated} / {len(json_files)} files")
    print(f"{'='*60}")


# ---------------------------------------------------------------------------
# rename  –  originally rename_experiments.py
# ---------------------------------------------------------------------------

def rename_json_files(glob_pattern: str = 'experiments/Ablation_Gemini*',
                      start_counter: int = 301) -> None:
    """
    Prepend a progressive numeric prefix to every JSON file that matches
    glob_pattern.  Counter starts at start_counter.
    """
    task_dirs = sorted(glob.glob(glob_pattern))
    if not task_dirs:
        print(f"No directories matching '{glob_pattern}' found.")
        return

    counter = start_counter
    for task_dir in task_dirs:
        json_files = sorted(glob.glob(os.path.join(task_dir, '*.json')))
        if not json_files:
            print(f"No JSON files in {task_dir}")
            continue

        print(f"\nProcessing {task_dir}:")
        for json_file in json_files:
            original_name = os.path.basename(json_file)
            new_name = f"{counter}_{original_name}"
            new_path = os.path.join(os.path.dirname(json_file), new_name)
            os.rename(json_file, new_path)
            print(f"  {original_name} → {new_name}")
            counter += 1

    print(f"\nTotal files renamed: {counter - start_counter}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description='Experiment file maintenance: update iteration counts, rename files.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python manage_experiments.py update
  python manage_experiments.py update --dir experiments/TASK_01_go_to_the_pile_of_pallets
  python manage_experiments.py rename
  python manage_experiments.py rename --pattern "experiments/Ablation_*" --start 401
""",
    )
    sub = parser.add_subparsers(dest='command')

    # ---- update ----
    upd_p = sub.add_parser('update',
                            help='Add/correct numberOfIterations in experiment JSON files.')
    upd_p.add_argument('--dir', type=str, default=None,
                       help='Experiments directory to scan (default: <script_dir>/experiments).')

    # ---- rename ----
    ren_p = sub.add_parser('rename', help='Prepend progressive numeric prefix to JSON filenames.')
    ren_p.add_argument('--pattern', type=str, default='experiments/Ablation_Gemini*',
                       help='Glob pattern for directories to process '
                            '(default: experiments/Ablation_Gemini*).')
    ren_p.add_argument('--start', type=int, default=301,
                       help='Starting counter value (default: 301).')

    args = parser.parse_args()

    if args.command == 'update':
        if args.dir:
            experiments_dir = Path(args.dir)
        else:
            experiments_dir = Path(__file__).parent / 'experiments'
        update_all_experiments(experiments_dir)

    elif args.command == 'rename':
        rename_json_files(glob_pattern=args.pattern, start_counter=args.start)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
