# clean_markers.py - Removes Git markers. Run: python clean_markers.py [dry-run]
import os
import sys

def clean_file(file_path, dry_run=False):
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        cleaned = [line for line in lines if not line.strip().startswith(('<<<<<<<', '=======', '>>>>>>>'))]
        if dry_run:
            print(f"Would clean {file_path}: Removed {len(lines) - len(cleaned)} lines")
            return
        with open(file_path, 'w') as f:
            f.write(''.join(cleaned))
        print(f"Cleaned {file_path}")
    except Exception as e:
        print(f"Error cleaning {file_path}: {e}")

def main(dry_run=False):
    root_dir = '.'  # Current dir
    extensions = ('.py', '.html', '.md', '.txt')  # Adapt
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(extensions):
                clean_file(os.path.join(root, file), dry_run)

if __name__ == '__main__':
    dry_run = len(sys.argv) > 1 and sys.argv[1] == 'dry-run'
    main(dry_run)
