"""Independent domain timer, debounced per hand; no camera/renderer dependencies."""
from dataclasses import dataclass, field


@dataclass
class Domain:
    duration: float = 12.
    started: float | None = None
    hold: dict = field(default_factory=lambda: {'Left':0.,'Right':0.})
    miss: dict = field(default_factory=lambda: {'Left':0.,'Right':0.})
    latched: bool = False
    release_time: float = 0.
    previous_time: float | None = None

    def active(self, now):
        return self.started is not None and 0 <= now-self.started < self.duration

    def strength(self, now):
        if not self.active(now):
            return 0.
        age = now-self.started
        x = min(1.,age/.85,(self.duration-age)/1.25)
        return x*x*(3-2*x)

    def update(self, hands, now):
        elapsed = 0. if self.previous_time is None else now-self.previous_time
        self.previous_time = now
        if elapsed > .2 or elapsed < 0:
            self.hold = dict.fromkeys(self.hold,0.)
            self.miss = dict.fromkeys(self.miss,0.)
            self.release_time = 0.
            elapsed = 0.
        dt = min(elapsed,.1)
        if self.active(now):
            self.hold = dict.fromkeys(self.hold,0.)
            return False
        if self.latched:
            released = bool(hands) and all(not h.crossed and h.confidence >= .6 for h in hands.values())
            self.release_time = self.release_time+dt if released else 0.
            if self.release_time >= .25 and now-self.started >= self.duration+1.:
                self.latched = False
            return False
        for side in self.hold:
            hand = hands.get(side)
            valid = hand is not None and hand.crossed and hand.confidence >= .6
            if valid:
                self.miss[side] = 0.
                self.hold[side] += dt
            elif hand is None or hand.confidence < .6:
                self.hold[side] = self.miss[side] = 0.
            else:
                self.miss[side] += dt
                self.hold[side] = (max(0.,self.hold[side]-.5*dt)
                                   if self.miss[side] <= .14 else 0.)
            if valid and self.hold[side] >= .52:
                self.started,self.latched,self.release_time = now,True,0.
                self.hold = dict.fromkeys(self.hold,0.)
                return True
        return False
