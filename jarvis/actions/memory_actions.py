import json
import os

# Use the centralized Memory class for all memory operations
from core.memory import Memory

def remember_user_preference(key, value):
    """Remember a user preference persistently"""
    print(f"Remembering preference: {key} = {value}")
    mem = Memory()
    
    # Store in a preferences sub-dict to keep organized
    if 'preferences' not in mem.long_term:
        mem.long_term['preferences'] = {}
    
    mem.long_term['preferences'][key] = value
    mem.save_memory()
    return f"Remembered that {key} is {value}"

def recall_memory(key):
    """Recall a user preference"""
    print(f"Recalling memory: {key}")
    mem = Memory()
    
    # Check preferences first
    if 'preferences' in mem.long_term and key in mem.long_term['preferences']:
        value = mem.long_term['preferences'][key]
        return f"{key} is {value}"
    
    # Check general memory
    value = mem.get(key)
    if value:
        return f"{key} is {value}"
    
    return f"I don't remember anything about {key}."

def update_memory(key, value):
    """Update a memory value"""
    print(f"Updating memory: {key} = {value}")
    mem = Memory()
    mem.set(key, value)
    return f"Updated memory for {key}"

def delete_memory(key):
    """Delete a memory"""
    print(f"Deleting memory: {key}")
    mem = Memory()
    
    # Check preferences
    if 'preferences' in mem.long_term and key in mem.long_term['preferences']:
        del mem.long_term['preferences'][key]
        mem.save_memory()
        return f"Deleted preference for {key}"
    
    # Check general memory
    if key in mem.long_term:
        del mem.long_term[key]
        mem.save_memory()
        return f"Deleted memory for {key}"
    
    return f"No memory found for {key}"

def forget_memory(key):
    """Alias for delete_memory"""
    return delete_memory(key)

def list_memories():
    """List all memories"""
    print("Listing all memories...")
    mem = Memory()
    return json.dumps(mem.long_term, indent=2)

# ===== NEW: Session and Task Memory Actions =====

def save_session_summary(summary):
    """Save a summary of the current session"""
    print(f"Saving session summary: {summary}")
    from core.memory import Memory
    mem = Memory()
    mem.add_session(summary)
    return "Session summary saved."

def get_recent_sessions(count=5):
    """Get recent session summaries"""
    print(f"Getting {count} recent sessions...")
    from core.memory import Memory
    mem = Memory()
    sessions = mem.get_recent_sessions(count)
    if sessions:
        result = "\n".join([f"[{s['timestamp']}] {s['summary']}" for s in sessions])
        return f"Recent sessions:\n{result}"
    return "No previous sessions found."

def remember_task(task_name, description):
    """Remember an ongoing task"""
    print(f"Remembering task: {task_name}")
    from core.memory import Memory
    mem = Memory()
    mem.add_task(task_name, {'description': description, 'status': 'active'})
    return f"Task '{task_name}' remembered."

def update_task_status(task_name, status):
    """Update task status"""
    print(f"Updating task {task_name} status: {status}")
    from core.memory import Memory
    mem = Memory()
    mem.update_task(task_name, {'status': status})
    return f"Task '{task_name}' updated."

def recall_task(task_name):
    """Recall task details"""
    print(f"Recalling task: {task_name}")
    from core.memory import Memory
    mem = Memory()
    task = mem.get_task(task_name)
    if task:
        return f"Task '{task_name}': {task['data']}"
    return f"No task named '{task_name}' found."

def list_tasks():
    """List all active tasks"""
    print("Listing all tasks...")
    from core.memory import Memory
    mem = Memory()
    tasks = mem.list_tasks()
    if tasks:
        return f"Active tasks: {', '.join(tasks)}"
    return "No active tasks."

def complete_task(task_name):
    """Mark task as complete"""
    print(f"Completing task: {task_name}")
    from core.memory import Memory
    mem = Memory()
    mem.complete_task(task_name)
    return f"Task '{task_name}' marked as complete."

def search_memories(query, top_k=3):
    """Search memories using semantic similarity"""
    print(f"Searching memories for: {query}")
    from core.memory import Memory
    mem = Memory()
    results = mem.search_memory(query, top_k)
    if results:
        return "Relevant memories:\n" + "\n".join([f"- {r}" for r in results])
    return "No relevant memories found."

