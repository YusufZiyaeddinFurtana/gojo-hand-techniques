import unittest
import numpy as np
from gojo.engine import Technique, FlickGate, Projectile
from gojo.gestures import Hand, classify, fingertip_gap


def hand(side='Right', x=600, y=350, seal=False, open_palm=False, pinch=2., span=70,
         palm_up=False, confidence=1., index_pinch=None):
    p = np.array([float(x),float(y)])
    return Hand(side,p,p.copy(),span,seal,open_palm,pinch=pinch,palm_up=palm_up,
                confidence=confidence,aim=np.array([1.,0.]),index_pinch=index_pinch)


class TechniqueTests(unittest.TestCase):
    def setUp(self):
        self.s,self.t = Technique(),0.

    def run_for(self,duration,hands,fps=60):
        for _ in range(round(duration*fps)):
            self.t += 1/fps
            self.s.update(hands,self.t)

    def summon_both(self):
        self.run_for(.6,[hand('Left',x=200,palm_up=True),hand(x=800,seal=True)])

    def purple(self):
        self.summon_both()
        self.run_for(.8,[hand('Left',x=450),hand(x=500)])
        self.assertEqual(self.s.phase,'fusion')
        self.run_for(1.1,[hand('Left',x=450),hand(x=500)])
        self.assertEqual(self.s.phase,'purple')
        self.run_for(1.,[hand(x=500)])

    def test_brief_gesture_does_not_summon(self):
        self.run_for(.15,[hand(seal=True)])
        self.run_for(.3,[hand()])
        self.assertFalse(self.s.energy['Right'].active)

    def test_blue_requires_upward_palm_not_two_fingers(self):
        self.run_for(.6,[hand('Left',seal=True)])
        self.assertFalse(self.s.energy['Left'].active)
        self.run_for(.6,[hand('Left',open_palm=True)])
        self.assertFalse(self.s.energy['Left'].active)
        self.run_for(.6,[hand('Left',open_palm=True,palm_up=True)])
        self.assertTrue(self.s.energy['Left'].active)

    def test_red_keeps_two_finger_gesture(self):
        self.run_for(.6,[hand(palm_up=True,open_palm=True)])
        self.assertFalse(self.s.energy['Right'].active)
        self.run_for(.6,[hand(seal=True)])
        self.assertTrue(self.s.energy['Right'].active)

    def test_summon_then_release_persists(self):
        self.run_for(.6,[hand(seal=True)])
        self.run_for(1.,[hand(x=400)])
        self.assertTrue(self.s.energy['Right'].active)
        self.assertAlmostEqual(self.s.energy['Right'].position[0],400,delta=1)

    def test_missing_hand_grace_then_expires(self):
        self.run_for(.6,[hand(seal=True)])
        self.run_for(.5,[])
        self.assertTrue(self.s.energy['Right'].active)
        self.run_for(3.,[])
        self.assertFalse(self.s.energy['Right'].active)

    def test_missing_hand_cannot_fuse(self):
        self.summon_both()
        self.run_for(1.,[hand(x=200)])
        self.assertEqual(self.s.phase,'summon')

    def test_complete_sequence_with_flick(self):
        self.purple()
        self.run_for(.4,[hand(x=500,pinch=.2)])
        self.assertTrue(self.s.pinch_armed)
        self.run_for(.10,[hand(x=500,pinch=1.2)])
        self.assertEqual(self.s.phase,'flight')
        self.assertEqual(self.s.projectiles[-1].kind,'Purple')
        self.run_for(2.,[])
        self.assertEqual(self.s.phase,'summon')
        self.assertFalse(any(e.active for e in self.s.energy.values()))

    def test_red_fires_while_blue_stays_held(self):
        self.summon_both()
        self.run_for(1.,[hand('Left',x=200),hand(x=800)])
        self.run_for(.4,[hand('Left',x=200),hand(x=800,pinch=.2)])
        self.run_for(.1,[hand('Left',x=200),hand(x=800,pinch=1.2)])
        self.assertEqual(self.s.projectiles[-1].kind,'Right')
        self.assertTrue(self.s.energy['Left'].active)
        self.assertFalse(self.s.energy['Right'].active)

    def test_blue_fires_independently(self):
        self.run_for(.6,[hand('Left',palm_up=True)])
        self.run_for(1.,[hand('Left')])
        self.run_for(.4,[hand('Left',pinch=.2)])
        self.run_for(.1,[hand('Left',pinch=1.2)])
        self.assertEqual(self.s.projectiles[-1].kind,'Left')
        self.assertEqual(self.s.phase,'summon')

    def test_hold_palm_after_launch_does_not_resummon(self):
        self.run_for(.6,[hand('Left',palm_up=True)])
        self.s.launch('Left',self.t)
        self.run_for(2.,[hand('Left',palm_up=True)])
        self.assertFalse(self.s.energy['Left'].active)
        self.run_for(.1,[hand('Left')])
        self.run_for(.6,[hand('Left',palm_up=True)])
        self.assertTrue(self.s.energy['Left'].active)

    def test_slow_release_does_not_throw(self):
        self.purple()
        self.run_for(.4,[hand(x=500,pinch=.2)])
        self.run_for(.5,[hand(x=500,pinch=.6)])
        self.run_for(.1,[hand(x=500,pinch=1.2)])
        self.assertEqual(self.s.phase,'purple')

    def test_lost_tracking_does_not_flick(self):
        self.purple()
        self.run_for(.4,[hand(x=500,pinch=.2)])
        self.run_for(.05,[])
        self.run_for(.1,[hand(x=800,pinch=1.2,open_palm=True)])
        self.assertEqual(self.s.phase,'purple')

    def test_open_palm_motion_and_depth_change_do_not_throw(self):
        self.purple()
        for k in range(30):
            self.run_for(1/60,[hand(x=500+k*15,span=70+k*4,open_palm=True)])
        self.assertEqual(self.s.phase,'purple')
        self.assertFalse(self.s.pinch_armed)

    def test_stationary_open_palm_does_not_throw(self):
        self.purple()
        self.run_for(1.,[hand(x=500,open_palm=True)])
        self.assertEqual(self.s.phase,'purple')

    def test_owner_transfer_cancels_armed_flick(self):
        self.purple()
        self.run_for(.4,[hand(x=500,pinch=.2)])
        self.run_for(1.,[hand('Left',x=200,open_palm=True)])
        self.assertEqual(self.s.owner,'Left')
        self.assertEqual(self.s.phase,'purple')
        self.assertFalse(self.s.pinch_armed)

    def test_duplicate_side_cannot_fake_two_hands(self):
        self.run_for(1.,[hand(seal=True),hand(seal=True)])
        self.assertEqual(self.s.phase,'summon')
        self.assertEqual(len(self.s.hands),1)

    def test_fusion_cancels_individual_throws(self):
        self.summon_both()
        self.run_for(1.,[hand('Left',x=200),hand(x=800)])
        self.run_for(.4,[hand('Left',x=200,pinch=.2),hand(x=800,pinch=.2)])
        self.assertTrue(self.s.energy['Right'].flick.armed)
        self.run_for(.8,[hand('Left',x=450),hand(x=500)])
        self.assertEqual(self.s.phase,'fusion')
        self.assertEqual(len(self.s.projectiles),0)

    def test_debounce_consistent_at_different_frame_rates(self):
        for fps in (15,30,60):
            self.s.reset()
            self.run_for(.6,[hand(seal=True)],fps)
            self.assertTrue(self.s.energy['Right'].active)


