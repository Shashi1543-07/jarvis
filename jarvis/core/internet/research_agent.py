from duckduckgo_search import DDGS
from newspaper import Article
import concurrent.futures
import time

class ResearchAgent:
    def __init__(self, ollama_brain):
        self.ollama = ollama_brain
        print("ResearchAgent: Initialized.")

    def search_links(self, query, max_results=3):
        """Finds the most relevant links for a query."""
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                return [r['href'] for r in results]
        except Exception as e:
            print(f"ResearchAgent Error: Search failed - {e}")
            return []

    def extract_content(self, url):
        """Silently scrapes and parses a single URL."""
        try:
            article = Article(url)
            article.download()
            article.parse()
            # We only need the text and title
            return {
                "title": article.title,
                "text": article.text[:3000], # Cap at 3000 chars per source for LLM context
                "url": url
            }
        except Exception as e:
            print(f"ResearchAgent Error: Extraction failed for {url} - {e}")
            return None

    def perform_research(self, topic):
        """
        Deep research: Search -> Extract -> Synthesize
        """
        print(f"ResearchAgent: Starting deep dive on '{topic}'...")
        
        # 1. Discovery
        links = self.search_links(topic)
        if not links:
            return "Sir, I couldn't find any information on that topic in the local digital streams."

        # 2. Parallel Extraction
        extracted_data = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            contents = list(executor.map(self.extract_content, links))
            extracted_data = [c for c in contents if c]

        if not extracted_data:
            return "Sir, I found links but was unable to penetrate their content for analysis."

        # 3. LLM Synthesis
        context = ""
        for i, data in enumerate(extracted_data):
            context += f"--- Source {i+1}: {data['title']} ({data['url']}) ---\n"
            context += f"{data['text']}\n\n"

        prompt = (
            f"You are JARVIS. I need a deep research report on: '{topic}'.\n"
            f"Here is information from {len(extracted_data)} different sources:\n\n"
            f"{context}\n"
            f"Instructions:\n"
            f"1. Synthesize a comprehensive, professional summary in JARVIS's elegant tone.\n"
            f"2. Cite your sources clearly by referencing [Source X].\n"
            f"3. Highlight key advancements, risks, or conclusions.\n"
            f"4. Keep the final response under 500 words but dense with information."
        )

        print("ResearchAgent: Synthesizing final report...")
        report = self.ollama.generate_research_report(prompt)
        return report
