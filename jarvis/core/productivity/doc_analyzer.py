import fitz  # PyMuPDF
from docx import Document
import os

class DocAnalyzer:
    def __init__(self, ollama_brain):
        self.ollama = ollama_brain
        print("DocAnalyzer: Initialized.")

    def extract_text(self, file_path):
        """Extracts text from PDF or DOCX files."""
        if not os.path.exists(file_path):
            return None
        
        ext = os.path.splitext(file_path)[1].lower()
        text = ""

        try:
            if ext == '.pdf':
                doc = fitz.open(file_path)
                for page in doc:
                    text += page.get_text()
            elif ext == '.docx':
                doc = Document(file_path)
                text = "\n".join([p.text for p in doc.paragraphs])
            else:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
            return text
        except Exception as e:
            print(f"DocAnalyzer Error: {e}")
            return None

    def summarize_document(self, file_path):
        """Generates a summary of the document."""
        text = self.extract_text(file_path)
        if not text:
            return "Sir, I'm unable to read that document."

        # Cap text for LLM context (approx 5k chars for now)
        truncated_text = text[:5000]
        
        prompt = (
            f"You are JARVIS. I need a concise summary of this document: {os.path.basename(file_path)}\n\n"
            f"Content:\n{truncated_text}\n\n"
            f"Instructions:\n"
            f"1. Summarize the main points in 3-5 bullet points.\n"
            f"2. Note any critical actions or dates if found.\n"
            f"3. Use a professional, JARVIS-like tone."
        )

        return self.ollama.generate_response(prompt)

    def ask_about_document(self, file_path, question):
        """Answers a specific question about the document's content."""
        text = self.extract_text(file_path)
        if not text:
            return "Sir, I'm unable to access that document's data."

        truncated_text = text[:8000]
        
        prompt = (
            f"Based on the following document content, please answer the question: '{question}'\n\n"
            f"Document Content:\n{truncated_text}\n\n"
            f"Answer concisely and citationally if possible."
        )

        return self.ollama.generate_response(prompt)