class FlickTests(unittest.TestCase):
    def setUp(self):
        self.f,self.t,self.shots = FlickGate(),0.,0

    def feed(self,duration,pinch,**kwargs):
        for _ in range(round(duration*60)):
            self.t += 1/60
            self.shots += self.f.update(hand(pinch=pinch,**kwargs),self.t)

    def arm(self):
        self.feed(.2,1.5)
        self.feed(.4,.2)
        self.assertTrue(self.f.armed)

    def test_no_initial_pinch_then_release_shortcut(self):
        self.feed(.5,.2)
        self.feed(.15,1.5)
        self.assertEqual(self.shots,0)

    def test_single_bad_frame_does_not_fire(self):
        self.arm()
        self.feed(1/60,1.6)
        self.feed(.1,.2)
        self.assertEqual(self.shots,0)
        self.assertTrue(self.f.armed)

    def test_short_pinch_does_not_arm(self):
        self.feed(.2,1.5)
        self.feed(.15,.2)
        self.feed(.2,1.5)
        self.assertEqual(self.shots,0)

    def test_long_hold_expires(self):
        self.arm()
        self.feed(3.2,.2)
        self.feed(.2,1.5)
        self.assertEqual(self.shots,0)

    def test_low_confidence_cancels(self):
        self.arm()
        self.feed(.1,1.5,confidence=.4)
        self.feed(.1,1.5)
        self.assertEqual(self.shots,0)

    def test_frame_stall_cancels(self):
        self.arm()
        self.t += .5
        self.feed(.2,1.5)
        self.assertEqual(self.shots,0)

    def test_jump_cancels(self):
        self.arm()
        self.feed(.2,1.5,x=1200)
        self.assertEqual(self.shots,0)

    def test_jitter_without_pinch_never_fires(self):
        rng = np.random.default_rng(123)
        for _ in range(600):
            self.feed(1/60,rng.uniform(.5,1.8))
        self.assertEqual(self.shots,0)

    def test_flick_across_frame_rates(self):
        for fps in (15,24,30,60):
            f,t,shots = FlickGate(),0.,0
            for duration,pinch in ((.3,1.5),(.5,.2),(.15,1.5),(.3,1.5)):
                for _ in range(round(duration*fps)):
                    t += 1/fps
                    shots += f.update(hand(pinch=pinch),t)
            self.assertEqual(shots,1,f'fps={fps}')

    def test_light_middle_tip_contact_arms_and_releases(self):
        self.feed(.2,1.2)
        self.feed(.34,.50)
        self.assertTrue(self.f.armed)
        self.feed(.10,.84)
        self.assertEqual(self.shots,1)

    def test_index_thumb_ok_gesture_works(self):
        self.feed(.2,1.5,index_pinch=1.2)
        self.feed(.34,1.5,index_pinch=.5)
        self.assertTrue(self.f.armed)
        self.feed(.1,1.5,index_pinch=.84)
        self.assertEqual(self.shots,1)

    def test_other_finger_does_not_trigger_a_held_index_pinch(self):
        self.feed(.2,1.2,index_pinch=1.2)
        self.feed(.34,.6,index_pinch=.5)
        self.feed(.1,1.5,index_pinch=.5)
        self.assertEqual(self.shots,0)
        self.assertTrue(self.f.armed)

    def test_light_contact_jitter_does_not_count_as_release(self):
        self.feed(.2,1.2)
        self.feed(.34,.5)
        for gap in (.57,.46,.59,.53,.61,.49):
            self.feed(.05,gap)
        self.assertEqual(self.shots,0)
        self.feed(.1,.9)
        self.assertEqual(self.shots,1)

    def test_slow_light_contact_release_is_cancelled(self):
        self.feed(.2,1.2)
        self.feed(.34,.5)
        self.feed(.5,.68)
        self.feed(.1,.9)
        self.assertEqual(self.shots,0)

    def test_lost_index_measurement_cancels_index_pinch(self):
        self.feed(.2,1.2,index_pinch=1.2)
        self.feed(.34,1.2,index_pinch=.5)
        self.feed(.05,1.2)
        self.feed(.1,1.2,index_pinch=.9)
        self.assertEqual(self.shots,0)

    def test_light_contact_with_both_fingers_only_fires_once(self):
        self.feed(.2,1.2,index_pinch=1.2)
        self.feed(.34,.5,index_pinch=.5)
        self.feed(.1,.9,index_pinch=.9)
        self.assertEqual(self.shots,1)


