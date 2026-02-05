import sys
import os
import unittest
from unittest.mock import MagicMock

# Add repo root to path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, repo_root)

# Mock modules to avoid importing real dependencies
# We need to mock 'jarvis.core.voice.*' and 'jarvis.core.router' BEFORE importing AudioEngine

sys.modules['numpy'] = MagicMock()

# Create a mock for the router module
mock_router_module = MagicMock()
# Create a mock for the Router class
MockRouterClass = MagicMock()
mock_router_module.Router = MockRouterClass

# Mock the modules in sys.modules
sys.modules['jarvis.core.router'] = mock_router_module

# Mock voice submodules
sys.modules['jarvis.core.voice'] = MagicMock()
sys.modules['jarvis.core.voice.state_machine_enhanced'] = MagicMock()
sys.modules['jarvis.core.voice.mic'] = MagicMock()
sys.modules['jarvis.core.voice.vad'] = MagicMock()
sys.modules['jarvis.core.voice.stt'] = MagicMock()
sys.modules['jarvis.core.voice.tts'] = MagicMock()
sys.modules['jarvis.core.voice.aec_enhanced'] = MagicMock()
sys.modules['jarvis.core.voice.wake_word'] = MagicMock()
sys.modules['jarvis.core.voice.speaker_id'] = MagicMock()
sys.modules['jarvis.core.voice.noise_suppression'] = MagicMock()

# Now import AudioEngine
# We need to make sure we import it as jarvis.core.audio_engine
try:
    from jarvis.core.audio_engine import AudioEngine
except ImportError as e:
    print(f"Failed to import AudioEngine: {e}")
    sys.exit(1)

class TestAudioEngineInit(unittest.TestCase):
    def test_init_with_router(self):
        """Test initializing AudioEngine with a provided router."""
        print("\nTesting initialization with provided router...")
        my_router = MagicMock()
        my_router.on_intent_classified = None # mock attribute access

        # Reset calls to MockRouterClass
        MockRouterClass.reset_mock()

        engine = AudioEngine(router=my_router)

        self.assertEqual(engine.router, my_router, "Should use the provided router")
        print("AudioEngine used the provided router.")

        # Ensure Router() was NOT called
        MockRouterClass.assert_not_called()
        print("Confirmed new Router() was NOT instantiated.")

    def test_init_without_router(self):
        """Test initializing AudioEngine without a router (default behavior)."""
        print("\nTesting initialization WITHOUT provided router...")
        # Reset mock
        MockRouterClass.reset_mock()

        engine = AudioEngine()

        # It should have created a new Router
        self.assertNotEqual(engine.router, None)
        print("AudioEngine created a router.")

        # Verify Router() was called
        MockRouterClass.assert_called()
        print("Confirmed new Router() WAS instantiated.")

        # Verify engine.router is the return value of Router()
        self.assertEqual(engine.router, MockRouterClass.return_value)

if __name__ == '__main__':
    unittest.main()
