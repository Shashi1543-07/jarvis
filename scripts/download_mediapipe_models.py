import requests
import os

def download_file(url, dest_folder):
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)
    
    filename = url.split('/')[-1]
    filepath = os.path.join(dest_folder, filename)
    
    if os.path.exists(filepath):
        print(f"File already exists: {filepath}")
        return filepath

    print(f"Downloading {filename}...")
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Downloaded: {filepath}")
        return filepath
    else:
        print(f"Failed to download {filename}. Status code: {response.status_code}")
        return None

if __name__ == "__main__":
    models_dir = "models/mediapipe"
    urls = [
        "https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task",
        "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
    ]
    
    for url in urls:
        download_file(url, models_dir)
