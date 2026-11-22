from functools import lru_cache
from math import atan2, cos, pi, sin, sqrt
from pathlib import Path
import json
from random import Random
import sys

import numpy as np

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT, SOURCE, ASSET = map(Path,sys.argv[1:])
DATA = json.loads(SNAPSHOT.read_text())
PROFILE = DATA["profile"]
NAME = PROFILE.get("name") or PROFILE["login"]
CREAM = "#f9eddd"
GOLD = "#ffc57f"
ICE = "#88c9f3"
RED = "#f3705d"
MUTED = "#9aaec4"
LINE = "#304658"
DARK = "#0b1421"
TAU = 2 * pi
RESAMPLE = Image.Resampling.LANCZOS
PERSPECTIVE = Image.Transform.PERSPECTIVE

@lru_cache
def font(name, size):
    family = {"Arial Bold.ttf": "DejaVuSans-Bold.ttf", "Courier New Bold.ttf": "DejaVuSansMono-Bold.ttf"}
    try:
        return ImageFont.truetype(family[name], size)
    except OSError:
        return ImageFont.truetype(str(Path("/System/Library/Fonts/Supplemental") / name), size)

def txt(d, xy, label, size=16, color=CREAM, face="Arial Bold.ttf"):
    d.text(xy, label, fill=color, font=font(face, size), anchor="lt")

@lru_cache
def fit_text(label,size,width):
    face="Arial Bold.ttf"
    while size>12 and font(face,size).getlength(label)>width:
        size-=1
    while len(label)>1 and font(face,size).getlength(label)>width:
        label=label[:-2]+"…"
    return label,size

def limited(d,xy,label,size,width,color=CREAM):
    label,size=fit_text(label,size,width)
    txt(d,xy,label,size,color,"Arial Bold.ttf")

def code(d, xy, label, color=GOLD, size=12):
    txt(d, xy, label, size, color, "Courier New Bold.ttf")

def mark(d, x,y, color=GOLD, s=8):
    d.line((x-s,y,x+s,y), fill=color)
    d.line((x,y-s,x,y+s), fill=color)

def dot(d,x,y,r,color):
    d.ellipse((x-r,y-r,x+r,y+r), fill=color)

def frame(d,w,h,margin=14):
    m=margin
    for x,y,sx,sy in [(m,m,1,1),(w-m,m,-1,1),(w-m,h-m,-1,-1),(m,h-m,1,-1)]:
        d.line((x,y,x+13*sx,y), fill=GOLD)
        d.line((x,y,x,y+10*sy), fill=GOLD)

def backdrop(size, flavor):
    w,h=size
    im=Image.new("RGB",size,DARK)
    d=ImageDraw.Draw(im)
    for i in range(82,0,-1):
        k=i/82
        c=(int(16+13*(1-k)),int(25+15*(1-k)),int(38+22*(1-k)))
        d.ellipse((w*flavor-w*k*.68,-h*.85*k,w*flavor+w*k*.68,h*1.33*k),fill=c)
    for x in range(0,w,36):
        d.line((x,0,x,h), fill="#1d2d3c")
    for y in range(0,h,36):
        d.line((0,y,w,y), fill="#1d2d3c")
    return im

def starfield(seed,count,x_range,y_range):
    rng=Random(seed)
    return [(rng.uniform(*x_range),rng.uniform(*y_range),rng.randint(1,3),rng.random())
            for _ in range(count)]

HORIZON=starfield(49,102,(19,879),(15,160))
OPEN_SPACE=starfield(183,84,(7,892),(9,279))
COLD=("#44668b","#88c9f3","#dbf4ff")
WARM=("#784950","#e57161","#ffd39b")

