import unittest
import numpy as np
from gojo.eyes import EYES, extract_eyes, blue_eyes


def face_points(openness=.3):
    p=np.zeros((478,2),float)
    for k,(lid_ids,iris_ids,upper,lower) in enumerate(EYES):
        cx,cy=80.+k*80,80.
        p[lid_ids]=np.array([[-25,0],[-12,-8],[12,-8],[25,0],[12,8],[-12,8]])+[cx,cy]
        p[iris_ids]=np.array([[-9,0],[0,-9],[9,0],[0,9]])+[cx,cy]
        p[upper],p[lower]=[cx,cy-25*openness],[cx,cy+25*openness]
    return p


class EyeTests(unittest.TestCase):
    def setUp(self):
        self.frame=np.full((160,240,3),60,np.uint8)
        self.eyes=extract_eyes(face_points())

    def test_both_irises_detected_from_topology(self):
        self.assertEqual(len(self.eyes),2)
        np.testing.assert_allclose(self.eyes[0].center,[80,80])

    def test_blue_effect_moves_with_landmarks(self):
        a=blue_eyes(self.frame,self.eyes,1.,1.)
        shifted=extract_eyes(face_points()+[0,45])
        b=blue_eyes(self.frame,shifted,1.,1.)
        self.assertGreater(int(a[80,87,0])-int(a[80,87,2]),100)
        np.testing.assert_array_equal(b[80,87],self.frame[80,87])
        self.assertGreater(int(b[125,87,0])-int(b[125,87,2]),100)

    def test_pupil_stays_darker_than_iris(self):
        result=blue_eyes(self.frame,self.eyes,1.,1.)
        self.assertLess(result[80,80,0],result[80,87,0])

    def test_eyelid_clipping_and_local_bloom(self):
        result=blue_eyes(self.frame,self.eyes,1.,1.)
        np.testing.assert_array_equal(result[20:40],self.frame[20:40])
        self.assertLess(int(result[68,80,0])-60,25)

    def test_blink_or_missing_face_leaves_no_glow(self):
        closed=extract_eyes(face_points(.02))
        self.assertEqual(closed,[])
        for eyes in (closed,[],extract_eyes([])):
            np.testing.assert_array_equal(blue_eyes(self.frame,eyes,1.,1.),self.frame)

    def test_domain_off_is_pixel_identical(self):
        np.testing.assert_array_equal(blue_eyes(self.frame,self.eyes,0.,1.),self.frame)

    def test_partial_face_outside_canvas_does_not_crash(self):
        eyes=extract_eyes(face_points()-[85,70])
        result=blue_eyes(self.frame,eyes,1.,1.)
        self.assertEqual(result.shape,self.frame.shape)

    def test_invalid_landmarks_are_rejected(self):
        p=face_points()
        p[0,0]=np.nan
        self.assertEqual(extract_eyes(p),[])