class GeometryTests(unittest.TestCase):
    def points(self):
        p = np.zeros((21,2))
        p[0] = [0,120]
        for i,xy in {5:(-30,40),6:(-30,0),8:(-25,-65),9:(0,35),10:(0,-5),
                     12:(-2,-72),13:(30,40),14:(30,0),16:(28,65),
                     17:(55,50),18:(55,20),20:(50,80),4:(-60,40)}.items():
            p[i] = xy
        return p

    def test_seal_rotation_and_scale_invariant(self):
        for angle in (0.,.5,1.6,3.1):
            r = np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]])
            self.assertTrue(classify(self.points()@r*1.7+[500,300],'Right').seal)

    def test_spread_v_sign_is_rejected(self):
        p = self.points()
        p[8],p[12] = [-85,-65],[30,-72]
        self.assertFalse(classify(p,'Right').seal)

    def test_open_hand_is_not_seal(self):
        p = self.points()
        p[16],p[20] = [30,-60],[55,-45]
        result = classify(p,'Left')
        self.assertTrue(result.open_palm)
        self.assertFalse(result.seal)

    def test_middle_thumb_pinch(self):
        p = self.points()
        p[4] = p[12]+[3,3]
        self.assertLess(classify(p,'Right').pinch,.1)

    def test_light_surface_contact_tolerates_small_depth_error(self):
        g,p = np.zeros((21,3)),np.zeros((21,2))
        g[12],p[12] = [.012,0,.030],[5,0]
        self.assertGreater(np.linalg.norm(g[12])/.05,.55)
        self.assertLess(fingertip_gap(g,p,12,.05,50),.55)

    def test_screen_overlap_cannot_hide_large_depth_gap(self):
        g,p = np.zeros((21,3)),np.zeros((21,2))
        g[8] = [0,0,.055]
        self.assertGreater(fingertip_gap(g,p,8,.05,50),1.)

    def world_hand(self,side,angle):
        p = self.points()
        p[16],p[20] = [30,-60],[55,-45]
        world = np.column_stack((p,np.zeros(21)))*.001
        if side == 'Left':
            world[:,0] *= -1
        c,s = np.cos(angle),np.sin(angle)
        rotation = np.array([[1,0,0],[0,c,-s],[0,s,c]])
        return world@rotation.T

    def test_upward_palm_detected_for_both_handedness(self):
        for side in ('Left','Right'):
            for angle in (-np.pi/2,-np.pi/3):
                world = self.world_hand(side,angle)
                pixels = world[:,:2]*1000+[500,350]
                h = classify(pixels,side,world=world)
                self.assertTrue(h.open_palm)
                self.assertTrue(h.palm_up)

    def test_front_and_downward_palm_do_not_summon_blue(self):
        for angle in (0,np.pi/2):
            world = self.world_hand('Left',angle)
            h = classify(world[:,:2]*1000+[500,350],'Left',world=world)
            self.assertFalse(h.palm_up)

    def test_pinch_uses_depth_not_projected_overlap(self):
        world = self.world_hand('Left',-np.pi/2)
        world[4] = world[12]+[0,0,.07]
        h = classify(world[:,:2]*1000+[500,350],'Left',world=world)
        self.assertGreater(h.pinch,.7)


class TrajectoryTests(unittest.TestCase):
    def projectile(self,kind):
        return Projectile(kind,np.array([300.,350.]),np.array([1.,0.]),0,70,
                          np.array([640.,400.]),5.2 if kind=='Left' else 1.25)

    def test_red_is_straight_and_moves_forward(self):
        p = self.projectile('Right')
        points = np.array([p.sample(t,(1280,720))[0] for t in (.1,.3,.5)])
        self.assertTrue(np.allclose(points[:,1],350))
        self.assertTrue(np.all(np.diff(points[:,0])>0))

    def test_blue_goes_around_both_sides(self):
        p = self.projectile('Left')
        points = np.array([p.sample(t,(1280,720))[0] for t in np.linspace(.4,4.8,80)])
        self.assertLess(points[:,0].min(),400)
        self.assertGreater(points[:,0].max(),880)
        self.assertGreater(np.ptp(points[:,1]),150)

    def test_projectiles_start_at_the_hand(self):
        for kind in ('Left','Right','Purple'):
            p = self.projectile(kind)
            self.assertTrue(np.allclose(p.sample(0,(1280,720))[0],p.origin))


if __name__ == '__main__':
    unittest.main()
