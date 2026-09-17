"""Local person segmentation, used only while the domain is visible."""
import cv2
import numpy as np
from .tracker import ROOT, download_model

MODEL = ROOT/'models'/'selfie_segmenter.tflite'
URL = 'https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_segmenter/float16/latest/selfie_segmenter.tflite'


class Foreground:
    def __init__(self):
        import mediapipe as mp
        self.mp = mp
        path = download_model(MODEL, URL, 100_000, 'Arka plan ayırma modeli (yaklaşık 250 KB)')
        options = mp.tasks.vision.ImageSegmenterOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(path)),
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            output_confidence_masks=True, output_category_mask=False)
        self.segmenter = mp.tasks.vision.ImageSegmenter.create_from_options(options)
        self.timestamp = -1

    def mask(self, frame, now):
        h,w = frame.shape[:2]
        small = cv2.resize(frame,(384,round(h*384/w)))
        rgb = np.ascontiguousarray(cv2.cvtColor(small,cv2.COLOR_BGR2RGB))
        self.timestamp = max(self.timestamp+1,int(now*1000))
        result = self.segmenter.segment_for_video(
            self.mp.Image(image_format=self.mp.ImageFormat.SRGB,data=rgb), self.timestamp)
        # This binary selfie model has one confidence output: probability of person.
        confidence = result.confidence_masks[0].numpy_view().copy()
        mask = np.clip((confidence-.20)/.65,0.,1.).astype(np.float32)
        mask = cv2.GaussianBlur(mask,(0,0),1.)
        return cv2.resize(mask,(w,h))

    def close(self):
        self.segmenter.close()
