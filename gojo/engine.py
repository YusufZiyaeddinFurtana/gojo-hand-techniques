"""Time-based techniques and conservative, per-hand flick recognition."""
from dataclasses import dataclass, field
import math
import numpy as np
from .gestures import Hand
from .domain import Domain


@dataclass
class PinchChannel:
    """Fresh open -> sustained pinch -> confirmed fast release; never motion alone."""
    HOLD_SECONDS = .28
    neutral: float = 0.
    holding: float = 0.
    armed: bool = False
    closed_at: float = -100.
    armed_at: float = -100.
    release_time: float = 0.
    release_frames: int = 0
    last_time: float | None = None
    last_palm: np.ndarray | None = None
    minimum: float = 1.
    contact_level: float = 0.
    maximum: float = 0.

    def cancel(self):
        self.neutral = self.holding = self.release_time = 0.
        self.release_frames = 0
        self.armed = False
        self.closed_at = self.armed_at = -100.
        self.last_time = self.last_palm = None
        self.minimum = 1.
        self.maximum = self.contact_level = 0.

    def update(self, hand, now, enabled=True, gap=None):
        if not enabled or hand is None or hand.confidence < .6:
            self.cancel()
            return False
        pinch = hand.pinch if gap is None else gap
        if not math.isfinite(pinch):
            self.cancel()
            return False
        dt = 0. if self.last_time is None else now - self.last_time
        jump = self.last_palm is not None and np.linalg.norm(hand.palm-self.last_palm) > hand.span*2.
        if dt > .20 or dt < 0 or jump:
            self.cancel()
            dt = 0.
        self.last_time, self.last_palm = now, hand.palm.copy()
        if self.armed:
            if now - self.armed_at > 3.:
                self.cancel()
                return False
            # The held contact defines the release, not how hard the tips are pressed.
            if pinch < min(.65, self.contact_level + .12):
                self.closed_at = now
                self.release_time = 0.
                self.release_frames = 0
                return False
            if now - self.closed_at > .38:
                self.cancel()
                return False
            threshold = max(.64, self.contact_level + .30)
            if pinch >= threshold:
                self.release_time += min(dt, .08)
                self.release_frames += 1
                if self.release_time >= .05 and self.release_frames >= 2:
                    self.cancel()
                    return True
            else:
                self.release_time = 0.
                self.release_frames = 0
            return False
        if self.neutral < .12:
            self.neutral = self.neutral + min(dt, .08) if pinch > .72 else 0.
            return False
        if pinch < .55:
            if self.holding == 0.:
                self.contact_level = self.minimum = self.maximum = pinch
            self.minimum = min(self.minimum, pinch)
            self.maximum = max(self.maximum, pinch)
            if self.maximum - self.minimum > .18:
                self.holding = 0.
                self.contact_level = self.minimum = self.maximum = pinch
            self.holding += min(dt, .08)
            self.contact_level += (pinch-self.contact_level) * .25
            self.closed_at = now
            if self.holding >= self.HOLD_SECONDS:
                self.armed = True
                self.armed_at = self.closed_at = now
        elif pinch > .63 or now-self.closed_at > .10:
            self.holding = 0.
            self.minimum = 1.
        return False


@dataclass
class FlickGate:
    """Separate finger channels prevent a different finger's opening from firing."""
    HOLD_SECONDS = PinchChannel.HOLD_SECONDS
    middle: PinchChannel = field(default_factory=PinchChannel)
    index: PinchChannel = field(default_factory=PinchChannel)

    @property
    def armed(self):
        return self.middle.armed or self.index.armed

    @property
    def holding(self):
        return max(self.middle.holding, self.index.holding)

    def cancel(self):
        self.middle.cancel()
        self.index.cancel()

    def update(self, hand, now, enabled=True):
        middle_fired = self.middle.update(hand, now, enabled)
        index_fired = False
        if hand is not None and hand.index_pinch is not None:
            index_fired = self.index.update(hand, now, enabled, gap=hand.index_pinch)
        else:
            self.index.cancel()
        if middle_fired or index_fired:
            self.cancel()
            return True
        return False


