import re

class QueryClassifier:
    """Classifies user queries to determine routing."""
    
    # SYSTEM: Control hardware/OS
    # ACTION: Open apps/websites
    # PERSONAL: Memory/Who am I
    # WEB: Search/News
    # CHAT: Small talk/Greeting
    
    TYPES = ["SYSTEM_COMMAND", "ACTION_REQUEST", "PERSONAL_QUERY", "WEB_ONLY_QUERY", "CHAT"]
    
    def classify(self, text: str) -> str:
        text = text.lower().strip()

        # 1. SPECIAL CASE CHECK: Vision context or identity
        if any(x in text for x in ["who is me", "who is i", "who is in front"]):
             return "ACTION_REQUEST"
        
        if any(x in text for x in ["identify yourself", "who are you", "who are u", "identify you"]):
             return "PERSONAL_QUERY"

        # 2. SYSTEM COMMANDS (Hardware/OS/Status)
        sys_triggers = ["volume", "brightness", "battery", "cpu", "ram", "screenshot", "record screen", "lock", "shutdown", "sleep", "restart", "time", "date", "briefing", "report", "summary"]
        if any(word in text for word in sys_triggers):
            return "SYSTEM_COMMAND"

        # 3. ACTION REQUESTS (Open things/Eyes)
        action_triggers = ["open", "close", "launch", "start", "eyes", "camera", "website", "youtube", "chrome", "google", "read", "describe", "look", "see", "holding", "hand", "analyse", "analyze", "recognise", "recognize", "detect", "scan", "check", "identify"]
        if any(word in text for word in action_triggers):
            return "ACTION_REQUEST"

        # 4. PERSONAL QUERIES
        personal_triggers = ["who am i", "who i am", "who are you", "my name", "my identity", "remember", "forget", "memorize", "memorise", "save this"]
        if any(word in text for word in personal_triggers):
            return "PERSONAL_QUERY"

        # 5. WEB QUERIES (Deep information/Real-time)
        web_triggers = ["news", "weather", "research", "deep dive", "search the web", "look up", "internet", "google", "stock", "price of"]
        if any(word in text for word in web_triggers):
            return "WEB_ONLY_QUERY"

        # 6. DEFAULT TO CHAT (Handled by Local LLM reasoning in local_brain.py)
        return "CHAT"
