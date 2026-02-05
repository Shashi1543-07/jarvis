
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'jarvis')))

# Mock cv2 before importing vision_manager if strict dependency
sys.modules['cv2'] = MagicMock()

from core.vision.vision_manager import VisionManager

class TestVisionManager(unittest.TestCase):
    def setUp(self):
        # Reset singleton logic for testing
        VisionManager._instance = None
        self.vm = VisionManager()

    @patch('cv2.VideoCapture')
    def test_priority_logic_external_first(self, mock_cap):
        # Setup mock: Index 0 and 1 are valid. 1 should be preferred.
        
        def side_effect(index, api=None):
            mock_obj = MagicMock()
            if index in [0, 1]:
                mock_obj.isOpened.return_value = True
                mock_obj.read.return_value = (True, "frame")
            else:
                mock_obj.isOpened.return_value = False
            return mock_obj
            
        mock_cap.side_effect = side_effect
        
        # Scan
        print("Scaning cameras (mocked)...")
        available = self.vm.scan_cameras(max_cameras_to_check=3)
        print(f"Available cameras: {available}")
        
        # Select
        best = self.vm.select_best_camera()
        print(f"Best camera selected: {best}")
        
        self.assertEqual(best, 1, "Should select highest index (external) camera")

    @patch('cv2.VideoCapture')
    def test_internal_only(self, mock_cap):
        # Setup mock: Only Index 0 is valid.
        
        def side_effect(index, api=None):
            mock_obj = MagicMock()
            if index == 0:
                mock_obj.isOpened.return_value = True
                mock_obj.read.return_value = (True, "frame")
            else:
                mock_obj.isOpened.return_value = False
            return mock_obj
            
        mock_cap.side_effect = side_effect
        
        # Scan
        available = self.vm.scan_cameras(max_cameras_to_check=3)
        print(f"Available cameras (internal only): {available}")
        
        # Select
        best = self.vm.select_best_camera()
        
        self.assertEqual(best, 0, "Should select index 0 if only one available")

    @patch('cv2.VideoCapture')
    def test_open_vision_feedback(self, mock_cap):
        # Test the open_vision method return values
        
        # Mock index 1 available
        def side_effect(index, api=None):
            m = MagicMock()
            if index == 1:
                m.isOpened.return_value = True
                m.read.return_value = (True, "frame")
            else:
                m.isOpened.return_value = False
            return m
        mock_cap.side_effect = side_effect
        
        result = self.vm.open_vision()
        print(f"Open Vision Result: {result}")
        
        self.assertTrue(result['success'])
        self.assertTrue("external" in result['message'] or "external" in result['camera_type'])
        self.assertEqual(result['index'], 1)

if __name__ == '__main__':
    unittest.main()
