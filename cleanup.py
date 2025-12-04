"""
Cleanup script for university submission.
Removes unnecessary files and creates .gitignore.
"""

import os
import glob


def cleanup():
    """Clean up project directory for submission."""

    # List of file prefixes to delete
    prefixes_to_delete = ['AUDIT', 'ISSUES',
                          'FINAL', 'DETAILED', 'DELIVERY', '00_START']

    # Get current directory
    current_dir = os.getcwd()

    # Delete files matching prefixes
    deleted_count = 0
    for prefix in prefixes_to_delete:
        pattern = os.path.join(current_dir, f'{prefix}*')
        files_to_delete = glob.glob(pattern)

        for file_path in files_to_delete:
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    deleted_count += 1
                    print(f"Deleted: {os.path.basename(file_path)}")
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")

    # Create .gitignore if it doesn't exist
    gitignore_path = os.path.join(current_dir, '.gitignore')
    if not os.path.exists(gitignore_path):
        with open(gitignore_path, 'w') as f:
            f.write('.venv/\n')
            f.write('__pycache__/\n')
        print("Created: .gitignore")
    else:
        print(".gitignore already exists")

    print(f"\nCleanup complete ({deleted_count} files deleted)")


if __name__ == '__main__':
    cleanup()
