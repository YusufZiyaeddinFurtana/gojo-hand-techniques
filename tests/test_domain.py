import unittest
import numpy as np
from gojo.domain import Domain
from gojo.engine import Technique
from gojo.gestures import Hand, classify
from gojo.void_effect import VoidRenderer
from gojo.demo import domain_demo_frame


def h(side='Right',crossed=True,confidence=1.):
    p=np.array([600.,350.])
    return Hand(side,p,p.copy(),70,crossed=crossed,confidence=confidence)


class DomainTests(unittest.TestCase):
    def setUp(self):
        self.d,self.t,self.activations=Domain(),0.,0

    def feed(self,seconds,hands,fps=30):
        for _ in range(round(seconds*fps)):
            self.t+=1/fps
            self.activations+=self.d.update({x.side:x for x in hands},self.t)

    def activate(self):
        self.feed(.8,[h()])
        self.assertTrue(self.d.active(self.t))

    def test_crossed_hold_activates_either_hand(self):
        for side in ('Right','Left'):
            self.d=Domain()
            self.feed(.8,[h(side)])
            self.assertTrue(self.d.active(self.t))

    def test_brief_or_interrupted_gesture_cannot_activate(self):
        self.feed(.3,[h()])
        self.feed(.1,[])
        self.feed(.3,[h()])
        self.assertFalse(self.d.active(self.t))

    def test_short_visible_classification_flicker_retains_progress(self):
        self.feed(.3,[h()])
        self.feed(2/30,[h(crossed=False)])
        self.feed(.3,[h()])
        self.assertEqual(self.activations,1)

    def test_long_uncrossed_pose_resets_progress(self):
        self.feed(.3,[h()])
        self.feed(.2,[h(crossed=False)])
        self.feed(.3,[h()])
        self.assertEqual(self.activations,0)

    def test_activation_time_independent_of_frame_rate(self):
        for fps in (15,30,60):
            d=Domain()
            for i in range(round(.7*fps)):
                d.update({'Right':h()},i/fps)
            self.assertTrue(d.active(.7))

    def test_low_confidence_does_not_activate(self):
        self.feed(1.,[h(confidence=.4)])
        self.assertEqual(self.activations,0)

    def test_left_and_right_hold_time_cannot_be_combined(self):
        self.feed(.4,[h('Left')])
        self.feed(.4,[h('Right')])
        self.assertEqual(self.activations,0)

    def test_duration_is_twelve_seconds_without_tracking(self):
        self.activate()
        start=self.d.started
        self.feed(11.,[])
        self.assertTrue(self.d.active(self.t))
        self.assertFalse(self.d.active(start+12))
        self.assertEqual(self.d.strength(start+12),0.)

    def test_holding_pose_does_not_retrigger(self):
        self.feed(28.,[h()])
        self.assertEqual(self.activations,1)

    def test_release_then_new_pose_allows_second_domain(self):
        self.activate()
        self.feed(13.,[])
        self.feed(.4,[h(crossed=False)])
        self.feed(.8,[h()])
        self.assertEqual(self.activations,2)

    def test_frame_stall_does_not_complete_hold(self):
        self.feed(.5,[h()])
        self.t+=2
        self.feed(.3,[h()])
        self.assertEqual(self.activations,0)

    def test_fades_have_no_abrupt_endpoint(self):
        self.activate()
        start=self.d.started
        self.assertEqual(self.d.strength(start),0.)
        self.assertLess(self.d.strength(start+.1),.1)
        self.assertEqual(self.d.strength(start+2),1.)
        self.assertLess(self.d.strength(start+11.9),.05)

    def test_reset_clears_domain(self):
        s=Technique()
        for i in range(30):
            s.update([h()],i/30)
        self.assertTrue(s.domain.active(1.))
        self.assertFalse(s.energy['Right'].active)
        s.reset()
        self.assertFalse(s.domain.active(1.))

    def test_existing_energy_can_remain_during_domain(self):
        s=Technique()
        s.energy['Right'].active=True
        for i in range(30):
            s.update([h()],i/30)
        self.assertTrue(s.energy['Right'].active)
        self.assertTrue(s.domain.active(1.))


