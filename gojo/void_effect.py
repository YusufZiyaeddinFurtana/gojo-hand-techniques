"""Unlimited-Void-inspired procedural environment; no embedded anime frames."""
from functools import lru_cache
import math
import cv2
import numpy as np


@lru_cache(maxsize=4)
def coordinates(width,height):
    h,w = max(90,height//3),max(160,width//3)
    y,x = np.mgrid[0:h,0:w].astype(np.float32)
    x = (x-w*.5)/(h*.36)
    y = (y-h*.44)/(h*.36)
    return x,y,np.sqrt(x*x+y*y),np.arctan2(y,x)


class VoidRenderer:
    def __init__(self):
        rng = np.random.default_rng(7466)
        self.stars = rng.uniform(-1,1,(950,2))
        self.depth = rng.uniform(0,1,950)
        self.tone = rng.uniform(0,1,950)

    def sky(self,width,height,age,reduced=False):
        x,y,r,a = coordinates(width,height)
        t = age*.45
        turbulence = (np.sin(a*7+r*9-t*1.8)+np.sin(a*17-r*12+t*2.1)*.45+
                      np.sin(a*31+r*26-t*1.5)*.18)
        clouds = np.clip(.50+turbulence*.24,0,1)
        belt = np.exp(-((r-1.24)/.36)**2)*clouds
        fog = np.exp(-((r-1.65)/.85)**2)*(.5+.5*np.sin(x*3+y*5+t))*.15
        image = np.zeros((*r.shape,3),np.float32)
        image[:] = [8,3,2]
        image += (belt+fog)[...,None]*np.array([155,92,68],np.float32)
        edge = 1.+.008*np.sin(a*21+t*5)+.006*np.sin(a*47-t*3)
        rim = np.exp(-((r-edge)/.016)**2)
        image += rim[...,None]*np.array([245,250,255],np.float32)
        halo = np.exp(-((r-1.015)/.085)**2)
        image += halo[...,None]*np.array([75,45,35],np.float32)
        # The aperture stays black, surrounded by a white-blue accretion boundary.
        inside = np.clip((r-.975)/.035,0,1)
        image *= inside[...,None]
        beam = np.exp(-((y+.02*np.sin(x*2+t))/.018)**2)*np.exp(-np.abs(x)*.5)
        image += (beam*(r>1.03))[...,None]*np.array([130,150,160],np.float32)
        sky = cv2.resize(np.uint8(np.clip(image,0,255)),(width,height))
        center = np.array([width*.5,height*.44])
        radius = height*.36
        count = 300 if reduced else len(self.stars)
        angle = age*.025
        rotation = np.array([[math.cos(angle),-math.sin(angle)],
                             [math.sin(angle),math.cos(angle)]])
        plane = self.stars[:count]@rotation
        z = .18+((self.depth[:count]-age*.105)%1)*2.8
        tail_z = z+.025+(.025 if not reduced else 0)
        head = center+plane/z[:,None]*[width*.95,height*1.1]
        tail = center+plane/tail_z[:,None]*[width*.95,height*1.1]
        for k,(p,q) in enumerate(zip(head,tail)):
            if not (0<=p[0]<width and 0<=p[1]<height) or np.linalg.norm(p-center)<radius*1.03:
                continue
            brightness = float(np.clip(1.15-z[k]*.22,.2,1))
            tone = self.tone[k]
            color = (int(240*brightness),int((185+60*tone)*brightness),int((150+95*tone)*brightness))
            p,q = tuple(p.astype(int)),tuple(q.astype(int))
            cv2.line(sky,q,p,color,1,cv2.LINE_AA)
            cv2.circle(sky,p,2 if z[k]<.8 else 1,color,-1,cv2.LINE_AA)
        if not reduced:
            small = cv2.resize(sky,(width//4,height//4))
            glow = cv2.resize(cv2.GaussianBlur(small,(0,0),2),(width,height))
            cv2.addWeighted(sky,1,glow,.28,0,dst=sky)
        return sky

    def render(self,frame,domain,now,person_mask=None,reduced=False):
        alpha = domain.strength(now)
        if alpha<=0:
            return frame.copy()
        age = now-domain.started
        h,w = frame.shape[:2]
        sky = self.sky(w,h,age,reduced)
        if person_mask is None:
            # If segmentation is unavailable, keep a faint live view instead of losing the user.
            scene = cv2.addWeighted(frame,.30,sky,.85,0)
        else:
            mask = np.clip(person_mask,0,1).astype(np.float32)[...,None]
            person = frame.astype(np.float32)*np.array([.94,.87,.84],np.float32)
            scene = np.uint8(np.clip(sky*(1-mask)+person*mask,0,255))
        return cv2.addWeighted(frame,1-alpha,scene,alpha,0)