def ambient(d,t,points,span,clipped_height,hero=False):
    for index,(sx,sy,depth,bias) in enumerate(points):
        x=15+(sx-15+t*span*depth)%span
        y=(sy+8*sin(TAU*(t+bias)))%clipped_height
        if hero and 440<x<563 and y>67:
            continue
        palette=WARM if index%6==0 else COLD
        color=palette[depth-1]
        tail=depth*2 if depth>1 else 0
        if tail:
            d.line((x-tail,y+1,x,y),fill=palette[0])
        dot(d,x,y,.45+depth*.24,color)
        if depth==3 and index%4==0:
            d.line((x-2,y,x+3,y),fill=color)
            d.line((x,y-2,x,y+2),fill=color)

hero_bg=ImageOps.fit(Image.open(ROOT/"sources/observatory.jpg").convert("RGB"),(900,318),method=RESAMPLE)
overlay=Image.new("RGBA",hero_bg.size)
shade=ImageDraw.Draw(overlay)
for x in range(900):
    alpha=max(0,int(223*(1-x/590)))
    shade.line((x,0,x,318),fill=(5,12,21,alpha))
hero_bg=Image.alpha_composite(hero_bg.convert("RGBA"),overlay).convert("RGB")
def intro(t):
    im=hero_bg.copy()
    d=ImageDraw.Draw(im)
    ambient(d,t,HORIZON,870,162,hero=True)
    streak_x=495+(t*385)%385
    for i in range(31):
        x=streak_x-i*2.25
        if 486<x<881:
            y=75+(x-486)*.13
            d.line((x-2,y+.26,x,y),fill=ICE if i<9 else "#4d839f",width=2 if i<7 else 1)
    for i,(radius,tilt,color) in enumerate([(205,-.24,ICE),(170,.31,GOLD),(136,-.53,RED)]):
        half=radius*.26
        phase=TAU*(t*(i+1)+i*.14)
        def pos(a):
            q,z=radius*cos(a),half*sin(a)
            return 648+q*cos(tilt)-z*sin(tilt),153+q*sin(tilt)+z*cos(tilt)
        for arc in range(0,120,4):
            d.line([pos(arc*TAU/120),pos((arc+2)*TAU/120)],fill=("#5c7893","#896d57","#8b5b58")[i])
        for j in range(17,0,-1):
            x,y=pos(phase-j*.035)
            dot(d,x,y,1+(17-j)/16,color if j<5 else ("#486275","#86684d","#714e4d")[i])
        x,y=pos(phase)
        mark(d,x,y,color,6)
        dot(d,x,y,3,CREAM)
    d.line((29,54,277,54),fill="#50627a")
    code(d,(30,35),"@"+PROFILE["login"].upper(),ICE,15)
    limited(d,(26,88),NAME,85,390)
    txt(d,(33,188),"AI Engineer & Researcher",28,GOLD)
    frame(d,900,318)
    return im

avatar=ImageOps.fit(Image.open(SOURCE/"avatar.jpg").convert("RGB"),(146,146),method=RESAMPLE)
holo_bg=backdrop((900,281),.2)
foil_colors=((135,208,252),(252,218,151),(243,120,119))
def warp(card, vertices, output_size):
    source_corners=[(0,0),(card.width,0),(card.width,card.height),(0,card.height)]
    rows, targets=[], []
    for (x,y),(u,v) in zip(vertices,source_corners):
        rows.extend([[x,y,1,0,0,0,-x*u,-y*u],[0,0,0,x,y,1,-x*v,-y*v]])
        targets.extend([u,v])
    coefficients=np.linalg.solve(rows,targets)
    return card.transform(output_size,PERSPECTIVE,coefficients,Image.Resampling.BICUBIC)

