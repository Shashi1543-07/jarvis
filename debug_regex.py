#!/usr/bin/env python3
"""
Simple test to debug the relationship extraction
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'jarvis'))

import re

def test_regex_patterns():
    # Test the specific patterns we added
    relationship_patterns = [
        r'\b(my|his|her|their)\s+(mom|dad|mother|father|brother|sister|son|daughter|wife|husband|spouse|friend|colleague|boss|employee|girlfriend|boyfriend|gf|bf|partner|crush|date|ex|ex-girlfriend|ex-boyfriend|ex-wife|ex-husband)(?:\'s name is|\s+is)\s+(\w+(?:\s+\w+)*)',  # "my girlfriend's name is Sarah" or "my girlfriend is Sarah"
        r'\b(this is my|meet my)\s+(mom|dad|mother|father|brother|sister|son|daughter|wife|husband|spouse|friend|colleague|boss|employee|girlfriend|boyfriend|gf|bf|partner|crush|date|ex|ex-girlfriend|ex-boyfriend|ex-wife|ex-husband)\s+(\w+(?:\s+\w+)*)\b',  # "this is my girlfriend Sarah"
        r'\b(\w+(?:\s+\w+)*)\s+is my\s+(mom|dad|mother|father|brother|sister|son|daughter|wife|husband|spouse|friend|colleague|boss|employee|girlfriend|boyfriend|gf|bf|partner|crush|date|ex|ex-girlfriend|ex-boyfriend|ex-husband)\b',  # "Sarah is my girlfriend"
        r'\b(i have|have)\s+a\s+(mom|dad|mother|father|brother|sister|son|daughter|wife|husband|spouse|friend|colleague|boss|employee|girlfriend|boyfriend|gf|bf|partner|crush|date|ex|ex-girlfriend|ex-boyfriend|ex-wife|ex-husband)\s+(?:named|called|is)\s+(\w+(?:\s+\w+)*)\b',  # "I have a girlfriend named Sarah"
    ]
    
    test_inputs = [
        "This is my girlfriend Lisa",
        "My girlfriend's name is Emma Watson",
        "Sarah is my girlfriend",
        "I have a girlfriend named Jennifer"
    ]
    
    for user_input in test_inputs:
        print(f"\nTesting: '{user_input}'")
        all_matches = []
        # Test in the new order
        new_order_patterns = [
            r'\b(this is my|meet my)\s+(mom|dad|mother|father|brother|sister|son|daughter|wife|husband|spouse|friend|colleague|boss|employee|girlfriend|boyfriend|gf|bf|partner|crush|date|ex|ex-girlfriend|ex-boyfriend|ex-wife|ex-husband)\s+(\w+(?:\s+\w+)*)\b',  # "this is my girlfriend Sarah" - Put this first to catch this specific pattern
            r'\b(my|his|her|their)\s+(mom|dad|mother|father|brother|sister|son|daughter|wife|husband|spouse|friend|colleague|boss|employee|girlfriend|boyfriend|gf|bf|partner|crush|date|ex|ex-girlfriend|ex-boyfriend|ex-wife|ex-husband)(?:\'s name is|\s+is)\s+(\w+(?:\s+\w+)*)',  # "my girlfriend's name is Sarah" or "my girlfriend is Sarah"
            r'\b(\w+(?:\s+\w+)*)\s+is my\s+(mom|dad|mother|father|brother|sister|son|daughter|wife|husband|spouse|friend|colleague|boss|employee|girlfriend|boyfriend|gf|bf|partner|crush|date|ex|ex-girlfriend|ex-boyfriend|ex-husband)\b',  # "Sarah is my girlfriend" - This should come after patterns that start with possessives
            r'\b(i have|have)\s+a\s+(mom|dad|mother|father|brother|sister|son|daughter|wife|husband|spouse|friend|colleague|boss|employee|girlfriend|boyfriend|gf|bf|partner|crush|date|ex|ex-girlfriend|ex-boyfriend|ex-wife|ex-husband)\s+(?:named|called|is)\s+(\w+(?:\s+\w+)*)\b',  # "I have a girlfriend named Sarah"
        ]

        for i, pattern in enumerate(new_order_patterns):
            matches = re.findall(pattern, user_input, re.IGNORECASE)
            if matches:
                print(f"  New Pattern {i+1} matches: {matches}")
                all_matches.extend(matches)

        print(f"  All matches combined: {all_matches}")

if __name__ == "__main__":
    test_regex_patterns()