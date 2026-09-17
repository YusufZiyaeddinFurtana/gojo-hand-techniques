"""MediaPipe Tasks adapter and explicit, atomic model installation."""
from pathlib import Path
import ssl
import urllib.request
import cv2
import numpy as np
from .gestures import classify

ROOT = Path(__file__).resolve().parent.parent
MODEL = ROOT / 'models' / 'hand_landmarker.task'
MODEL_URL = 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task'


def download_model(path=MODEL, url=MODEL_URL, min_size=1_000_000, title='El takip modeli'):
    path = Path(path)
    if path.is_file() and path.stat().st_size > min_size:
        return path
    import certifi
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.part')
    print(f'{title} indiriliyor…', flush=True)
    try:
        with urllib.request.urlopen(url, timeout=60,
                                    context=ssl.create_default_context(cafile=certifi.where())) as response:
            with temporary.open('wb') as output:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
        if temporary.stat().st_size < min_size:
            raise RuntimeError('Model indirmesi eksik; tekrar deneyin.')
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    return path


class Tracker:
    def __init__(self, model=MODEL, swap=False):
        import mediapipe as mp
        self.mp = mp
        self.swap = swap
        self.timestamp = -1
        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(model)),
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_hands=2, min_hand_detection_confidence=.55,
            min_hand_presence_confidence=.55, min_tracking_confidence=.55)
        self.detector = mp.tasks.vision.HandLandmarker.create_from_options(options)

    def detect(self, mirrored_frame, now):
        h, w = mirrored_frame.shape[:2]
        # Smaller inference image; landmarks map back to the full effect canvas.
        small = cv2.resize(mirrored_frame, (640, round(h * 640 / w))) if w > 640 else mirrored_frame
        rgb = np.ascontiguousarray(cv2.cvtColor(small, cv2.COLOR_BGR2RGB))
        timestamp = max(self.timestamp + 1, int(now * 1000))
        self.timestamp = timestamp
        result = self.detector.detect_for_video(
            self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=rgb), timestamp)
        hands = []
        for landmarks, categories, world_landmarks in zip(
                result.hand_landmarks, result.handedness, result.hand_world_landmarks):
            label = categories[0].category_name
            points = np.array([(p.x * w, p.y * h) for p in landmarks])
            world = np.array([(p.x, p.y, p.z) for p in world_landmarks])
            hand = classify(points, label, categories[0].score, world)
            if self.swap:
                # Palm normal uses the original label; color assignment can swap.
                hand.side = 'Right' if label == 'Left' else 'Left'
                if hand.side == 'Left':
                    hand.anchor = hand.palm + [0, -hand.span * .75]
                elif hand.seal:
                    tip = (points[8] + points[12]) * .5
                    direction = tip - hand.palm
                    direction /= max(float(np.linalg.norm(direction)), 1.)
                    hand.anchor = tip + direction * hand.span * .45
                else:
                    hand.anchor = hand.palm.copy()
            hands.append(hand)
        return hands

    def close(self):
        self.detector.close()
