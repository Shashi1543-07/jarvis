# Jarvis AI

**Jarvis AI** is a comprehensive, voice-activated personal assistant designed to automate tasks, control your PC, and provide intelligent responses. Built with Python and modern web technologies, it features a modular architecture, voice interaction, and a futuristic GUI.

## 🚀 Features

*   **Voice Control:** Wake word detection ("Jarvis") and natural language command processing.
*   **Intelligent Brain:** Powered by LLMs (Large Language Models) for reasoning and conversation.
*   **System Automation:** Control screen brightness, volume, launch applications, and manage system power.
*   **Vision System:** (In Development) Camera integration for object detection and scene description.
*   **Modern GUI:** A futuristic interface built with web technologies (HTML/CSS/JS) and PyQt5.
*   **Memory:** Long-term memory to remember user preferences and past interactions.

## 🛠️ Tech Stack

*   **Core:** Python 3.12+
*   **Voice:** `SpeechRecognition`, `pyttsx3`, `pyaudio`
*   **AI/ML:** `google-generativeai` (Gemini), `torch` (for local models)
*   **GUI:** PyQt5, HTML5, CSS3, JavaScript
*   **Automation:** `pyautogui`, `screen_brightness_control`, `ctypes`

## 📦 Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Shashi1543-07/jarvis.git
    cd jarvis
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv .venv
    .\.venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up API Keys:**
    *   Create a `.env` file (or configure environment variables) with your API keys (e.g., `GEMINI_API_KEY`).

## ▶️ Usage

Run the main application:

```bash
python jarvis/app.py
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
