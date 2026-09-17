"""Local iris tracking and eyelid-clipped cyan eyes for Unlimited Void."""
from dataclasses import dataclass
import cv2
import numpy as np
from .tracker import ROOT, download_model

MODEL = ROOT / 'models' / 'face_landmarker.task'
URL = 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task'
# MediaPipe FaceLandmarker topology: eyelid perimeter, iris ring, upper/lower lid.
EYES = (
    ([33,160,158,133,153,144], [469,470,471,472], 159,145),
    ([362,385,387,263,373,380], [474,475,476,477], 386,374),
)


@dataclass
class Eye:
    lid: np.ndarray
    center: np.ndarray
    radius: float
    openness: float


def extract_eyes(points):
    """Never reuse stale positions: missing faces and closed eyes produce no glow."""
    p = np.asarray(points,dtype=float)
    if p.shape != (478,2) or not np.isfinite(p).all():
        return []
    eyes = []
    for lid_ids,iris_ids,upper,lower in EYES:
        lid,ring = p[lid_ids],p[iris_ids]
        center = ring.mean(axis=0)
        radius = float(np.mean(np.linalg.norm(ring-center,axis=1)))
        width = float(np.linalg.norm(lid[0]-lid[3]))
        openness = float(np.linalg.norm(p[upper]-p[lower]) / max(width,1.))
        if width >= 8 and .075 < openness < .65 and 1. < radius < width*.45:
            eyes.append(Eye(lid,center,radius,openness))
    return eyes


class EyeTracker:
    def __init__(self):
        import mediapipe as mp
        self.mp = mp
        path = download_model(MODEL,URL,1_000_000,'Göz takip modeli (yaklaşık 4 MB)')
        options = mp.tasks.vision.FaceLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(path)),
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_faces=1,min_face_detection_confidence=.5,
            min_face_presence_confidence=.5,min_tracking_confidence=.5)
        self.detector = mp.tasks.vision.FaceLandmarker.create_from_options(options)
        self.timestamp = -1

    def detect(self,frame,now):
        h,w = frame.shape[:2]
        small = cv2.resize(frame,(640,round(h*640/w))) if w > 640 else frame
        rgb = np.ascontiguousarray(cv2.cvtColor(small,cv2.COLOR_BGR2RGB))
        self.timestamp = max(self.timestamp+1,int(now*1000))
        result = self.detector.detect_for_video(
            self.mp.Image(image_format=self.mp.ImageFormat.SRGB,data=rgb),self.timestamp)
        if not result.face_landmarks:
            return []
        return extract_eyes([(p.x*w,p.y*h) for p in result.face_landmarks[0]])

    def close(self):
        self.detector.close()


def blue_eyes(frame,eyes,strength,now):
    """Keep the pupil and iris texture; cyan iris and restrained blue bloom."""
    if strength <= 0 or not eyes:
        return frame
    out = frame.copy()
    h,w = frame.shape[:2]
    for eye in eyes:
        cx,cy = eye.center
        r = eye.radius
        pad = max(5.,r*3.5)
        x0,y0 = max(0,int(cx-pad)),max(0,int(cy-pad))
        x1,y1 = min(w,int(cx+pad+1)),min(h,int(cy+pad+1))
        if x1 <= x0 or y1 <= y0:
            continue
        roi = out[y0:y1,x0:x1]
        yy,xx = np.mgrid[y0:y1,x0:x1]
        distance = np.hypot(xx-cx,yy-cy)/max(r,1.)
        angle = np.arctan2(yy-cy,xx-cx)
        clip = np.zeros(roi.shape[:2],np.uint8)
        cv2.fillPoly(clip,[np.round(eye.lid-[x0,y0]).astype(np.int32)],255,lineType=cv2.LINE_AA)
        clip = clip.astype(np.float32)/255.
        iris = np.clip((1.12-distance)*7.,0,1)*clip
        pupil = np.clip((distance-.22)*7.,0,1)
        fibers = .5+.5*np.sin(angle*26+distance*17+now*.3)
        brightness = .65+.25*fibers+.1*np.sin(now*3.)
        color = np.stack([np.full_like(distance,255),175+65*brightness,35+45*brightness],axis=-1)
        blink = np.clip((eye.openness-.075)/.08,0,1)
        alpha = (iris*pupil*.88*strength*blink)[...,None]
        result = roi*(1-alpha)+color*alpha
        # Bloom starts from the visible iris, so blinks cannot leave floating dots.
        glow = cv2.GaussianBlur(iris*pupil,(0,0),max(1.,r*.65))
        result += glow[...,None]*np.array([70.,38.,5.])*strength*blink
        rim = np.exp(-((distance-.8)/.14)**2)*iris
        result += rim[...,None]*np.array([32.,42.,12.])*strength*blink
        roi[:] = np.clip(result,0,255).astype(np.uint8)
    return out
