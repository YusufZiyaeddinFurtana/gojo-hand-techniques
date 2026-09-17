import unittest
import numpy as np
from gojo.effects import Renderer
from gojo.engine import Technique
from gojo.demo import demo_frame


class RenderingTests(unittest.TestCase):
    def test_idle_canvas_has_no_text_panels_or_tint(self):
        frame = np.random.default_rng(1).integers(0,256,(360,640,3),dtype=np.uint8)
        out = Renderer().render(frame,Technique(),0)
        np.testing.assert_array_equal(out,frame)

    def test_overlapping_orbs_do_not_cut_dark_lines_into_each_other(self):
        renderer = Renderer()
        layer = np.zeros((360,640,3),np.uint8)
        renderer.orb(layer,np.array([300.,180.]),60,'Left',.6)
        blue = layer.copy()
        renderer.orb(layer,np.array([350.,180.]),60,'Right',.6)
        self.assertTrue(np.all(layer>=blue))

    def test_demo_exercises_every_color_and_full_fusion_cycle(self):
        state = Technique()
        phases,shots = set(),[]
        for n in range(540):
            _,hands = demo_frame(n/30,640,360)
            state.viewport = (640,360)
            state.update(hands,n/30)
            phases.add(state.phase)
            shots.extend(kind for event,_,kind in state.events if event=='launch')
        self.assertEqual(shots,['Right','Left','Purple'])
        self.assertEqual(phases,{'summon','fusion','purple','flight','cooldown'})
