"""Geometry only: independent from camera, renderer and MediaPipe runtime."""
from dataclasses import dataclass
import numpy as np


@dataclass
class Hand:
    side: str
    palm: np.ndarray
    anchor: np.ndarray
    span: float
    seal: bool = False
    open_palm: bool = False
    points: np.ndarray | None = None
    confidence: float = 1.0
    pinch: float = 2.0
    palm_up: bool = False
    aim: np.ndarray | None = None
    index_pinch: float | None = None
    crossed: bool = False


def crossed_fingers(p, g, width):
    """Recognize tip reversal OR crossing finger segments in a palm-local frame.

    A bent middle finger often crosses the index at the DIP joint while its tip
    returns to its original side. Tip ordering alone misses that natural pose.
    """
    across = p[9] - p[5]
    base = float(np.linalg.norm(across))
    if base < width*.08:
        return False
    across /= base
    up = (p[5]+p[9])*.5-p[0]
    up /= max(float(np.linalg.norm(up)),1.)
    raised = all(np.dot(p[tip]-p[mcp],up) > width*.25
                 and max(np.dot(p[j]-p[mcp],up) for j in range(mcp+1,tip+1)) > width*.48
                 for mcp,tip in ((5,8),(9,12)))
    reversed_tips = np.dot(p[12]-p[8],across) < -width*.018
    close = np.linalg.norm(p[8]-p[12]) < width*1.15
    curled = not extended(g,13,14,16) and not extended(g,17,18,20)
    if not (raised and close and curled):
        return False
    if reversed_tips:
        return True
    origin = (p[5]+p[9])*.5
    # Strict interior intersection: mere touching/parallel two-finger seals
    # must continue to summon red. Ignore crossings down inside the palm.
    def cross(a,b):
        return a[0]*b[1]-a[1]*b[0]
    for i in (5,6,7):
        for j in (9,10,11):
            a,b,c,d=p[i],p[i+1],p[j],p[j+1]
            u,v=b-a,d-c
            denominator=cross(u,v)
            if abs(denominator) < width*width*.004:
                continue
            t,s=cross(c-a,v)/denominator,cross(c-a,u)/denominator
            if .04 < t < .96 and .04 < s < .96:
                intersection=a+t*u
                if np.dot(intersection-origin,up) > width*.25:
                    return True
    return False


def fingertip_gap(g, p, tip, width, projected_width):
    """Allow bounded depth-estimation error without treating projected overlap as contact."""
    spatial = float(np.linalg.norm(g[4] - g[tip]) / width)
    projected = float(np.linalg.norm(p[4] - p[tip]) / projected_width)
    if spatial < .75 and projected < .45:
        return min(spatial, max(projected, spatial - .12))
    return spatial


def extended(p: np.ndarray, mcp: int, pip: int, tip: int) -> bool:
    a, b = p[mcp] - p[pip], p[tip] - p[pip]
    cosine = np.dot(a, b) / max(np.linalg.norm(a) * np.linalg.norm(b), 1e-6)
    return bool(cosine < -0.65 and np.linalg.norm(p[tip] - p[0]) >
                np.linalg.norm(p[pip] - p[0]) * 1.10)


def classify(points: np.ndarray, side: str, confidence: float = 1.0,
             world: np.ndarray | None = None) -> Hand:
    p = np.asarray(points, dtype=float)[:, :2]
    # World geometry stays usable when a horizontal palm is nearly edge-on.
    g = np.asarray(world, dtype=float) if world is not None else p
    width = max(float(np.linalg.norm(g[5] - g[17])), 1e-6)
    span = max(float(np.linalg.norm(p[5] - p[17])),
               float(np.linalg.norm(p[0] - p[9])) * .75, 15.0)
    fingers = [extended(g, *ids) for ids in [(5, 6, 8), (9, 10, 12),
                                            (13, 14, 16), (17, 18, 20)]]
    crossed = crossed_fingers(p,g,span)
    # Rotation independent; thumb position is deliberately unrestricted.
    close = np.linalg.norm(g[8] - g[12]) < width * 0.65
    seal = fingers[0] and fingers[1] and not fingers[2] and not fingers[3] and close and not crossed
    palm = np.mean(p[[0, 5, 9, 13, 17]], axis=0)
    tip = (p[8] + p[12]) * 0.5
    direction = tip - palm
    direction /= max(float(np.linalg.norm(direction)), 1.0)
    open_palm = sum(fingers) >= 3 and fingers[0] and fingers[1]
    palm_up = False
    if world is not None:
        normal = np.cross(g[5] - g[0], g[17] - g[0])
        normal *= -1 if side == 'Right' else 1
        normal /= max(float(np.linalg.norm(normal)), 1e-8)
        # Image/world y points down. Permit a comfortably tilted open palm.
        palm_up = bool(open_palm and normal[1] < -.38)
    anchor = tip + direction * span * .45 if seal else palm.copy()
    if side == 'Left':
        anchor = palm + [0, -span * .75]
    aim = p[8] - p[5]
    aim /= max(float(np.linalg.norm(aim)), 1.)
    projected_width = max(float(np.linalg.norm(p[5] - p[17])), span, 1.)
    pinch = fingertip_gap(g, p, 12, width, projected_width)
    index_pinch = fingertip_gap(g, p, 8, width, projected_width)
    return Hand(side, palm, anchor, span, bool(seal), bool(open_palm), p,
                confidence, pinch, palm_up, aim, index_pinch, crossed)
