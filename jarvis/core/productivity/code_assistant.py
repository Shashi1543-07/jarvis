import os
import subprocess

class CodeAssistant:
    def __init__(self, ollama_brain):
        self.ollama = ollama_brain
        print("CodeAssistant: Initialized.")

    def explain_code(self, file_path, function_name=None):
        """Provides an explanation of a file or a specific function."""
        if not os.path.exists(file_path):
            return "Sir, I cannot find the source file in question."

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # Simple substring search for function focus if requested
            if function_name:
                start = code.find(f"def {function_name}")
                if start == -1: start = code.find(f"class {function_name}")
                if start != -1:
                    # Capture approx 100 lines/3000 chars from start
                    code = code[start:start+3000]

            prompt = (
                f"You are JARVIS, an expert software engineer. Explain the following code from '{os.path.basename(file_path)}':\n\n"
                f"```python\n{code[:4000]}\n```\n\n"
                f"Instructions:\n"
                f"1. Explain what this code does concisely.\n"
                f"2. Identify any potential bugs or architectural weaknesses.\n"
                f"3. Maintain your signature elegant tone."
            )

            return self.ollama.generate_response(prompt)
        except Exception as e:
            return f"CodeAssistant Error: {e}"

    def run_tests(self, project_root):
        """Runs pytest or similar in the project root."""
        print(f"CodeAssistant: Running tests in {project_root}...")
        try:
            # Check for common test runners
            if os.path.exists(os.path.join(project_root, "pytest.ini")) or os.path.exists(os.path.join(project_root, "tests")):
                result = subprocess.run([".venv\\Scripts\\python", "-m", "pytest"], capture_output=True, text=True, cwd=project_root)
                return f"Test Results:\n{result.stdout[-1000:]}\n\nErrors (if any):\n{result.stderr}"
            return "Sir, I couldn't find a standard test suite configuration in that directory."
        except Exception as e:
            return f"Test Execution Error: {e}"

    def analyze_project_structure(self, root_path):
        """Lists the directory tree for context."""
        tree = []
        for root, dirs, files in os.walk(root_path):
            level = root.replace(root_path, '').count(os.sep)
            indent = ' ' * 4 * level
            tree.append(f"{indent}{os.path.basename(root)}/")
            sub_indent = ' ' * 4 * (level + 1)
            for f in files[:10]: # Limit files per dir for brevity
                tree.append(f"{sub_indent}{f}")
        
        context = "\n".join(tree[:50]) # Limit total lines
        prompt = f"Analyze this project structure and summarize its architecture:\n\n{context}"
        return self.ollama.generate_response(prompt)
