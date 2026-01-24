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
        
        # Helper to clean slots
        def clean_slot(text):
            return re.sub(r'^(my|the|a|an)\s+', '', text, flags=re.IGNORECASE).strip()

        # High-precision regex rules
        # (Pattern, IntentType, Slots Extraction Logic)
        self.rules = [
            (r"(open|launch|start|run) (.+)", IntentType.SYSTEM_OPEN_APP, lambda m: {"app_name": clean_slot(m.group(2))}),
            (r"(close|quit|exit|kill) (.+)", IntentType.SYSTEM_CLOSE_APP, lambda m: {"app_name": clean_slot(m.group(2))}),
            (r"(delete|remove|erase) (.+)", IntentType.FILE_DELETE, lambda m: {"file_name": clean_slot(m.group(2))}),
            (r"(search for|find) (.+) in browser", IntentType.BROWSER_SEARCH, lambda m: {"query": clean_slot(m.group(2))}),
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
            match = re.match(pattern, text_lower)
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
            "- TASK_MANAGEMENT, KNOWLEDGE_QUERY, CONVERSATION, CLARIFICATION_REQUIRED\n"
            "\n"
            "Response Format:\n"
            "{\n"
            "  \"intent\": \"INTENT_NAME\",\n"
            "  \"confidence\": 0.0-1.0,\n"
            "  \"slots\": { \"content\": \"...\", \"query\": \"...\", \"app_name\": \"...\", \"command\": \"...\" },\n"
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
