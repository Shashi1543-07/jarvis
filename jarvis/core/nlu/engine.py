import json
import re
from typing import Optional, Dict, Any, List
from .intents import Intent, IntentType

class NLUEngine:
    """
    Hybrid NLU Engine:
    1. Regular Expressions (Fast, High Precision)
    2. Local LLM (Analysis, Slots, Fallback)
    """
    
    def __init__(self, llm_brain=None):
        self.llm = llm_brain
        
        # Helper to clean slots and normalize app names
        def clean_slot(text):
            # Remove common prefixes
            text = re.sub(r'^(my|the|a|an)\s+', '', text, flags=re.IGNORECASE).strip()
            # Remove trailing punctuation and filler words
            text = re.sub(r'[\.\,\!\?]+$', '', text).strip()
            text = re.sub(r'\s+(please|now|then|for me)$', '', text, flags=re.IGNORECASE).strip()
            return text
        
        # App name aliases for common Windows applications
        self.app_aliases = {
            # Browsers
            "edge": "msedge", "microsoft edge": "msedge", "ms edge": "msedge",
            "chrome": "chrome", "google chrome": "chrome",
            "firefox": "firefox", "mozilla firefox": "firefox",
            "brave": "brave",
            # Microsoft Office
            "word": "WINWORD", "microsoft word": "WINWORD",
            "excel": "excel", "microsoft excel": "excel",
            "powerpoint": "powerpnt", "ppt": "powerpnt",
            "outlook": "outlook", "microsoft outlook": "outlook",
            "notepad": "notepad",
            # Development
            "vscode": "Code", "visual studio code": "Code", "vs code": "Code",
            "code": "Code",
            # Media
            "spotify": "Spotify",
            "vlc": "vlc",
            # System
            "explorer": "explorer", "file explorer": "explorer", "files": "explorer",
            "settings": "SystemSettings",
            "calculator": "calc", "calc": "calc",
            "terminal": "wt", "windows terminal": "wt",
            "cmd": "cmd", "command prompt": "cmd",
            "powershell": "powershell",
            # Games/Common
            "discord": "Discord",
            "slack": "slack",
            "teams": "Teams", "microsoft teams": "Teams",
            "zoom": "Zoom",
        }
        
        # Helper to normalize app names using aliases
        app_aliases = self.app_aliases  # Local reference for closure
        def normalize_app_name(text):
            text = clean_slot(text).lower()
            # Check direct match in aliases
            if text in app_aliases:
                return app_aliases[text]
            # Try partial match
            for alias, real_name in app_aliases.items():
                if alias in text or text in alias:
                    return real_name
            # Return cleaned original
            return clean_slot(text)

        # High-precision regex rules
        # (Pattern, IntentType, Slots Extraction Logic)
        self.rules = [
            # ═══════════════════════════════════════════════════════════
            # SYSTEM CONTROL (Volume, Brightness, etc.)
            # ═══════════════════════════════════════════════════════════
            (r"(?:set|change|adjust)?\s*(?:the)?\s*volume\s*(?:to|at)?\s*(\d+)(?:%|percent)?", IntentType.SYSTEM_CONTROL, lambda m: {"command": f"volume {m.group(1)}"}),
            (r"(increase|raise|turn up|up)\s+(?:the)?\s*volume(?:\s+(?:by|to))?\s*(\d+)?(?:%|percent)?", IntentType.SYSTEM_CONTROL, lambda m: {"command": f"volume up {m.group(2) or '10'}"}),
            (r"(decrease|lower|turn down|down)\s+(?:the)?\s*volume(?:\s+(?:by|to))?\s*(\d+)?(?:%|percent)?", IntentType.SYSTEM_CONTROL, lambda m: {"command": f"volume down {m.group(2) or '10'}"}),
            (r"(mute|unmute|silence)(?:\s+(?:the)?\s*(?:volume|sound|audio))?", IntentType.SYSTEM_CONTROL, lambda m: {"command": m.group(1)}),
            (r"(?:set|change|adjust)?\s*(?:the)?\s*brightness\s*(?:to|at)?\s*(\d+)(?:%|percent)?", IntentType.SYSTEM_CONTROL, lambda m: {"command": f"brightness {m.group(1)}"}),
            (r"(increase|raise|turn up)\s+(?:the)?\s*brightness(?:\s+(?:by|to))?\s*(\d+)?(?:%|percent)?", IntentType.SYSTEM_CONTROL, lambda m: {"command": f"brightness up {m.group(2) or '10'}"}),
            (r"(decrease|lower|turn down|dim)\s+(?:the)?\s*brightness(?:\s+(?:by|to))?\s*(\d+)?(?:%|percent)?", IntentType.SYSTEM_CONTROL, lambda m: {"command": f"brightness down {m.group(2) or '10'}"}),
            (r"(shutdown|shut down|restart|reboot|sleep|lock)(?:\s+(?:the)?\s*(?:system|computer|pc))?", IntentType.SYSTEM_CONTROL, lambda m: {"command": m.group(1).replace(" ", "")}),
            (r"(?:what(?:'s| is)?\s+(?:the)?)?\s*(?:current)?\s*(?:battery|power)\s*(?:level|status|percent(?:age)?)?", IntentType.SYSTEM_CONTROL, lambda m: {"command": "battery"}),
            (r"(?:take\s+a?)?\s*screenshot", IntentType.SYSTEM_CONTROL, lambda m: {"command": "screenshot"}),
            
            # ═══════════════════════════════════════════════════════════
            # CONNECTIVITY - WiFi, Bluetooth, Hotspot
            # More flexible patterns to handle speech variations and Whisper mishearing
            # ═══════════════════════════════════════════════════════════
            
            # WiFi patterns - connect/enable/turn on (handles "system wifi", "my wifi", "the wifi")
            (r"(?:turn\s+on|enable|connect(?:\s+to)?|activate)\s+(?:the\s+|my\s+|system\s+)?(?:wi-?fi|wifi|wireless|internet)", IntentType.SYSTEM_WIFI_CONNECT, lambda m: {}),
            (r"(?:wi-?fi|wifi|wireless)\s+(?:on|connect|enable)", IntentType.SYSTEM_WIFI_CONNECT, lambda m: {}),
            # WiFi patterns - disconnect/disable/turn off (including typo "turn of")
            (r"(?:turn\s+of{1,2}|disable|disconnect)\s+(?:the\s+|my\s+|system\s+)?(?:wi-?fi|wifi|wireless|internet)", IntentType.SYSTEM_WIFI_DISCONNECT, lambda m: {}),
            (r"(?:wi-?fi|wifi|wireless)\s+(?:off|disconnect|disable)", IntentType.SYSTEM_WIFI_DISCONNECT, lambda m: {}),
            
            # Bluetooth patterns (handles variations)
            (r"(?:turn\s+on|enable|activate|connect)\s+(?:the\s+|my\s+)?bluetooth", IntentType.SYSTEM_BLUETOOTH, lambda m: {"state": "on"}),
            (r"bluetooth\s+(?:on|enable|connect)", IntentType.SYSTEM_BLUETOOTH, lambda m: {"state": "on"}),
            (r"(?:turn\s+of{1,2}|disable|disconnect)\s+(?:the\s+|my\s+)?bluetooth", IntentType.SYSTEM_BLUETOOTH, lambda m: {"state": "off"}),
            (r"bluetooth\s+(?:off|disable|disconnect)", IntentType.SYSTEM_BLUETOOTH, lambda m: {"state": "off"}),
            
            # Hotspot patterns - including Whisper mishearing "hard spot" for "hotspot"
            (r"(?:turn\s+on|enable|start|activate|create)\s+(?:the\s+|my\s+|mobile\s+)?(?:hot\s*spot|hard\s*spot|hotspot)", IntentType.SYSTEM_HOTSPOT, lambda m: {"state": "on"}),
            (r"(?:hot\s*spot|hotspot)\s+(?:on|enable|start)", IntentType.SYSTEM_HOTSPOT, lambda m: {"state": "on"}),
            (r"(?:turn\s+of{1,2}|disable|stop)\s+(?:the\s+|my\s+|mobile\s+)?(?:hot\s*spot|hard\s*spot|hotspot)", IntentType.SYSTEM_HOTSPOT, lambda m: {"state": "off"}),
            (r"(?:hot\s*spot|hotspot)\s+(?:off|disable|stop)", IntentType.SYSTEM_HOTSPOT, lambda m: {"state": "off"}),
            
            # Recycle bin
            (r"(?:empty|clear|clean)\s+(?:the\s+)?(?:recycle\s*bin|trash|dustbin)", IntentType.SYSTEM_RECYCLE_BIN, lambda m: {}),
            


            # ═══════════════════════════════════════════════════════════
            # APPLICATION CONTROL  
            # ═══════════════════════════════════════════════════════════
            (r"(open|launch|start|run)\s+(.+)", IntentType.SYSTEM_OPEN_APP, lambda m: {"app_name": normalize_app_name(m.group(2))}),
            (r"(close|quit|exit|kill)\s+(.+)", IntentType.SYSTEM_CLOSE_APP, lambda m: {"app_name": normalize_app_name(m.group(2))}),
            
            # ═══════════════════════════════════════════════════════════
            # FILE OPERATIONS
            # ═══════════════════════════════════════════════════════════
            (r"(delete|remove|erase)\s+(.+)", IntentType.FILE_DELETE, lambda m: {"file_name": clean_slot(m.group(2))}),
            (r"(search for|find|look for)\s+(.+?)\s+(?:in|on)\s+(?:the\s+)?browser", IntentType.BROWSER_SEARCH, lambda m: {"query": clean_slot(m.group(2))}),
            (r"(?:google|search|search for|look up)\s+(.+)", IntentType.BROWSER_SEARCH, lambda m: {"query": clean_slot(m.group(1))}),
            
            # ═══════════════════════════════════════════════════════════
            # MEMORY OPERATIONS
            # ═══════════════════════════════════════════════════════════
            # MEMORY_WRITE - remembering things
            # Pattern for "my X is Y" style (captures the whole statement)
            (r"(?:my\s+)?(?:father|mother|dad|mom|brother|sister|friend|girlfriend|boyfriend|wife|husband)(?:'s\s+name)?\s+is\s+(.+?)(?:,?\s*(?:kindly\s+)?(?:memorize|remember|note).*)?$", IntentType.MEMORY_WRITE, lambda m: {"content": m.group(0).split(",")[0].strip()}),
            (r"(?:my\s+)?birthday\s+is\s+(.+?)(?:,?\s*(?:kindly\s+)?(?:memorize|remember|note).*)?$", IntentType.MEMORY_WRITE, lambda m: {"content": m.group(0).split(",")[0].strip()}),
            # Standard patterns - "remember that X"
            (r"(?:remember|memorize|note|save|store|keep in mind)\s+that\s+(.+)", IntentType.MEMORY_WRITE, lambda m: {"content": m.group(1)}),
            (r"(?:remember|memorize|note|save|store)\s+(?!it\b|this\b|that\b)(.+)", IntentType.MEMORY_WRITE, lambda m: {"content": m.group(1)}),
            (r"(?:i want you to|please)\s+(?:remember|memorize)\s+(?:that\s+)?(.+)", IntentType.MEMORY_WRITE, lambda m: {"content": m.group(1)}),
            # "X, kindly memorize it" - capture full sentence by flagging for full text extraction
            (r"(.+?),?\s*(?:kindly\s+)?(?:memorize|remember)\s+(?:it|this|that)\.?$", IntentType.MEMORY_WRITE, lambda m: {"content": m.group(1), "use_full": True}),

            
            # MEMORY_READ - recalling things
            (r"(?:what|do you)\s+(?:do you\s+)?(?:know|remember)\s+(?:about\s+)?(.+)", IntentType.MEMORY_READ, lambda m: {"query": m.group(1)}),
            (r"(?:recall|retrieve|tell me about|what about)\s+(.+)", IntentType.MEMORY_READ, lambda m: {"query": m.group(1)}),
            (r"what(?:'s| is)\s+my\s+(.+)", IntentType.MEMORY_READ, lambda m: {"query": f"my {m.group(1)}"}),
            (r"(?:what did i|did i)\s+(?:tell|say)\s+(?:you\s+)?(?:about\s+)?(.+)", IntentType.MEMORY_READ, lambda m: {"query": m.group(1)}),
            # Relationship queries - "who is my father/mother/friend"
            (r"who\s+(?:is|are)\s+(?:my\s+)?(.+)", IntentType.MEMORY_READ, lambda m: {"query": f"relationship {m.group(1)}"}),
            (r"(?:do you know|can you tell me)\s+(?:who\s+)?(?:is\s+)?my\s+(.+)", IntentType.MEMORY_READ, lambda m: {"query": f"relationship {m.group(1)}"}),
            # Event queries - "when is my birthday"
            (r"when\s+(?:is|was)\s+(?:my\s+)?(.+)", IntentType.MEMORY_READ, lambda m: {"query": f"event {m.group(1)}"}),
            
            # MEMORY_FORGET - forgetting things
            (r"(?:forget|erase|delete)\s+(?:about\s+)?(?:the\s+)?(?:memory|fact|info)?(?:\s+(?:about|of))?\s*(.+)?", IntentType.MEMORY_FORGET, lambda m: {"content": m.group(1) or ""}),
            (r"(?:don't|do not)\s+remember\s+(?:that|about)?\s*(.+)?", IntentType.MEMORY_FORGET, lambda m: {"content": m.group(1) or ""}),


            
            # ═══════════════════════════════════════════════════════════
            # VISION & SCREEN (Order matters! Screen patterns first)
            # ═══════════════════════════════════════════════════════════
            # SCREEN patterns (most specific - must come first)
            (r"(?:read|ocr|display)(?:\s+(?:the|what's|what is|whats|text|on)){0,3}\s+screen", IntentType.SCREEN_OCR, lambda m: {}),
            (r"(?:describe|analyze|what's|whats|what is)(?:\s+(?:on|the|what is on|what's on)){0,4}\s+screen", IntentType.SCREEN_DESCRIBE, lambda m: {}),
            
            # QR Code scanning
            (r"(?:scan|read)(?:\s+(?:a|the|this)){0,2}\s+(?:qr|barcode|qr code)", IntentType.VISION_QR, lambda m: {}),

            # Gesture control
            (r"(?:enable|start|turn on)(?:\s+(?:the|hand)){0,2}\s+(?:gesture|gestures|hand control)", IntentType.VISION_GESTURE, lambda m: {}),

            # Emotion detection
            (r"(?:what(?:'s| is)|detect|read|analyze)(?:\s+(?:my|the|his|her)){0,2}\s+(?:emotion|mood|feeling|expression)", IntentType.VISION_EMOTION, lambda m: {}),

            # Posture check
            (r"(?:check|monitor|analyze)(?:\s+(?:my|the)){0,2}\s+(?:posture|sitting|stance)", IntentType.VISION_POSTURE, lambda m: {}),

            # Video recording
            (r"(?:record|start recording|capture)(?:\s+(?:a|the)){0,2}\s+(?:video|footage)(?:\s+for\s+(\d+)\s*(?:seconds?|s))?", IntentType.VISION_RECORD, lambda m: {"duration": m.group(1) or "10"}),

            # Deep scan (explicit)
            (r"(?:deep|full|complete)(?:\s+(?:vision|camera)){0,2}\s+(?:scan|analysis|mode)", IntentType.VISION_DEEP_SCAN, lambda m: {}),

            # Screen Analysis (High priority before generic OCR)
            (r"(?:read|ocr|extract)(?:\s+(?:the|this|my)){0,2}\s+screen", IntentType.SCREEN_OCR, lambda m: {}),
            (r"(?:analyze|describe|examine)(?:\s+(?:the|this|my)){0,2}\s+screen", IntentType.SCREEN_DESCRIBE, lambda m: {}),

            # VISION OCR patterns (more general - after screen)
            (r"(?:read|ocr)(?:\s+(?:the|what's|what is|whats|text|written|on|in|from|at|the)){0,4}\s+(.+)", IntentType.VISION_OCR, lambda m: {"prompt": f"Read {m.group(1)}"}),
            (r"(?:look|see|read|ocr)\s+(?:at|what's|what is|whats|the|this){0,3}\s+(.+)", IntentType.VISION_OCR, lambda m: {"prompt": f"Look at {m.group(1)}"}),
            # Vision describe/detect/people
            (r"(?:describe|what do|what's|whats|what is|analyze)(?:\s+(?:you|the|visible|in front|of|me|this)){0,5}\s+(?:see|visible|happening|in front|at|scene|around)", IntentType.VISION_DESCRIBE, lambda m: {}),
            (r"(?:detect|find|what|list)(?:\s+(?:all|the|some|visible|any)){0,3}\s+(?:objects|things|items)(?:\s+(?:there|in front|visible|of me|here)){0,4}", IntentType.VISION_OBJECTS, lambda m: {}),
            (r"(?:who|identify|recognize)(?:\s+(?:is |are |this |the )){0,3}(?:people|person|one|individual|he|she|they|that|this)(?:\s+(?:there|in front|visible|here)){0,4}", IntentType.VISION_PEOPLE, lambda m: {}),
            (r"(?:repair|fix|reset|restart)(?:\s+(?:the|your|my)){0,2}\s+(?:vision|eyes|ocr|camera|sight)", IntentType.VISION_REPAIR, lambda m: {}),
            (r"(?:i am|my name is|remember me as|this is)\s+(.+)", IntentType.VISION_LEARN_FACE, lambda m: {"name": clean_slot(m.group(1))}),
            (r"(?:close|stop|shut|turn off|disable)(?:\s+(?:the|your)){0,2}\s+(?:camera|vision|eyes|sight|looking)", IntentType.VISION_CLOSE, lambda m: {}),
            (r"(?:analyze|describe|understand|tell me about)(?:\s+(?:the|this)){0,2}\s+(?:scene|environment|room|context)", IntentType.ADVANCED_SCENE_ANALYSIS, lambda m: {}),
            (r"(?:scan|read)(?:\s+(?:this|the|a)){0,2}\s+(?:document|paper|page|sheet)", IntentType.VISION_DOCUMENT, lambda m: {}),
            (r"(?:what|how)(?:\s+am|is)?\s+i\s+(?:doing|looking|sitting|standing)", IntentType.VISION_ACTIVITY, lambda m: {}),
            (r"(?:track|follow|focus\s+on)(?:\s+(?:the|this|that|a)){0,2}\s+(.+)", IntentType.VISION_TRACK, lambda m: {"object_name": clean_slot(m.group(1))}),
            # (r"(?:highlight|point\s+out)(?:\s+(?:the|this|that|a)){0,2}\s+(.+)", IntentType.VISION_HIGHLIGHT, lambda m: {"object_name": clean_slot(m.group(1))}),
            
            # ═══════════════════════════════════════════════════════════
            # WEB INTELLIGENCE
            # ═══════════════════════════════════════════════════════════
            (r"(?:what's|whats|what is|get|tell me)(?:\s+(?:the|latest)){0,2}\s+(?:news|headlines)", IntentType.WEB_NEWS, lambda m: {}),
            (r"(?:what's|whats|what is|check)(?:\s+(?:the|today's)){0,2}\s+weather", IntentType.WEB_WEATHER, lambda m: {}),
            (r"(?:deep\s+research|research|deep\s+dive|analyze|summary|summarize)(?:\s+on)?\s+(.+)", IntentType.WEB_RESEARCH, lambda m: {"topic": m.group(1)}),

            # ═══════════════════════════════════════════════════════════
            # MEDIA CONTROL (Previously Missing)
            # ═══════════════════════════════════════════════════════════
            (r"(?:play|resume)(?:\s+(?:the|my|some)){0,2}\s*(?:music|song|audio|track|playback)?", IntentType.MEDIA_CONTROL, lambda m: {"command": "play"}),
            (r"(?:pause|stop)(?:\s+(?:the|my)){0,2}\s*(?:music|song|audio|track|playback)?", IntentType.MEDIA_CONTROL, lambda m: {"command": m.group(0).split()[0]}),
            (r"(?:next|skip)(?:\s+(?:this|the)){0,2}\s*(?:track|song)?", IntentType.MEDIA_CONTROL, lambda m: {"command": "next"}),
            (r"(?:previous|prev|go\s+back)(?:\s+(?:to|the)){0,2}\s*(?:track|song)?", IntentType.MEDIA_CONTROL, lambda m: {"command": "previous"}),

            # ═══════════════════════════════════════════════════════════
            # TASK MANAGEMENT & PRODUCTIVITY
            # ═══════════════════════════════════════════════════════════
            (r"(?:set|start|create)(?:\s+a)?\s+timer(?:\s+for)?\s+(.+)", IntentType.TASK_TIMER, lambda m: {"duration": m.group(1)}),
            (r"(?:remind|set\s+a\s+reminder)(?:\s+me)?(?:\s+to)?\s+(.+)", IntentType.TASK_REMINDER, lambda m: {"task": m.group(1)}),
            
            # TODO List
            (r"(?:add|put)(?:\s+(?:to|on)){0,2}(?:\s+(?:my|the)){0,2}\s+(?:todo|to-do|tasks)(?:\s+list)?\s+(.+)", IntentType.TODO_ADD, lambda m: {"item": m.group(1)}),
            (r"(?:what's|whats|what is|show|list)(?:\s+(?:on|my|the)){0,2}\s+(?:todo|to-do|tasks)(?:\s+list)?", IntentType.TODO_LIST, lambda m: {}),
            (r"(?:remove|delete|check\s+off)(?:\s+(?:from|on)){0,2}(?:\s+(?:my|the)){0,2}\s+(?:todo|to-do|tasks)(?:\s+list)?\s+(.+)", IntentType.TODO_DELETE, lambda m: {"item": m.group(1)}),
            
            # Document & Code Analysis
            (r"(?:summarize|summary)(?:\s+(?:the|this))?\s+(?:document|file|pdf)\s+(?:at|path)?\s*(.+)", IntentType.DOC_SUMMARIZE, lambda m: {"file_path": m.group(1).strip()}),
            (r"(?:ask|question)(?:\s+(?:about|the|this|on))?\s+(?:document|file|pdf)\s*(.+)", IntentType.DOC_ASK, lambda m: {"query": m.group(1).strip()}),
            (r"(?:explain|how\s+does|what\s+does)(?:\s+(?:the|this|that))?\s+code\s+(?:in|at)?\s*(.+)", IntentType.CODE_EXPLAIN, lambda m: {"file_path": m.group(1).strip()}),
            (r"(?:analyze|scan|check)(?:\s+(?:the|this|that))?\s+project\s+(?:at|path)?\s*(.+)", IntentType.PROJECT_ANALYZE, lambda m: {"root_path": m.group(1).strip()}),

            # ═══════════════════════════════════════════════════════════
            # CONNECTIVITY & SYSTEM EXTRAS
            # ═══════════════════════════════════════════════════════════
            (r"(?:empty|clear)(?:\s+(?:the|my)){0,2}\s+recycle\s+bin", IntentType.SYSTEM_RECYCLE_BIN, lambda m: {}),
            (r"(?:connect|join)(?:\s+to)?\s+wifi\s+(.+)", IntentType.SYSTEM_WIFI_CONNECT, lambda m: {"ssid": m.group(1)}),
            (r"(?:disconnect|off|turn\s+off)\s+wifi", IntentType.SYSTEM_WIFI_DISCONNECT, lambda m: {}),
            (r"(?:turn\s+)?(?:on|off|enable|disable)\s+bluetooth", IntentType.SYSTEM_BLUETOOTH, lambda m: {"state": "on" if "on" in m.group(0) or "enable" in m.group(0) else "off"}),
            (r"(?:turn\s+)?(?:on|off|enable|disable)\s+hotspot", IntentType.SYSTEM_HOTSPOT, lambda m: {"state": "on" if "on" in m.group(0) or "enable" in m.group(0) else "off"}),
        ]

    def parse(self, text: str, context: Optional[str] = None) -> Intent:
        text = text.strip()
        
        # 1. Rule-based First Pass
        rule_intent = self._check_rules(text)
        if rule_intent:
            return rule_intent
            
        # 2. LLM Fallback
        if self.llm:
            return self._query_llm(text, context)

        # 3. Ultimate Fallback
        return Intent(
            intent_type=IntentType.UNKNOWN,
            confidence=0.0,
            original_text=text
        )

    def _check_rules(self, text: str) -> Optional[Intent]:
        text_lower = text.lower()
        for pattern, intent_type, slot_extractor in self.rules:
            # Use search instead of match to handle prefixes like "can you", "jarvis", "please"
            match = re.search(pattern, text_lower)
            if match:
                slots = slot_extractor(match)
                
                # Default dangerous check
                requires_conf = False
                if intent_type in [IntentType.FILE_DELETE]:
                    requires_conf = True
                
                return Intent(
                    intent_type=intent_type,
                    confidence=1.0,
                    slots=slots,
                    requires_confirmation=requires_conf,
                    original_text=text
                )
        return None

    def _query_llm(self, text: str, context: Optional[str]) -> Intent:
        system_prompt = (
            "You are the NLU engine for JARVIS. Classify queries into structured JSON intents.\n"
            "Return ONLY JSON.\n"
            "\n"
            "Intents:\n"
            "- SYSTEM_CONTROL: volume, brightness, wifi, shutdown, restart, sleep.\n"
            "   - Slot: 'command' (The action and any parameters, e.g. 'restart', 'shutdown', 'increase brightness to 100%')\n"
            "- SYSTEM_OPEN_APP, SYSTEM_CLOSE_APP\n"
            "   - Slot: 'app_name'\n"
            "- FILE_OPERATION (delete, search, create)\n"
            "   - Slot: 'file_name'\n"
            "- MEMORY_WRITE: User explicitly asks to remember something (e.g. 'Remember I like blue').\n"
            "   - Slot: 'content' (the fact to remember)\n"
            "- MEMORY_READ: User asks what is remembered (e.g. 'What is my favorite color?').\n"
            "   - Slot: 'query' (what to look for)\n"
            "- MEMORY_FORGET: User asks to forget something.\n"
            "   - Slot: 'content' (what to forget)\n"
            "- VISION_OCR: Read text from camera/eyes. Use for queries like 'read what you see', 'what does it say', 'read this'.\n"
            "   - Slot: 'prompt' (Description of WHAT to read if specified, e.g. 'the title', or keep empty for 'read all')\n"
            "- VISION_DESCRIBE: Describe scene or visual context. Use for 'what do you see', 'describe this', 'tell me about this scene', 'can you see?'.\n"
            "- VISION_OBJECTS: List or count specific objects. Use for 'what objects are there', 'identify things', 'is there a book?'.\n"
            "- VISION_PEOPLE: Identify people in view. Use for 'who are you looking at', 'who is this'.\n"
            "- VISION_CLOSE: Stop the vision system and close camera window. Use for 'close eyes', 'stop camera'.\n"
            "- ADVANCED_SCENE_ANALYSIS: Deep context understanding. Use for 'where am I', 'analyze this scene', 'describe environment'.\n"
            "- TASK_MANAGEMENT, KNOWLEDGE_QUERY, CONVERSATION, CLARIFICATION_REQUIRED\n"
            "\n"
            "- VISION_OCR, VISION_DESCRIBE, VISION_OBJECTS, VISION_PEOPLE, SCREEN_OCR, SCREEN_DESCRIBE\n"
            "   - Slot: 'prompt' (Describe what you want me to do or look for, e.g. 'the book', 'the man', 'the error')\n"
            "\n"
            "Response Format:\n"
            "{\n"
            "  \"intent\": \"INTENT_NAME\",\n"
            "  \"confidence\": 0.0-1.0,\n"
            "  \"slots\": { \"prompt\": \"...\", \"app_name\": \"...\", \"command\": \"...\", \"content\": \"...\", \"query\": \"...\" },\n"
            "  \"requires_confirmation\": boolean,\n"
            "  \"clarification_question\": \"string or null\"\n"
            "}\n"
            "\n"
            "Rules:\n"
            "1. Dangerous commands (delete file, shutdown) -> requires_confirmation=true.\n"
            "2. Unclear intent -> CLARIFICATION_REQUIRED.\n"
            "3. Capture all parameters: Ensure values like percentages (100%), units, or specific details are included in the slots (e.g. 'increase volume to 50' in 'command' slot).\n"
            "4. Memory: Extract the *core info* into 'content' or 'query'. Strip 'remember that' or 'what is'."
        )

        try:
            # Call Ollama
            response_text = self.llm.generate_response(prompt=f"User Input: {text}", system=system_prompt)
            
            # Clean possible markdown code blocks
            clean_text = response_text.replace("```json", "").replace("```", "").strip()
            
            data = json.loads(clean_text)
            
            intent_str = data.get("intent", "UNKNOWN")
            confidence = data.get("confidence", 0.0)
            slots = data.get("slots", {})
            req_conf = data.get("requires_confirmation", False)
            clarification = data.get("clarification_question")
            
            # Map string to Enum
            try:
                intent_type = IntentType[intent_str]
            except KeyError:
                # Fallback mapping or default
                if "OPEN" in intent_str: intent_type = IntentType.SYSTEM_OPEN_APP
                elif "CLOSE" in intent_str: intent_type = IntentType.SYSTEM_CLOSE_APP
                elif "SEARCH" in intent_str: intent_type = IntentType.BROWSER_SEARCH
                elif "FILE" in intent_str: intent_type = IntentType.FILE_OPERATION
                elif "REMIND" in intent_str or "ALARM" in intent_str: intent_type = IntentType.TASK_MANAGEMENT
                else: intent_type = IntentType.CONVERSATION # Default safe fallback

            return Intent(
                intent_type=intent_type,
                confidence=confidence,
                slots=slots,
                requires_confirmation=req_conf,
                original_text=text,
                clarification_question=clarification
            )

        except json.JSONDecodeError:
            print(f"NLU Parsing Error: Could not parse JSON from LLM: {response_text}")
            return Intent(intent_type=IntentType.CONVERSATION, confidence=0.5, slots={}, original_text=text)
        except Exception as e:
            print(f"NLU Error: {e}")
            return Intent(intent_type=IntentType.UNKNOWN, confidence=0.0, slots={}, original_text=text)
