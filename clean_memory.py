#!/usr/bin/env python3
"""
Script to clean up the memory.json file by removing irrelevant data
"""

import json
import os

def clean_memory_file():
    memory_file = "jarvis/config/memory.json"
    
    # Load the current memory
    with open(memory_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("Original memory data loaded.")
    
    # Clean up facts that don't belong to the user
    if 'long_term' in data and 'facts' in data['long_term']:
        original_count = len(data['long_term']['facts'].get('general', []))
        cleaned_facts = []
        
        for fact in data['long_term']['facts'].get('general', []):
            # Keep facts that are genuinely about the user
            if any(keyword in fact.lower() for keyword in ['shashi', 'mishra', 'vnit', 'student', 'education', 'college']):
                cleaned_facts.append(fact)
            else:
                print(f"Removing irrelevant fact: {fact}")
        
        data['long_term']['facts']['general'] = cleaned_facts
        print(f"Cleaned facts: {original_count} -> {len(cleaned_facts)}")
    
    # Clean up relationships that don't make sense
    if 'relationships' in data:
        original_count = len(data['relationships'])
        # Keep only relationships that seem legitimate
        legitimate_relationships = {}
        
        for person, details in data['relationships'].items():
            # Keep relationships that are clearly defined
            if details.get('type') in ['father', 'mother', 'girlfriend', 'boyfriend', 'friend', 'wife', 'husband', 'sister', 'brother']:
                legitimate_relationships[person] = details
            elif person.lower() in ['ravishankar mishra', 'akansha', 'abhijeet dhuke', 'om sutwane']:  # Known legitimate names
                legitimate_relationships[person] = details
            else:
                print(f"Removing questionable relationship: {person} -> {details}")
        
        data['relationships'] = legitimate_relationships
        print(f"Cleaned relationships: {original_count} -> {len(legitimate_relationships)}")
    
    # Clean up interests that don't make sense
    if 'interests' in data:
        original_count = len(data['interests'])
        cleaned_interests = []
        
        for interest in data['interests']:
            # Keep meaningful interests
            if interest.strip() and len(interest.strip()) > 1 and interest not in ['s', 'her']:
                cleaned_interests.append(interest)
            else:
                print(f"Removing meaningless interest: {interest}")
        
        data['interests'] = list(set(cleaned_interests))  # Remove duplicates too
        print(f"Cleaned interests: {original_count} -> {len(data['interests'])}")
    
    # Save the cleaned memory
    with open(memory_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    
    print("Memory file cleaned successfully!")

if __name__ == "__main__":
    clean_memory_file()