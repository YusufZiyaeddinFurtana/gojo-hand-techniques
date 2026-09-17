"""18-second synthetic choreography, identified in the CLI and accompanying README."""
import math
import cv2
import numpy as np
from .gestures import Hand


def demo_frame(t, width=1280, height=720):
    frame = np.zeros((height,width,3),np.uint8)
    frame[:] = (22,18,18)
    phase = t % 18
    approach = np.clip((phase-11.4)/1.4,0,1)
    separation = (1-approach)*width*.25+width*.025
    hands = []
    for i,side in enumerate(('Left','Right')):
        center = np.array([width*.5+(-1 if i==0 else 1)*separation,
                           height*.53+math.sin(t*1.4+i)*5])
        span = height*.105
        pinch = 1.5
        if side == 'Right' and (1.8 < phase < 2.30 or 15.0 < phase < 15.55):
            pinch = .16
        if side == 'Left' and 3.2 < phase < 3.70:
            pinch = .16
        summon = phase < 1.5 or 10 < phase < 11.5
        hand = Hand(side,center,center.copy(),span,seal=summon and side=='Right',
                    open_palm=summon and side=='Left',pinch=pinch,
                    palm_up=summon and side=='Left',aim=np.array([.98,-.20]))
        hands.append(hand)
        # Simple calibration dots rather than a photographic person: this is simulated input.
        cv2.circle(frame,tuple(center.astype(int)),4,(84,70,65),-1,cv2.LINE_AA)
    return frame,hands if phase < 16.3 else []


def domain_demo_frame(t,width=1280,height=720):
    frame = np.full((height,width,3),(46,39,33),np.uint8)
    phase = t%16
    # Deliberately plain simulated stage. No person image or camera recording.
    p = np.array([width*.66,height*.5])
    hand = Hand('Right',p,p.copy(),height*.11,crossed=1.<phase<2.5)
    return frame,[hand]