@dataclass
class Energy:
    side: str
    active: bool = False
    progress: float = 0.
    position: np.ndarray = field(default_factory=lambda: np.zeros(2))
    span: float = 65.
    last_seen: float = -100.
    created: float = -100.
    cooldown: float = -100.
    needs_neutral: bool = False
    flick: FlickGate = field(default_factory=FlickGate)


@dataclass
class Projectile:
    kind: str
    origin: np.ndarray
    direction: np.ndarray
    started: float
    span: float
    orbit_center: np.ndarray
    duration: float

    def sample(self, now, viewport):
        """Return position, perspective and opacity (also used by trails)."""
        w, h = viewport
        elapsed = max(0., now-self.started)
        p = min(1., elapsed/self.duration)
        fade = min(1., p*12+.2, (1-p)*6)
        if self.kind == 'Left':
            angle0 = math.atan2((self.origin[1]-self.orbit_center[1])/.48,
                               self.origin[0]-self.orbit_center[0])
            angle = angle0 + elapsed*3.5
            rx = w*(.19+.10*math.sin(p*math.pi))
            ry = h*(.16+.05*math.sin(p*math.pi))
            orbit = self.orbit_center + [math.cos(angle)*rx,
                                        math.sin(angle)*ry - p*h*.15]
            blend = 1-math.exp(-elapsed*7)
            center = self.origin*(1-blend)+orbit*blend
            depth = .80+.25*math.sin(angle)
            return center, depth, fade*(.65+.35*max(0.,math.sin(angle)))
        if self.kind == 'Right':
            center = self.origin + self.direction * (p+p*p*.6)*max(w,h)*1.2
            return center, 1.-p*.45, fade
        center = self.origin + (np.array([w*.5,h*.48])-self.origin)*p
        return center, 1.+p*p*4., fade


