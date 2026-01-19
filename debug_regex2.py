#!/usr/bin/env python3
"""
Debug script to test the new regex pattern
"""

import re

def test_regex():
    # Test the specific pattern for "I have a girlfriend, I love her, her name is Akansha"
    pattern = r'(i have|have)\s+a\s+(girlfriend|boyfriend)[^,]*,\s*(?:love|like|adore)\s+(?:her|him)[^,]*,\s+(?:her|his|their)\s+name\s+is\s+(\w+(?:\s+\w+)*)'

    test_string = "I have a girlfriend, I love her, her name is Akansha"

    matches = re.findall(pattern, test_string, re.IGNORECASE)
    print(f"Pattern: {pattern}")
    print(f"Test string: {test_string}")
    print(f"Matches found: {matches}")

    # Test the other pattern too
    pattern2 = r'(girlfriend|boyfriend),?\s+(?:her|his|their)\s+name\s+is\s+(\w+(?:\s+\w+)*)'
    matches2 = re.findall(pattern2, test_string, re.IGNORECASE)
    print(f"Pattern 2: {pattern2}")
    print(f"Matches found: {matches2}")

    # Test the original complex pattern without word boundaries temporarily
    pattern3 = r'(i have|have)\s+a\s+(mom|dad|mother|father|brother|sister|son|daughter|wife|husband|spouse|friend|colleague|boss|employee|girlfriend|boyfriend|gf|bf|partner|crush|date|ex|ex-girlfriend|ex-boyfriend|ex-wife|ex-husband)[^,]*,\s*(?:love|like|adore)\s+(?:her|him)[^,]*,\s+(?:her|his|their)\s+name\s+is\s+(\w+(?:\s+\w+)*)'
    matches3 = re.findall(pattern3, test_string, re.IGNORECASE)
    print(f"Pattern 3 (original without \\b): {pattern3}")
    print(f"Matches found: {matches3}")

if __name__ == "__main__":
    test_regex()