class CrossGeometryTests(unittest.TestCase):
    def points(self,crossed):
        p=np.zeros((21,2))
        p[0]=[0,120]
        for i,xy in {5:(-30,40),6:(-20,0),8:(-25,-65),9:(0,35),10:(0,-5),
                     12:(-2,-72),13:(30,40),14:(30,0),16:(28,65),
                     17:(55,50),18:(55,20),20:(50,80),4:(-60,40)}.items():
            p[i]=xy
        if crossed:
            p[8],p[12]=[12,-55],[-18,-72]
        p[7]=(p[6]+p[8])*.5
        p[11]=(p[10]+p[12])*.5
        return p

    def test_crossing_detected_under_rotation_scale_and_mirroring(self):
        for mirror in (-1,1):
            for a in (0,.6,1.5,3.):
                r=np.array([[np.cos(a),-np.sin(a)],[np.sin(a),np.cos(a)]])
                p=self.points(True)*[mirror,1]
                result=classify(p@r*1.3+[500,350],'Right')
                self.assertTrue(result.crossed)
                self.assertFalse(result.seal)

    def test_bent_finger_segment_crossing_without_reversed_tips(self):
        p=self.points(False)
        p[6],p[7],p[8]=[-25,-5],[8,-42],[-5,-65]
        p[10],p[11],p[12]=[0,-8],[-16,-40],[3,-72]
        for mirror in (-1,1):
            for angle in (0,.7,1.8):
                r=np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]])
                self.assertTrue(classify((p*[mirror,1])@r*1.2+[300,250],'Left').crossed)

    def test_moderately_bent_raised_tip_is_accepted(self):
        p=self.points(True)
        p[8]=[8,8]
        p[7]=[2,-28]
        self.assertTrue(classify(p,'Right').crossed)

    def test_parallel_fingers_remain_red_not_domain(self):
        result=classify(self.points(False),'Right')
        self.assertTrue(result.seal)
        self.assertFalse(result.crossed)

    def test_touching_but_not_crossed_tips_are_rejected(self):
        p=self.points(False)
        p[8],p[12]=[-2,-70],[-2,-70]
        self.assertFalse(classify(p,'Right').crossed)

    def test_open_ring_and_pinky_reject_domain(self):
        p=self.points(True)
        p[16],p[20]=[30,-60],[55,-45]
        self.assertFalse(classify(p,'Right').crossed)


class VoidRenderTests(unittest.TestCase):
    def test_environment_changes_and_returns_without_text(self):
        d=Domain(started=0.)
        r=VoidRenderer()
        frame=np.full((360,640,3),90,np.uint8)
        empty=np.zeros((360,640),np.float32)
        active=r.render(frame,d,3.,empty)
        self.assertGreater(np.mean(np.abs(active.astype(float)-frame)),20)
        np.testing.assert_array_equal(r.render(frame,d,12.,empty),frame)

    def test_foreground_is_preserved_by_segmentation(self):
        d=Domain(started=0.)
        frame=np.full((360,640,3),120,np.uint8)
        mask=np.zeros((360,640),np.float32)
        mask[100:300,250:390]=1
        result=VoidRenderer().render(frame,d,3.,mask)
        expected=np.array([112,104,100])
        np.testing.assert_array_equal(result[200,320],expected)

    def test_stars_change_over_time(self):
        r=VoidRenderer()
        a,b=r.sky(640,360,2.),r.sky(640,360,3.)
        self.assertGreater(np.mean(np.abs(a.astype(float)-b)),1.)

    def test_demo_triggers_once_and_expires(self):
        s=Technique()
        starts=set()
        for i in range(480):
            _,hands=domain_demo_frame(i/30,640,360)
            s.update(hands,i/30)
            if s.domain.started is not None:
                starts.add(s.domain.started)
        self.assertEqual(len(starts),1)
        self.assertFalse(s.domain.active(480/30))