class Technique:
    def __init__(self):
        self.viewport = (1280, 720)
        self.reset()

    def reset(self):
        self.energy = {s: Energy(s) for s in ('Left', 'Right')}
        self.phase, self.phase_start = 'summon', 0.
        self.merge_progress = 0.
        self.purple = np.zeros(2)
        self.purple_span = 70.
        self.owner = 'Right'
        self.previous_time = None
        self.events = []
        self.hands = {}
        self.projectiles = []
        self.purple_last_seen = -100.
        self.purple_flick = FlickGate()
        self.body_center = np.array(self.viewport, dtype=float)*[.5,.57]
        self.domain = Domain()

    @property
    def pinch_armed(self):
        return self.purple_flick.armed

    def launch(self, kind, now, hand=None):
        if kind == 'Purple':
            if self.phase != 'purple':
                return
            origin, span = self.purple.copy(), self.purple_span
            self.phase, self.phase_start = 'flight', now
            self.purple_flick.cancel()
        else:
            e = self.energy[kind]
            if not e.active or self.phase != 'summon':
                return
            origin, span = e.position.copy(), e.span
            e.active, e.progress = False, 0.
            e.cooldown, e.needs_neutral = now+1., True
            e.flick.cancel()
        aim = hand.aim if hand is not None and hand.aim is not None else np.array([.6,-.8])
        direction = np.array(aim, dtype=float)
        if np.linalg.norm(direction) < .25:
            direction = np.array([.6,-.8])
        direction /= np.linalg.norm(direction)
        duration = {'Left': 5.2, 'Right': 1.25, 'Purple': 1.25}[kind]
        self.projectiles.append(Projectile(kind, origin, direction, now, span,
                                           self.body_center.copy(), duration))
        self.projectiles = self.projectiles[-8:]
        self.events.append(('launch', origin, kind))

    def update(self, hands: list[Hand], now: float):
        dt = 0. if self.previous_time is None else max(0., min(now-self.previous_time,.1))
        interrupted = self.previous_time is not None and now-self.previous_time > .20
        self.previous_time = now
        self.events = []
        self.hands = {}
        self.projectiles = [p for p in self.projectiles if now-p.started < p.duration]
        for hand in hands:
            if hand.side not in self.hands or hand.confidence > self.hands[hand.side].confidence:
                self.hands[hand.side] = hand
        self.domain.update(self.hands,now)
        if len(self.hands) == 2:
            midpoint = np.mean([hand.palm for hand in self.hands.values()], axis=0)
            w,h = self.viewport
            target = np.clip(midpoint+[0,h*.12], [w*.25,h*.40], [w*.75,h*.70])
            self.body_center += (target-self.body_center)*(1-math.exp(-dt*2.))
        if interrupted:
            self.purple_flick.cancel()
            self.merge_progress = 0.
            for e in self.energy.values():
                e.flick.cancel()
                e.progress = 0.
        for side,e in self.energy.items():
            hand = self.hands.get(side)
            if hand is None:
                e.progress = 0.
                e.flick.cancel()
                if now-e.last_seen > 3.:
                    e.active = False
                continue
            reacquired = now-e.last_seen > .3
            e.last_seen = now
            a = 1. if reacquired else 1-math.exp(-dt*18)
            e.position += (hand.anchor-e.position)*a
            e.span += (hand.span-e.span)*a
            summon_pose = (hand.palm_up if side == 'Left' else hand.seal) and not hand.crossed
            if not summon_pose:
                e.needs_neutral = False
            if self.phase == 'summon' and not e.active:
                allowed = not e.needs_neutral and now > e.cooldown and hand.confidence >= .6
                e.progress = min(1.,e.progress+dt/.38) if summon_pose and allowed else 0.
                if e.progress >= 1.:
                    e.active, e.created = True, now
                    e.flick.cancel()
                    self.events.append(('summon', e.position.copy(), side))

        if self.phase == 'summon':
            left,right = self.energy['Left'],self.energy['Right']
            both = left.active and right.active and len(self.hands) == 2
            close = both and np.linalg.norm(left.position-right.position) < (left.span+right.span)*1.
            # Fusion takes priority over flicks made while bringing hands together.
            self.merge_progress = min(1.,self.merge_progress+dt/.4) if close else 0.
            for side,e in self.energy.items():
                hand = self.hands.get(side)
                allowed = e.active and now-e.created > .55 and not close and hand is not None and not hand.crossed
                if e.flick.update(self.hands.get(side), now, allowed):
                    self.launch(side, now, self.hands[side])
            if self.merge_progress >= 1.:
                self.phase,self.phase_start = 'fusion',now
                self.purple = (left.position+right.position)*.5
                self.purple_span = (left.span+right.span)*.5
                self.purple_flick.cancel()
                self.events.append(('fusion',self.purple.copy(),'Purple'))
        elif self.phase == 'fusion':
            if len(self.hands) == 2:
                target = np.mean([e.position for e in self.energy.values()],axis=0)
                self.purple += (target-self.purple)*(1-math.exp(-dt*8))
            if now-self.phase_start >= 1.:
                self.phase,self.phase_start = 'purple',now
                self.owner = 'Right' if 'Right' in self.hands else 'Left'
                self.purple_last_seen = now
                self.purple_flick.cancel()
                for e in self.energy.values():
                    e.active,e.progress = False,0.
                    e.flick.cancel()
        elif self.phase == 'purple':
            hand = self.hands.get(self.owner)
            if hand is None and now-self.purple_last_seen > .65 and self.hands:
                self.owner = next(iter(self.hands))
                hand = self.hands[self.owner]
                self.purple_flick.cancel()
            if hand:
                self.purple_last_seen = now
                self.purple += (hand.palm-self.purple)*(1-math.exp(-dt*22))
                self.purple_span += (hand.span-self.purple_span)*(1-math.exp(-dt*10))
                if self.purple_flick.update(hand,now, now-self.phase_start > .55 and not hand.crossed):
                    self.launch('Purple',now,hand)
            else:
                self.purple_flick.cancel()
                if now-self.purple_last_seen > 3.:
                    self.phase,self.phase_start = 'cooldown',now
        elif self.phase == 'flight' and now-self.phase_start >= 1.25:
            self.phase,self.phase_start = 'cooldown',now
        elif self.phase == 'cooldown' and now-self.phase_start >= .6:
            self.phase,self.phase_start = 'summon',now
            for e in self.energy.values():
                e.active,e.progress,e.needs_neutral = False,0.,True
                e.flick.cancel()

    def visibility(self, side, now):
        return float(np.clip(1-(now-self.energy[side].last_seen-.2)/.6,0,1))
