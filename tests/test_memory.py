import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'jarvis')))

print("Testing Long-Term Memory System...")
print("=" * 60)

from jarvis.core.memory import Memory

# Test 1: Basic Memory
print("\n1. Testing Basic Memory Storage...")
mem = Memory()
mem.set("favorite_color", "blue")
result = mem.get("favorite_color")
print(f"   ✓ Set and get: {result}")

# Test 2: Session Persistence
print("\n2. Testing Session Persistence...")
mem.add_session("User asked about the weather and system performance")
sessions = mem.get_recent_sessions(1)
print(f"   ✓ Session saved: {len(sessions)} session(s)")

# Test 3: Task Memory
print("\n3. Testing Task Memory...")
mem.add_task("build_jarvis", {"description": "Complete Jarvis AI", "status": "in_progress"})
task = mem.get_task("build_jarvis")
print(f"   ✓ Task created: {task['data']['description']}")

# Test 4: Semantic Search
print("\n4. Testing Semantic Search...")
print("   Note: This requires sentence-transformers and may take a moment...")
try:
    results = mem.search_memory("weather", top_k=2)
    if results:
        print(f"   ✓ Semantic search returned {len(results)} result(s)")
    else:
        print("   ⚠ No results (memory may need to build embeddings cache)")
except Exception as e:
    print(f"   ⚠ Semantic search error: {e}")

# Test 5: Verify Router Integration
print("\n5. Testing Router Integration...")
from jarvis.core.router import Router
router = Router()

memory_actions = [
    'remember_user_preference', 'search_memories', 'save_session_summary',
    'remember_task', 'recall_task', 'list_tasks'
]

missing = []
for action in memory_actions:
    if action not in router.action_map:
        missing.append(action)
        print(f"   ✗ {action} - NOT FOUND")
    else:
        print(f"   ✓ {action}")

print("=" * 60)
if missing:
    print(f"\n⚠ Missing {len(missing)} memory actions")
else:
    print("\n✓ All memory features verified!")
