import json
import os
import random

class NLU:
    def __init__(self):
        self.intents = []
        self.load_intents()

    def load_intents(self):
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'intents.json')
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                self.intents = data.get('intents', [])
            print("NLU: Intents loaded.")
        except Exception as e:
            print(f"NLU: Failed to load intents: {e}")

    def predict_intent(self, text):
        text = text.lower()
        for intent in self.intents:
            for pattern in intent['patterns']:
                if pattern in text:
                    return intent
        return None
