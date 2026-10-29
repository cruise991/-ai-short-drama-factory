#!/usr/bin/env python3
"""Workspace & Temporary File Hygiene Utility for AI Short Drama Factory.

Safely scans, audits, and removes ephemeral cache files (.DS_Store, __pycache__, .pytest_cache),
provides controlled lifecycle pruning of intermediate project artifacts, and purges obsolete archives.

Usage:
  python3 scripts/clean_workspace.py --status            # Check workspace hygiene & disk usage
  python3 scripts/clean_workspace.py --dry-run           # Preview items to be cleaned
  python3 scripts/clean_workspace.py --execute           # Safely clean ephemeral caches
  python3 scripts/clean_workspace.py --prune-runs        # Preview pruning of old intermediate runs
  python3 scripts/clean_workspace.py --prune-runs --execute --keep 5  # Prune intermediate runs beyond recent 5
  python3 scripts/clean_workspace.py --purge-archive     # Clean obsolete archive/experiments
"""

import os
import sys
import shutil
import argparse
from pathlib import Path


def format_size(size_bytes: int) -> str:
    """Format bytes to human readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def get_dir_size(path: Path) -> int:
    """Recursively calculate directory size."""
    total = 0
    try:
        for entry in path.rglob('*'):
            if entry.is_file() and not entry.is_symlink():
                total += entry.stat().st_size
    except Exception:
        pass
    return total


def scan_ephemeral_items(workspace_root: Path) -> list[Path]:
    """Find all system and build junk files (.DS_Store, __pycache__, .pytest_cache)."""
    junk_patterns = [
        "**/.DS_Store",
        "**/__pycache__",
        "**/.pytest_cache",
        "**/*.pyc",
        "**/*.pyo",
        "**/.AppleDouble",
        "**/._*"
    ]
    
    found = []
    exclude_dirs = {"venv", ".venv", "env", "node_modules"}
    
    for pat in junk_patterns:
        for p in workspace_root.glob(pat):
            parts = p.parts
            if any(ex in parts for ex in exclude_dirs):
                continue
            found.append(p)
            
    return sorted(list(set(found)))


def prune_old_runs(projects_dir: Path, keep_recent: int = 5, dry_run: bool = True):
    """Prune intermediate run assets (video clips, raw frames, temp audios) of older projects.
    
    Keeps project tickets and metadata intact, while freeing intermediate render runs.
    """
    mode_str = "[DRY-RUN]" if dry_run else "[EXECUTE]"
    print(f"\n{mode_str} Auditing intermediate runs in {projects_dir} (Keeping {keep_recent} most recent projects)...")
    
    if not projects_dir.exists():
        print("  Projects directory does not exist.")
        return
        
    projects = [p for p in projects_dir.iterdir() if p.is_dir() and not p.name.startswith('.')]
    # Sort projects by last modification time descending
    projects.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    
    active_projects = projects[:keep_recent]
    older_projects = projects[keep_recent:]
    
    print(f"  Active Projects (Protected): {len(active_projects)}")
    for p in active_projects:
        print(f"    ⭐ {p.name}")
        
    if not older_projects:
        print("  No older projects exceed the retention threshold.")
        return
        
    print(f"\n  Older Candidate Projects for Run Pruning: {len(older_projects)}")
    freed_bytes = 0
    cleaned_runs = 0
    
    for p in older_projects:
        runs_dir = p / "runs"
        if runs_dir.exists() and runs_dir.is_dir():
            run_size = get_dir_size(runs_dir)
            if run_size > 0:
                print(f"    🗑️ {p.name}/runs ({format_size(run_size)})")
                freed_bytes += run_size
                cleaned_runs += 1
                if not dry_run:
                    shutil.rmtree(runs_dir, ignore_errors=True)
                    # Re-create empty runs directory placeholder
                    runs_dir.mkdir(parents=True, exist_ok=True)
                    
    action_verb = "Would reclaim" if dry_run else "Reclaimed"
    print(f"{mode_str} {action_verb} {format_size(freed_bytes)} across {cleaned_runs} project runs.")


def purge_archive(workspace_root: Path, dry_run: bool = True):
    """Purge temporary experiment files under archive/experiments."""
    mode_str = "[DRY-RUN]" if dry_run else "[EXECUTE]"
    exp_dir = workspace_root / "archive" / "experiments"
    print(f"\n{mode_str} Purging obsolete experiment archive in {exp_dir}...")
    
    if not exp_dir.exists():
        print("  Archive experiments directory is already clean.")
        return
        
    size = get_dir_size(exp_dir)
    if size == 0:
        print("  Archive experiments directory contains 0 bytes.")
        return
        
    print(f"  Found obsolete archive data: {format_size(size)}")
    if not dry_run:
        shutil.rmtree(exp_dir, ignore_errors=True)
        exp_dir.mkdir(parents=True, exist_ok=True)
        print(f"{mode_str} Successfully purged {format_size(size)}.")
    else:
        print(f"{mode_str} Would purge {format_size(size)}.")


def print_status(workspace_root: Path):
    """Print overall workspace hygiene and directory disk usage report."""
    print("=" * 60)
    print("🔍 AI Short Company - Workspace Hygiene & Storage Audit")
    print("=" * 60)
    
    app_root = workspace_root / "ai-short-drama"
    
    key_dirs = [
        ("Workspace Root", workspace_root),
        ("ai-short-drama (Codebase)", app_root),
        ("Models (LivePortrait / Wav2Lip)", workspace_root / "models"),
        ("Media Center (MinIO / Storage)", workspace_root / "media_center"),
        ("Global Agents & Skills (.agents)", workspace_root / ".agents"),
        ("Pipeline Runtime (.agent-video)", workspace_root / ".agent-video"),
        ("Out (Root / Shared Masters)", workspace_root / "out"),
        ("Out (Drama Internal Masters)", app_root / "out"),
        ("Projects (Intermediate Runs)", app_root / "projects"),
        ("Archive (Experiments / History)", workspace_root / "archive"),
    ]
    
    for label, path in key_dirs:
        if path.exists():
            size_str = format_size(get_dir_size(path)) if path.is_dir() else format_size(path.stat().st_size)
            print(f"  📁 {label:<35}: {size_str:>10}")
        else:
            print(f"  ⚪ {label:<35}: (Not present)")
            
    ephemeral = scan_ephemeral_items(workspace_root)
    print("\n🧹 Ephemeral Files Status:")
    print(f"  Pending .DS_Store / Cache / pyc items: {len(ephemeral)}")
    print("=" * 60)


def clean_ephemeral(workspace_root: Path, dry_run: bool = True):
    """Clean system and build ephemeral files."""
    items = scan_ephemeral_items(workspace_root)
    mode_str = "[DRY-RUN]" if dry_run else "[EXECUTE]"
    print(f"\n{mode_str} Scanning ephemeral cache files in {workspace_root}...")
    
    freed_bytes = 0
    cleaned_count = 0
    
    for item in items:
        try:
            if item.is_file() or item.is_symlink():
                size = item.stat().st_size
                if not dry_run:
                    item.unlink(missing_ok=True)
                freed_bytes += size
                cleaned_count += 1
            elif item.is_dir():
                size = get_dir_size(item)
                if not dry_run:
                    shutil.rmtree(item, ignore_errors=True)
                freed_bytes += size
                cleaned_count += 1
        except Exception as e:
            print(f"  [Warning] Failed to clean {item}: {e}")
            
    action_verb = "Would remove" if dry_run else "Cleaned"
    print(f"{mode_str} {action_verb} {cleaned_count} items. Total space: {format_size(freed_bytes)}.")


def main():
    parser = argparse.ArgumentParser(description="Clean and audit AI Short Drama workspace.")
    parser.add_argument("--dry-run", action="store_true", help="Preview items to be deleted without removing them.")
    parser.add_argument("--execute", action="store_true", help="Safely perform deletions.")
    parser.add_argument("--status", action="store_true", help="Show workspace hygiene and disk usage breakdown.")
    parser.add_argument("--prune-runs", action="store_true", help="Prune intermediate runs of older projects.")
    parser.add_argument("--keep", type=int, default=5, help="Number of recent projects to protect during prune-runs (default: 5).")
    parser.add_argument("--purge-archive", action="store_true", help="Purge obsolete experiment archives.")
    
    args = parser.parse_args()
    
    script_dir = Path(__file__).resolve().parent
    drama_root = script_dir.parent
    workspace_root = drama_root.parent
    
    is_dry_run = not args.execute
    
    if args.status:
        print_status(workspace_root)
        return
        
    if args.purge_archive:
        purge_archive(workspace_root, dry_run=is_dry_run)
        if not is_dry_run:
            print_status(workspace_root)
        return
        
    if args.prune_runs:
        projects_dir = drama_root / "projects"
        prune_old_runs(projects_dir, keep_recent=args.keep, dry_run=is_dry_run)
        if not is_dry_run:
            print_status(workspace_root)
        return
        
    # Default: ephemeral clean
    clean_ephemeral(workspace_root, dry_run=is_dry_run)
    if not is_dry_run:
        print_status(workspace_root)
    else:
        print("\n💡 Run with --execute to perform actual cleanup, or --status to view disk usage.")


if __name__ == "__main__":
    main()
