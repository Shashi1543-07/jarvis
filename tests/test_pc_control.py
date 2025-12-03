import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'jarvis')))

from jarvis.core.router import Router

print("Testing PC System Control Integration...")
print("=" * 60)

router = Router()

# Check that key PC control actions are accessible
test_actions = [
    'set_brightness', 'set_volume', 'battery_status', 'system_performance',
    'type_text', 'mouse_move', 'mouse_click', 'mouse_scroll',
    'create_file', 'read_file', 'delete_file', 'read_document_aloud',
    'open_app', 'close_app'
]

missing = []
for action in test_actions:
    if action in router.action_map:
        print(f"✓ {action}")
    else:
        print(f"✗ {action} - NOT FOUND")
        missing.append(action)

print("=" * 60)
if missing:
    print(f"\n⚠ Missing {len(missing)} actions: {', '.join(missing)}")
else:
    print("\n✓ All PC control actions are available!")
    print(f"\nTotal actions registered: {len(router.action_map)}")
