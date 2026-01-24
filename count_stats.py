
import os

def count_lines(start_path):
    total_lines = 0
    total_files = 0
    extensions = ['.py', '.js', '.html', '.css', '.tsx', '.ts', '.json', '.md']
    exclude_dirs = {'venv', '.git', '__pycache__', 'node_modules', 'dist', 'build', '.idea', '.vscode', 'site-packages'}
    
    print(f"Scanning {start_path}...")
    
    for root, dirs, files in os.walk(start_path):
        # Modify dirs in-place to skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            ext = os.path.splitext(file)[1]
            if ext in extensions:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = sum(1 for _ in f)
                        total_lines += lines
                        total_files += 1
                        # print(f"{file}: {lines}")
                except Exception as e:
                    print(f"Error reading {file}: {e}")

    print(f"Total Files: {total_files}")
    print(f"Total Lines: {total_lines}")

if __name__ == "__main__":
    count_lines('.')
