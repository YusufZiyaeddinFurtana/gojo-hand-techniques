"""Text-free procedural energy: attraction, repulsion and orbiting projectiles."""
from functools import lru_cache
import math
import cv2
import numpy as np
from .void_effect import VoidRenderer

COLORS = {'Left': (255, 145, 12), 'Right': (48, 24, 255), 'Purple': (255, 55, 174)}
WHITE = (255, 247, 250)
TAU = math.tau


def point(p):
    return tuple(np.clip(p, -20000, 20000).astype(int))


def tint(color, strength):
    return tuple(int(np.clip(c*strength, 0, 255)) for c in color)


@lru_cache(maxsize=48)
def light_sprite(radius, color):
    extent = radius * 3
    y, x = np.mgrid[-extent:extent+1, -extent:extent+1].astype(np.float32)
    r = np.sqrt(x*x+y*y)/radius
    halo = np.exp(-r*r*1.15)[..., None]*np.array(color, np.float32)
    core = np.exp(-r**4*13)[..., None]*np.array(WHITE, np.float32)
    corona = np.exp(-((r-.82)/.14)**2)[..., None]*np.array(color, np.float32)*.38
    return np.uint8(np.clip(halo*.90+core+corona, 0, 255))


def add_sprite(canvas, position, radius, color, alpha=1.):
    radius = int(np.clip(round(radius/4)*4, 8, 240))
    sprite = light_sprite(radius, color)
    extent = radius*3
    cx, cy = point(position)
    x0, y0 = cx-extent, cy-extent
    x1, y1 = x0+sprite.shape[1], y0+sprite.shape[0]
    h,w = canvas.shape[:2]
    a,b,c,d = max(0,x0),max(0,y0),min(w,x1),min(h,y1)
    if a >= c or b >= d:
        return
    roi = canvas[b:d,a:c]
    cv2.addWeighted(roi,1,sprite[b-y0:d-y0,a-x0:c-x0],float(alpha),0,dst=roi)


