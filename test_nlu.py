"""Quick test for NLU app name normalization"""
import sys
sys.path.insert(0, 'jarvis')

from core.nlu.engine import NLUEngine

e = NLUEngine()

tests = [
    'close Microsoft Edge',
    'close edge', 
    'open chrome',
    'close notepad',
    'open vscode',
    'kill discord',
    'scan this qr code',
    'enable gesture control',
    'what is my mood',
    'check my posture',
    'record a video for 5 seconds',
    'deep scan the scene',
    'set a timer for 5 minutes',
    'remind me to buy milk',
    'scan this document',
    'what am i doing',
    'track the bottle',
    'what is the latest news',
    'check today\'s weather',
    'deep research on quantum computing',
    'add buy groceries to my todo list',
    'show my tasks',
    'remove buy milk from my todo list',
    'summarize the document at C:/docs/report.pdf',
    'explain this code in main.py',
    'empty the recycle bin',
    'connect to wifi home_network',
    'turn on bluetooth',
    'read my screen',
    'analyze my screen'
]

for t in tests:
    result = e.parse(t)
    print(f'{t} -> {result.intent_type.name}: {result.slots}')