def holo(t):
    im=holo_bg.copy()
    d=ImageDraw.Draw(im)
    ambient(d,t,OPEN_SPACE,870,260)
    wobble=sin(TAU*t)
    d.rounded_rectangle((57,56,335,238),radius=13,fill="#080f19",outline="#30445c")
    card=Image.new("RGBA",(252,178))
    inner=ImageDraw.Draw(card)
    inner.rounded_rectangle((1,1,250,176),radius=11,fill="#21354a",outline="#86bfe5",width=2)
    for offset in range(5,244,5):
        inner.line((offset,160,min(offset+87,244),84),fill="#2b3f53")
    card.paste(avatar,(13,15))
    code(inner,(171,24),"PROFILE",ICE)
    limited(inner,(169,54),NAME,18,75)
    code(inner,(170,83),"AI ENG.",GOLD)
    code(inner,(170,106),"RESEARCH",GOLD)
    inner.line((171,137,231,137),fill="#7e9abd")
    for i in range(9):
        q=171+i*7
        inner.line((q,148,q,162-(i%4)*2),fill=("#97abca","#f5ba7e","#e97f78")[i%3])
    fx=Image.new("RGBA",card.size)
    f=ImageDraw.Draw(fx)
    sweep=-94+t*430
    for j in range(-27,28):
        strength=int(max(0,1-abs(j)/29)*109)
        color=foil_colors[min(2,(j+27)//18)]
        f.line((sweep+j-32,176,sweep+j+33,1),fill=color+(strength,),width=2)
    composite=Image.alpha_composite(card,fx)
    composite.putalpha(card.getchannel("A"))
    outline=[(69+13*wobble,52+11*wobble),(325+8*wobble,36-12*wobble),(320+11*wobble,213+17*wobble),(70+13*wobble,227-8*wobble)]
    layer=warp(composite,outline,im.size)
    im.paste(layer,(0,0),layer)
    d=ImageDraw.Draw(im)
    for x,y in [outline[0],outline[2]]:
        mark(d,x,y,RED,9)
    for k,word in enumerate(["Build the tool.","Test the idea.","Publish the evidence."]):
        yy=56+48*k
        active=min(2,int(t*3))==k
        d.line((391,yy+13,423,yy+13),fill=GOLD if active else LINE,width=2)
        txt(d,(441,yy),word,31,CREAM if active else "#beced9")
    frame(d,900,281)
    return im

projects=DATA["projects"]
project_images=[Image.open(SOURCE/p["media"]).convert("RGB") if p["media"] else None for p in projects]
work_bg=backdrop((900,344),.77)
def reel(t):
    im=work_bg.copy()
    d=ImageDraw.Draw(im)
    if not projects:
        txt(d,(30,115),"No public featured projects",34)
        return im
    phase=t*len(projects)
    idx=min(len(projects)-1,int(phase))
    part=phase-idx
    item=projects[idx]
    name,kind=item["title"],item["category"].upper()
    source=project_images[idx]
    crop=Image.new("RGB",(565,281),"#0d1726")
    if source:
        scaled=ImageOps.contain(source,(565,281),method=RESAMPLE)
        scale=1.02+.075*(.5-.5*cos(pi*part))
        shot=scaled.resize((round(scaled.width*scale),round(scaled.height*scale)),RESAMPLE)
        crop.paste(shot,((565-shot.width)//2+round((part-.5)*10),(281-shot.height)//2))
    else:
        txt(ImageDraw.Draw(crop),(40,115),"View repository documentation",26,ICE)
    im.paste(crop,(24,32))
    d=ImageDraw.Draw(im)
    d.rectangle((24,32,589,313),outline="#69839b")
    cross=int(39+569*part)
    if cross<589 and part<.17:
        for i in range(13):
            d.line((cross-i,33,cross-i,311),fill=("#245071" if i else ICE))
    limited(d,(619,110),name,34,250)
    d.line((621,169,861,169),fill="#647484")
    code(d,(622,190),kind,GOLD,13)
    for j in range(len(projects)):
        xx=622+47*j
        d.line((xx,248,xx+33,248),fill=RED if j==idx else LINE,width=2)
        code(d,(xx,261),f"0{j+1}",ICE if j==idx else MUTED)
    d.line((622,296,622+int(235*part),296),fill=GOLD,width=2)
    frame(d,900,344)
    return im

calendar=DATA["calendar"]
active=[(w,d) for w,d,level,count in calendar if level]
activity_index={point:i for i,point in enumerate(active)}
weeks=[0]*max(53,1+max(d[0] for d in calendar))
for w,d,level,count in calendar:
    weeks[w]+=count
peak=max(1,max(weeks))
tape_bg=ImageOps.fit(Image.open(ROOT/"sources/cassette.jpg").convert("RGB"),(900,288),method=RESAMPLE)
def tape(t):
    im=tape_bg.copy()
    d=ImageDraw.Draw(im)
    ambient(d,t,HORIZON[:24],870,37)
    for idx,(x,y) in enumerate([(194,141),(359,116)]):
        a=TAU*t*(1 if idx else -1)+.8
        for j in range(12):
            p=a-j*.10
            dot(d,x+18*cos(p),y+10*sin(p),2,("#7e573d" if j>6 else GOLD if j else ICE))
        d.line((x,y,x+16*cos(a),y+9*sin(a)),fill=GOLD,width=2)
        d.line((x,y,x-16*cos(a),y-9*sin(a)),fill="#b37544",width=2)
        dot(d,x,y,2,CREAM)
    txt(d,(590,47),"More to explore",30)
    code(d,(594,96),"PUBLIC GITHUB ACTIVITY",ICE,12)
    marker=int(t*53)
    for i,n in enumerate(weeks):
        x=593+5*i
        height=2+int(72*sqrt(n/peak))
        d.rectangle((x,207-height,x+2,207),fill=GOLD if abs(i-marker)<2 else "#7299a8")
    d.line((591,221,860,221),fill=LINE)
    frame(d,900,288)
    return im

activity_bg=backdrop((900,205),.52)
def replay(t):
    im=activity_bg.copy()
    d=ImageDraw.Draw(im)
    if not active:
        return calendar_view(t)
    progress=min(len(active),t*(len(active)+6))
    eaten=int(progress)
    fraction=progress-eaten
    sent=active[min(eaten,len(active)-1)]
    prev=active[max(0,eaten-1)] if eaten else (sent[0]-.75,sent[1])
    def pos(w,day):
        return 37+w*(823/max(52,len(weeks)-1)),59+day*15.0
    scan=(len(weeks)+3)*t-1
    for week,day,lvl,count in calendar:
        x,y=pos(week,day)
        val=("#213047","#497999","#78a6c4","#e58069","#ffcb8d")[lvl]
        if lvl and activity_index[(week,day)] < eaten:
            val="#283950"
        d.rounded_rectangle((x-5,y-5,x+5,y+5),radius=2,fill=val)
        if abs(week-scan)<1:
            d.rounded_rectangle((x-6,y-6,x+6,y+6),radius=2,outline=ICE)
    px,py=pos(*prev)
    dx,dy=pos(*sent)
    x,y=px+(dx-px)*fraction,py+(dy-py)*fraction
    a=atan2(dy-py,dx-px)
    jaw=3+4*abs(sin(progress*pi))
    def ship(points):
        return [(x+u*cos(a)-v*sin(a),y+u*sin(a)+v*cos(a)) for u,v in points]
    d.line(ship([(-25,0),(-12,0)]),fill=ICE,width=2)
    d.polygon(ship([(12,-jaw),(-9,-10),(-14,0),(-9,10),(12,jaw),(2,0)]),fill=RED,outline=GOLD)
    d.line(ship([(-7,-4),(-4,-4)]),fill=ICE,width=2)
    code(d,(29,28),"PUBLIC CONTRIBUTION ACTIVITY",ICE)
    code(d,(29,176),f"{eaten:02d} / {len(active)} ACTIVE DAYS EATEN",GOLD)
    code(d,(580,176)," TO ".join(DATA["dates"]),MUTED)
    frame(d,900,205)
    return im

pins_bg=backdrop((900,293),.85)
def pin_scene(t):
    im=pins_bg.copy()
    d=ImageDraw.Draw(im)
    ambient(d,t,OPEN_SPACE,870,279)
    pins=PROFILE["pins"]
    swipe=t*7
    for index,pin in enumerate(pins):
        row,column=divmod(index,2)
        x=27+column*432
        y=23+row*82
        active_pin=abs(swipe-index-.65)<.75
        edge=GOLD if active_pin else LINE
        d.rounded_rectangle((x,y,x+411,y+68),radius=7,fill="#141f31",outline=edge,width=2 if active_pin else 1)
        code(d,(x+14,y+14),f"{index+1:02d}",edge)
        limited(d,(x+44,y+15),pin["title"],21,350)
        short_summary=pin.get("summary") or "Public pin"
        limited(d,(x+44,y+45),short_summary,13,345,MUTED)
    if not pins:
        txt(d,(24,92),"No public pins are set.",31)
    frame(d,900,293)
    return im

def calendar_view(t):
    im=activity_bg.copy()
    d=ImageDraw.Draw(im)
    marker=int(t*(len(weeks)+6))-2
    for week,day,level,_ in calendar:
        x,y=37+week*(823/max(52,len(weeks)-1)),59+day*15
        color=("#263445","#285b55","#377c73","#55a095","#9ed0b3")[level]
        d.rounded_rectangle((x-5,y-5,x+5,y+5),radius=2,fill=color)
        if abs(week-marker)<1:
            d.rounded_rectangle((x-6,y-6,x+6,y+6),radius=3,outline=ICE,width=1)
    code(d,(29,28),"PUBLIC CALENDAR",ICE)
    code(d,(29,175),f"{sum(weeks)} CALENDAR CONTRIBUTIONS",GOLD)
    code(d,(580,175)," TO ".join(DATA["dates"]),MUTED)
    frame(d,900,205)
    return im

events_bg=backdrop((900,285),.81)
def recent_activity(t):
    im=events_bg.copy()
    d=ImageDraw.Draw(im)
    ambient(d,t,OPEN_SPACE,870,279)
    activity=DATA.get("activity",[])
    d.line((49,41,49,251),fill="#6e90ac",width=2)
    cursor=t*len(activity)
    for index,event in enumerate(activity):
        y=43+index*48
        hot=abs(index-cursor)<.7
        tint=GOLD if hot else ICE
        d.rounded_rectangle((72,y-17,861,y+23),radius=6,fill="#132236",outline=tint if hot else LINE)
        dot(d,49,y+1,6 if hot else 4,tint)
        limited(d,(93,y-9),event["repo"],19,278)
        limited(d,(400,y-7),event["label"],14,280,MUTED)
        code(d,(741,y-5),event["at"][:10],tint,13)
    if not activity:
        txt(d,(94,104),"No recent public events",25)
    frame(d,900,285)
    return im

def export(name, drawing, count, duration, still=.18):
    frames=[drawing(i/count) for i in range(count)]
    drawing(still).save(ASSET/f"{name}.jpg",quality=92,optimize=True)
    # The shared palette limits frame-to-frame color flicker.
    strip=Image.new("RGB",(180, max(1, len(frames[::5]))*56))
    for index,picture in enumerate(frames[::5]):
        strip.paste(ImageOps.fit(picture,(180,56),method=RESAMPLE),(0,index*56))
    palette=strip.quantize(colors=224)
    converted=[picture.quantize(palette=palette,dither=Image.Dither.NONE) for picture in frames]
    converted[0].save(ASSET/f"{name}.gif",save_all=True,append_images=converted[1:],duration=duration,loop=0,optimize=True)
    print(name, len(converted), (ASSET/f"{name}.gif").stat().st_size,flush=True)

scenes = [
    ("observatory",intro,52,110,.18),
    ("identity",holo,60,100,.18),
    ("project-reel",reel,90,120,.12),
    ("mixtape",tape,60,115,.18),
    ("activity-replay",replay,130,125,0),
    ("pinned-work",pin_scene,52,120,.05),
    ("calendar",calendar_view,60,110,.15),
    ("recent-activity",recent_activity,56,110,.1),
]
for scene in scenes:
    export(*scene)
