#!/usr/bin/env python3
"""
Debug script to test the regex step by step
"""

import re

def test_regex_step_by_step():
    test_string = "I have a girlfriend, I love her, her name is Akansha"
    print(f"Test string: {test_string}")
    
    # Break down the pattern step by step
    # "I have a girlfriend, I love her, her name is Akansha"
    
    # Step 1: Check if "I have a" is matched
    step1 = r'(i have|have)\s+a\s+'
    matches1 = re.findall(step1, test_string, re.IGNORECASE)
    print(f"Step 1 - '(i have|have)\\s+a\\s+': {matches1}")
    
    # Step 2: Check if "girlfriend" is matched
    step2 = r'a\s+(girlfriend|boyfriend)'
    matches2 = re.findall(step2, test_string, re.IGNORECASE)
    print(f"Step 2 - 'a (girlfriend|boyfriend)': {matches2}")
    
    # Step 3: Check if ", I love her" is matched
    step3 = r'girlfriend,\s*I\s*love\s*her'
    matches3 = re.findall(step3, test_string, re.IGNORECASE)
    print(f"Step 3 - 'girlfriend, I love her': {matches3}")
    
    # Step 4: Check if ", her name is Akansha" is matched
    step4 = r'her\s+name\s+is\s+(\w+)'
    matches4 = re.findall(step4, test_string, re.IGNORECASE)
    print(f"Step 4 - 'her name is (\\w+)': {matches4}")
    
    # Full pattern with simplified version
    full_pattern = r'(i have|have)\s+a\s+(girlfriend|boyfriend)[^,]*,\s*i\s+love\s+her[^,]*,\s+her\s+name\s+is\s+(\w+)'
    full_matches = re.findall(full_pattern, test_string, re.IGNORECASE)
    print(f"Full pattern: {full_pattern}")
    print(f"Full matches: {full_matches}")
    
    # Even more specific
    very_specific = r'I have a girlfriend, I love her, her name is (\w+)'
    specific_matches = re.findall(very_specific, test_string, re.IGNORECASE)
    print(f"Very specific: {very_specific}")
    print(f"Specific matches: {specific_matches}")

if __name__ == "__main__":
    test_regex_step_by_step()