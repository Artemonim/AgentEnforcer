import subprocess
import os

def get_git_modified_files(root_path='.'):
    """
    Gets the list of modified, added, or renamed files from git status.
    
    This runs 'git status --porcelain -u no' to get a machine-readable
    list of files. It includes staged and unstaged changes, but not
    untracked files.
    
    Args:
        root_path (str): The path to the repository root.
        
    Returns:
        list[str]: A list of absolute file paths for modified files.
                   Returns an empty list if git command fails.
    """
    try:
        # -u no -> Excludes untracked files
        # --porcelain -> machine-readable output
        result = subprocess.run(
            ['git', 'status', '--porcelain', '-u', 'no'],
            capture_output=True,
            text=True,
            check=True,
            cwd=root_path,
            encoding='utf-8'
        )
        
        files = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            
            # The format is "XY PATH" or "R  OLD_PATH -> NEW_PATH"
            # We just need the file path at the end.
            parts = line.split()
            if line.startswith('R '): # Renamed file
                # R  "source" -> "destination"
                file_path = parts[-1]
            else: # Modified, Added, Deleted, etc.
                file_path = parts[-1]

            # The path might contain spaces and be quoted
            file_path = file_path.strip('"')

            # Ensure the file exists, as 'git status' can list deleted files
            abs_path = os.path.join(root_path, file_path)
            if os.path.exists(abs_path):
                 files.append(abs_path)
                 
        return files
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        # This can happen if not in a git repo or git is not installed.
        print(f"Warning: Could not get git status: {e}")
        return [] 