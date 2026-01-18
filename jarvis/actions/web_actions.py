import webbrowser
import requests
import os

def google_search(query):
    print(f"Searching Google for: {query}")
    webbrowser.open(f"https://www.google.com/search?q={query}")

def open_website(url):
    if not url.startswith("http"):
        url = "https://" + url
    print(f"Opening website: {url}")
    webbrowser.open(url)

def youtube_search(query):
    print(f"Searching YouTube for: {query}")
    webbrowser.open(f"https://www.youtube.com/results?search_query={query}")

def youtube_play(query):
    # This is a basic implementation that searches and opens the first result
    # For true "play", we might need selenium or a specific youtube library
    print(f"Playing on YouTube: {query}")
    # Using "I'm Feeling Lucky" style by just searching for now, 
    # or we could try to find a direct link if we had an API key.
    # A simple workaround is playing the first video from search results
    webbrowser.open(f"https://www.youtube.com/results?search_query={query}&sp=EgIQAQ%253D%253D") 

def download_file(url, file_path=None):
    print(f"Downloading file from {url}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        if not file_path:
            file_path = url.split("/")[-1]
            
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192): 
                f.write(chunk)
        print(f"File downloaded to {file_path}")
        return f"File downloaded successfully to {file_path}"
    except Exception as e:
        print(f"Error downloading file: {e}")
        return f"Failed to download file: {e}"

def deep_research(topic):
    """
    Performs a multi-source deep dive on a topic and returns a synthesis.
    """
    from core.internet.research_agent import ResearchAgent
    from core.ollama_brain import OllamaBrain
    
    print(f"WebActions: Triggering deep research on {topic}...")
    agent = ResearchAgent(OllamaBrain())
    return agent.perform_research(topic)

def get_news():
    """
    Fetches the latest news headlines.
    """
    from core.internet.research_agent import ResearchAgent
    from core.ollama_brain import OllamaBrain
    agent = ResearchAgent(OllamaBrain())
    return agent.perform_research("world news today headlines")

def get_weather():
    """
    Fetches current weather information.
    """
    # Placeholder for a proper API call, using research agent for now
    from core.internet.research_agent import ResearchAgent
    from core.ollama_brain import OllamaBrain
    agent = ResearchAgent(OllamaBrain())
    return agent.perform_research("current weather report")
