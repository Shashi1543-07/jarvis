import base64
import os

face_path = r"c:\Users\lenovo\JarvisAI\jarvis\web\face.png"
html_path = r"c:\Users\lenovo\JarvisAI\jarvis\web\face_image.html"

try:
    with open(face_path, "rb") as f:
        encoded_string = base64.b64encode(f.read()).decode('utf-8')
        base64_src = f"data:image/png;base64,{encoded_string}"

    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Replace the loader line
    new_loader_line = f"const texture = loader.load('{base64_src}');"
    
    # Check if already replaced to avoid double replacement
    if "data:image/png;base64" in html_content:
        print("Image already embedded.")
    else:
        html_content = html_content.replace("const texture = loader.load('face.png');", new_loader_line)
        
        # Also add the initial updateState call if missing
        if "updateState('idle');" not in html_content:
             html_content = html_content.replace("window.addEventListener('resize', () => {", "updateState('idle');\n        window.addEventListener('resize', () => {")

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print("Successfully embedded face.png into face_image.html")

except Exception as e:
    print(f"Error: {e}")
