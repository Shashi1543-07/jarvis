"""
Scene Description - Natural language scene understanding using BLIP
Generates human-readable descriptions of what's in the camera view
"""

import cv2
import numpy as np
from PIL import Image

try:
    from transformers import BlipProcessor, BlipForConditionalGeneration
    import torch
    BLIP_AVAILABLE = True
except ImportError:
    BLIP_AVAILABLE = False
    print("[SceneDescriptor] Warning: transformers not installed. Scene description disabled.")

class SceneFuser:
    """Fuses object detection and BLIP descriptions into high-level semantic context"""
    
    SCENE_RULES = {
        "office/workspace": ["laptop", "mouse", "keyboard", "monitor", "desk", "book"],
        "classroom/lab": ["whiteboard", "microscope", "desk", "chair", "person"],
        "bedroom": ["bed", "pillow", "blanket", "wardrobe"],
        "living_room": ["sofa", "television", "remote", "coffee table"],
        "kitchen": ["refrigerator", "oven", "microwave", "sink", "dining table"],
        "outdoor/road": ["car", "tree", "traffic light", "building", "person", "bicycle"],
    }

    def infer_scene(self, objects, blip_description):
        """
        Heuristic-based context fusion.
        """
        scores = {scene: 0 for scene in self.SCENE_RULES}
        desc_lower = blip_description.lower()
        
        # 1. Object-based scoring
        for scene, keywords in self.SCENE_RULES.items():
            for obj in objects:
                if obj.lower() in keywords:
                    scores[scene] += 1
            
            # 2. Description keyword matching
            for word in scene.replace("/", " ").split():
                if word in desc_lower:
                    scores[scene] += 2
        
        # Get best match
        best_scene = max(scores, key=scores.get)
        if scores[best_scene] < 2:
            return "unknown environment"
        return best_scene


class SceneDescriptor:
    """BLIP-based scene description generator"""
    
    def __init__(self, model_name="Salesforce/blip-image-captioning-base"):
        """
        Initialize Scene Descriptor
        
        Args:
            model_name: HuggingFace model name
        """
        self.processor = None
        self.model = None
        self.model_name = model_name
        self.device = "cuda" if BLIP_AVAILABLE and hasattr(torch, 'cuda') and torch.cuda.is_available() else "cpu"
        
        if not BLIP_AVAILABLE:
            print("[SceneDescriptor] BLIP not available")
            return
        
        self.fuser = SceneFuser()
        print(f"[SceneDescriptor] Initialized (model will load on first use, device: {self.device})")

    def analyze_luminosity(self, frame):
        """Analyze frame brightness to detect night/dark scenes"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        avg_brightness = np.mean(gray)
        return "night/dark" if avg_brightness < 40 else "day/bright"
    
    def _load_model(self):
        """Lazy load BLIP model"""
        if self.model is None and BLIP_AVAILABLE:
            print(f"[SceneDescriptor] Loading {self.model_name}...")
            try:
                self.processor = BlipProcessor.from_pretrained(self.model_name)
                self.model = BlipForConditionalGeneration.from_pretrained(self.model_name)
                self.model.to(self.device)
                self.model.eval()  # Set to evaluation mode
                print(f"[SceneDescriptor] Model loaded successfully on {self.device}")
            except Exception as e:
                print(f"[SceneDescriptor] Failed to load model: {e}")
    
    def describe(self, frame, prompt=None):
        """
        Generate natural language description of the scene
        
        Args:
            frame: OpenCV BGR frame
            prompt: Optional text prompt to guide generation
            
        Returns:
            dict with description and metadata
        """
        if not BLIP_AVAILABLE:
            return {
                'description': '',
                'error': 'BLIP not available. Install transformers and torch.'
            }
        
        # Load model if not loaded
        self._load_model()
        
        if self.model is None:
            return {
                'description': '',
                'error': 'Model failed to load'
            }
        
        try:
            # Convert OpenCV BGR to PIL RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_frame)
            
            # Process image
            if prompt:
                # Conditional generation with prompt
                inputs = self.processor(pil_image, prompt, return_tensors="pt").to(self.device)
            else:
                # Unconditional caption generation
                inputs = self.processor(pil_image, return_tensors="pt").to(self.device)
            
            # Generate caption
            with torch.no_grad():
                outputs = self.model.generate(**inputs, max_length=50)
            
            # Decode caption
            caption = self.processor.decode(outputs[0], skip_special_tokens=True)
            
            return {
                'description': caption,
                'success': True
            }
            
        except Exception as e:
            return {
                'description': '',
                'error': f'Failed to generate description: {str(e)}'
            }
    
    def describe_detailed(self, frame):
        """
        Generate a more detailed description by asking multiple questions
        
        Args:
            frame: OpenCV BGR frame
            
        Returns:
            dict with detailed description
        """
        # Generate base description
        base_desc = self.describe(frame)
        
        if 'error' in base_desc:
            return base_desc
        
        # You could extend this with multiple prompts:
        # - "What objects are in this image?"
        # - "What is the person doing?"
        # - "What is the environment like?"
        
        return {
            'description': base_desc['description'],
            'success': True
        }
    
    def get_semantic_context(self, frame, detected_objects):
        """
        Get structured semantic context by fusing everything.
        """
        desc_res = self.describe(frame)
        description = desc_res.get('description', 'unclear')
        
        scene_type = self.fuser.infer_scene(detected_objects, description)
        lighting = self.analyze_luminosity(frame)
        
        # Combine lighting with scene if dark
        if lighting == "night/dark" and scene_type != "unknown environment":
            scene_type = f"{scene_type} at night"
            
        return {
            "scene_type": scene_type,
            "key_objects": list(set(detected_objects)),
            "people_count": detected_objects.count("person"),
            "confidence": 0.85 if scene_type != "unknown environment" else 0.4,
            "summary": f"I'm looking at a {scene_type}. I see {len(detected_objects)} objects including {', '.join(list(set(detected_objects))[:3])}."
        }

    def answer_question(self, frame, question):
        """
        Answer a question about the image using Visual Question Answering
        
        Args:
            frame: OpenCV BGR frame
            question: Question to answer
            
        Returns:
            dict with answer
        """
        # BLIP can do conditional generation with prompts
        result = self.describe(frame, prompt=question)
        
        if 'error' in result:
            return result
        
        return {
            'question': question,
            'answer': result['description'],
            'success': True
        }