class Renderer:
    def __init__(self, reduced=False):
        self.reduced = reduced
        self.debug = False
        self.particles = []
        self.rng = np.random.default_rng(42)
        self.previous = None
        self.angle = np.linspace(0, TAU, 128)
        self.void = VoidRenderer()

    def field(self, layer, center, radius, kind, now, strength):
        """Blue pulls spiralling motes inward; red throws debris radially outward."""
        color = COLORS[kind]
        count = 26 if self.reduced else 90
        inward = kind == 'Left'
        for k in range(count):
            speed = .35+(k%7)*.045
            life = (now*speed+k*.6180339)%1.
            age = np.clip(life-np.linspace(.055,0,5), 0, 1)
            if inward:
                distance = 4.4-3.55*age**.72
                angle = k*2.39996 + age*2.8 + now*.18
            else:
                distance = .9+age**1.6*4.5
                angle = k*2.39996+np.sin(age*8+k)*.035
            positions = center + np.column_stack((np.cos(angle)*distance,
                                                   np.sin(angle)*distance*.76))*radius
            light = math.sin(life*math.pi)**.6*strength
            cv2.polylines(layer,[positions.astype(np.int32)],False,tint(color,light*.65),1,cv2.LINE_AA)
            p = point(positions[-1])
            cv2.circle(layer,p,1+(k%13==0),tint(WHITE if k%4==0 else color,light),-1,cv2.LINE_AA)
        if self.reduced:
            return
        if inward:
            # Long curved streamlines show the direction of the force even in a still frame.
            for k in range(5):
                u = np.linspace(0,1,80)
                a = k*TAU/5 + u*2.4 + now*.5
                r = radius*(3.4-2.3*u)
                pts = center+np.column_stack((np.cos(a)*r,np.sin(a)*r*.7))
                cv2.polylines(layer,[pts.astype(np.int32)],False,tint(color,.16*strength),1,cv2.LINE_AA)
        else:
            for k in range(2):
                life = (now*.8+k*.5)%1
                theta = self.angle
                r = radius*(1.15+life*3.8)*(1+.025*np.sin(theta*9+now*4))
                pts = center+np.column_stack((np.cos(theta)*r,np.sin(theta)*r*.74))
                cv2.polylines(layer,[pts.astype(np.int32)],True,
                              tint(color,(1-life)**2*.45*strength),1,cv2.LINE_AA)

    def orb(self, layer, center, radius, kind, now, strength=1., ready=0., field=True):
        destination = layer
        layer = np.zeros_like(destination)
        color = COLORS[kind]
        radius *= 1+.025*math.sin(now*8)
        if field and kind != 'Purple':
            self.field(layer,center,radius,kind,now,strength)
        elif field and not self.reduced:
            self.field(layer,center,radius*.9,'Left',now,strength*.3)
            self.field(layer,center,radius*.9,'Right',now,strength*.3)
        # The filaments are outside the core: drawing them first avoids dark cuts into it.
        if not self.reduced:
            for k in range(5):
                theta = self.angle
                rough = .06*np.sin(theta*13+now*11+k)+.035*np.sin(theta*29-now*17)
                r = radius*(.94+k*.055+rough)
                a = theta+now*(.4+k*.14)
                pts = center+np.column_stack((np.cos(a)*r,np.sin(a)*r*(.73+k*.055)))
                cv2.polylines(layer,[pts.astype(np.int32)],True,tint(color,strength*.85),1,cv2.LINE_AA)
            # Branching electrical lashes; smooth time noise prevents random per-frame popping.
            for k in range(9):
                u = np.linspace(0,1,23)
                a = k*TAU/9+now*.35
                r = radius*(.90+u*(.8+.35*math.sin(k*7+now*2)))
                bend = np.sin(u*20+k*3+now*16)*u*.1
                pts = center+np.column_stack((np.cos(a+bend)*r,np.sin(a+bend)*r))
                cv2.polylines(layer,[pts.astype(np.int32)],False,
                              tint(color,(.35+.15*math.sin(now*13+k))*strength),1,cv2.LINE_AA)
        add_sprite(layer,center,radius,color,strength)
        if ready:
            # Diegetic readiness cue, no words or UI bars.
            rr = radius*(1.35+.07*math.sin(now*12))
            cv2.ellipse(layer,point(center),(int(rr),int(rr*.86)),now*70,0,325,
                        tint(WHITE,ready*strength),2,cv2.LINE_AA)
            add_sprite(layer,center,radius*.4,WHITE,ready*.22*strength)
        cv2.add(destination,layer,dst=destination)

    def burst(self, center, kind, count=70):
        color = COLORS[kind]
        for _ in range(count if not self.reduced else 10):
            a = self.rng.uniform(0,TAU)
            vel = np.array([math.cos(a),math.sin(a)])*self.rng.uniform(100,650)
            self.particles.append([center.copy(),vel,self.rng.uniform(.3,.8),color])
        self.particles = self.particles[-240:]

    def draw_projectile(self, layer, projectile, now, viewport):
        kind = projectile.kind
        color = COLORS[kind]
        center,depth,fade = projectile.sample(now,viewport)
        base = float(np.clip(projectile.span*.95,42,105))
        elapsed = now-projectile.started
        if kind in ('Left','Right'):
            trail_duration = .8 if kind == 'Left' else .18
            steps = 22 if not self.reduced else 8
            for i in range(steps,0,-1):
                age = i/steps*trail_duration
                if elapsed < age:
                    continue
                pos,d,f = projectile.sample(now-age,viewport)
                size = base*d*(1-i/(steps+3))*.60
                add_sprite(layer,pos,size,color,(1-i/(steps+1))*.24*fade)
            if kind == 'Left' and elapsed > .08:
                times = np.linspace(max(projectile.started,now-1.05),now,70)
                pts = np.array([projectile.sample(t,viewport)[0] for t in times])
                # A pair of thin helices follows the moving blue singularity.
                for k in (-1,1):
                    offset = np.column_stack((np.sin(times*23),np.cos(times*23)))*base*.16*k
                    cv2.polylines(layer,[(pts+offset).astype(np.int32)],False,tint(color,fade*.4),2,cv2.LINE_AA)
        elif not self.reduced:
            w,h = viewport
            progress = elapsed/projectile.duration
            for k in range(26):
                a = k*TAU/26+.06*math.sin(k*5)
                ray = np.array([math.cos(a),math.sin(a)])
                r = base*depth
                cv2.line(layer,point(center+ray*r*1.25),point(center+ray*r*(1.9+progress)),
                         tint(color,fade*.5),2,cv2.LINE_AA)
            cv2.circle(layer,point(projectile.origin),int(45+progress*max(w,h)),
                       tint(color,(1-progress)*.55),2,cv2.LINE_AA)
        self.orb(layer,center,base*depth,kind,now,fade,field=not self.reduced)

    def render(self, frame, state, now, fps=0, demo=False, swapped=False, person_mask=None):
        dt = .033 if self.previous is None else max(0,min(.1,now-self.previous))
        self.previous = now
        h,w = frame.shape[:2]
        has_energy = any(e.active for e in state.energy.values()) or state.projectiles or state.phase in ('fusion','purple')
        out = cv2.convertScaleAbs(frame,alpha=.91) if has_energy else frame.copy()
        if state.domain.active(now):
            out = self.void.render(out,state.domain,now,person_mask,self.reduced)
        layer = np.zeros_like(out)
        for name,pos,kind in state.events:
            self.burst(pos,kind,85 if name == 'launch' else 45)
        alive = []
        for pos,vel,life,color in self.particles:
            life -= dt
            if life <= 0:
                continue
            new = pos+vel*dt
            cv2.line(layer,point(pos),point(new),tint(color,min(1,life*2)),2,cv2.LINE_AA)
            alive.append([new,vel*math.exp(-dt*1.5),life,color])
        self.particles = alive

        if state.phase == 'summon':
            for side,e in state.energy.items():
                visible = state.visibility(side,now)
                radius = float(np.clip(e.span*.98,42,112))
                if e.active and visible > 0:
                    birth = min(1.,max(.1,(now-e.created)/.25))
                    self.orb(layer,e.position,radius*birth,side,now,visible,
                             ready=1. if e.flick.armed else e.flick.holding/e.flick.HOLD_SECONDS*.2)
                elif e.progress > 0:
                    self.orb(layer,e.position,radius*(.25+.5*e.progress),side,now,e.progress*.7)
        elif state.phase == 'fusion':
            p = float(np.clip(now-state.phase_start,0,1))
            r = state.purple_span*(1.7*(1-p)+.06)
            for k,side in enumerate(('Left','Right')):
                a = p*TAU*1.6+k*math.pi
                pos = state.purple+np.array([math.cos(a),math.sin(a)*.50])*r
                self.orb(layer,pos,state.purple_span*(.85-p*.55),side,now,1-p*.5)
            self.orb(layer,state.purple,20+65*p,'Purple',now,p)
        elif state.phase == 'purple':
            visible = float(np.clip(1-(now-state.purple_last_seen-.2)/.6,0,1))
            radius = float(np.clip(state.purple_span*1.14,54,132))
            self.orb(layer,state.purple,radius,'Purple',now,visible,ready=float(state.pinch_armed))
        for projectile in state.projectiles:
            self.draw_projectile(layer,projectile,now,(w,h))
        if not self.reduced:
            tiny = cv2.resize(layer,(max(1,w//4),max(1,h//4)))
            bloom = cv2.resize(cv2.GaussianBlur(tiny,(0,0),3),(w,h))
            cv2.addWeighted(out,1,bloom,.5,0,dst=out)
        cv2.add(out,layer,dst=out)
        if self.debug:
            for side,hand in state.hands.items():
                if hand.points is not None:
                    for p in hand.points:
                        cv2.circle(out,point(p),2,COLORS[side],-1)
        return out
