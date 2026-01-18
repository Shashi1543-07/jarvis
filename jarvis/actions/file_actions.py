import os
import shutil
import datetime
import glob

def create_file(file_path, content=""):
    print(f"Creating file: {file_path}")
    try:
        with open(file_path, "w") as f:
            f.write(content)
        return f"File created: {file_path}"
    except Exception as e:
        return f"Error creating file: {e}"

def read_file(file_path):
    print(f"Reading file: {file_path}")
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                content = f.read()
            return content
        except Exception as e:
            return f"Error reading file: {e}"
    else:
        return "File not found."

def write_file(file_path, content):
    print(f"Writing to file: {file_path}")
    try:
        with open(file_path, "w") as f:
            f.write(content)
        return f"Written to {file_path}"
    except Exception as e:
        return f"Error writing to file: {e}"

def delete_file(file_path):
    print(f"Deleting file: {file_path}")
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            return f"Deleted {file_path}"
        except Exception as e:
            return f"Error deleting file: {e}"
    else:
        return "File not found."

def search_file(query, path="."):
    print(f"Searching for {query} in {path}...")
    results = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if query in file:
                results.append(os.path.join(root, file))
    return results if results else "No files found."

def open_folder(folder_path):
    print(f"Opening folder: {folder_path}")
    if os.path.exists(folder_path):
        try:
            import subprocess
            # For Windows, use explorer command
            subprocess.Popen(['explorer', os.path.abspath(folder_path)])
            return f"Opened {folder_path}"
        except Exception as e:
            return f"Error opening folder: {e}"
    else:
        return "Folder not found."

def create_folder(folder_path):
    print(f"Creating folder: {folder_path}")
    try:
        os.makedirs(folder_path, exist_ok=True)
        return f"Folder created: {folder_path}"
    except Exception as e:
        return f"Error creating folder: {e}"

def delete_folder(folder_path):
    print(f"Deleting folder: {folder_path}")
    if os.path.exists(folder_path):
        try:
            shutil.rmtree(folder_path)
            return f"Deleted folder {folder_path}"
        except Exception as e:
            return f"Error deleting folder: {e}"
    else:
        return "Folder not found."

def rename_file(old_path, new_path):
    print(f"Renaming {old_path} to {new_path}")
    try:
        os.rename(old_path, new_path)
        return f"Renamed {old_path} to {new_path}"
    except Exception as e:
        return f"Error renaming file: {e}"

def copy_file(source, destination):
    print(f"Copying {source} to {destination}")
    try:
        shutil.copy2(source, destination)
        return f"Copied {source} to {destination}"
    except Exception as e:
        return f"Error copying file: {e}"

def move_file(source, destination):
    print(f"Moving {source} to {destination}")
    try:
        shutil.move(source, destination)
        return f"Moved {source} to {destination}"
    except Exception as e:
        return f"Error moving file: {e}"

def create_note(content):
    print(f"Creating note: {content}")
    file_path = "notes.txt"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(file_path, "a") as f:
        f.write(f"[{timestamp}] {content}\n")
    return f"Note saved: {content}"

def read_notes():
    print("Reading notes...")
    file_path = "notes.txt"
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            notes = f.read()
        return notes
    else:
        return "No notes found."

def delete_note(content_snippet):
    # This is a bit tricky with a text file, implementing a simple line removal
    print(f"Deleting note containing: {content_snippet}")
    file_path = "notes.txt"
    if not os.path.exists(file_path):
        return "No notes found."
    
    with open(file_path, "r") as f:
        lines = f.readlines()
    
    new_lines = [line for line in lines if content_snippet not in line]
    
    with open(file_path, "w") as f:
        f.writelines(new_lines)
    
    return "Note deleted if found."

def read_document_aloud(file_path):
    """Read a document aloud using TTS"""
    print(f"Reading document: {file_path}")
    if not os.path.exists(file_path):
        return "File not found."
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Return the content to be spoken by the TTS engine
        # The router will handle passing it to TTS
        return f"Reading {file_path}: {content}"
    except Exception as e:
        return f"Error reading file: {e}"

def organize_folder(path):
    """Sorts files into subfolders based on their extension types."""
    if not os.path.exists(path):
        return "Folder not found."
    
    categories = {
        "Documents": [".pdf", ".docx", ".txt", ".csv", ".xlsx", ".pptx"],
        "Media": [".mp3", ".mp4", ".wav", ".avi", ".mkv"],
        "Images": [".jpg", ".jpeg", ".png", ".gif", ".svg"],
        "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
        "Source": [".py", ".js", ".html", ".css", ".cpp", ".c", ".go", ".json"]
    }

    count = 0
    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        if os.path.isfile(item_path):
            ext = os.path.splitext(item)[1].lower()
            target_cat = "Others"
            for cat, exts in categories.items():
                if ext in exts:
                    target_cat = cat
                    break
            
            target_dir = os.path.join(path, target_cat)
            os.makedirs(target_dir, exist_ok=True)
            shutil.move(item_path, os.path.join(target_dir, item))
            count += 1
            
    return f"Folder organized. Moved {count} files into categories."
