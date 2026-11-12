import cv2, numpy as np, pickle, sys
from scipy import ndimage as ndi
sys.path.insert(0,str(__import__("pathlib").Path(__file__).resolve().parents[1]))
import prop_test_sequence as pts
S=sys.argv[1]; OUT=sys.argv[2]; AUDIO=sys.argv[3]
lab,keep,fps=pickle.load(open(S+"/seg.pkl","rb")); (cl,)=pickle.load(open(S+"/clus.pkl","rb"))
cells=np.load(S+"/cells.npy"); g=cells.max(axis=3); T=g.shape[0]; B=8
F=np.load(S+"/F.npy",mmap_mode="r")
sizes=ndi.sum(lab>0,lab,range(1,lab.max()+1)); big=np.argmax(sizes)+1
orn=[i for i in keep if i!=big]; orn.sort(key=lambda i:np.where(lab==i)[0].mean())
reg=[]
for k in range(cl.max()+1):
    l2,n2=ndi.label(cl==k,structure=np.ones((3,3)))
    for j in range(1,n2+1):
        if (l2==j).sum()>=5: reg.append(l2==j)
reg.sort(key=lambda m:-m.sum())
elem={}  # id -> (pixel mask, signal)
for n,i in enumerate(orn): elem[f"O{n+1}"]=(lab==i)
for n,m in enumerate(reg): elem[f"H{n+1}"]=np.kron(m,np.ones((B,B),bool))
def _hsv(fi):
    f=np.asarray(F[fi]).copy(); h=cv2.cvtColor(f,cv2.COLOR_BGR2HSV); return f,h[...,0].astype(int),h[...,1].astype(int),h[...,2].astype(int)
_,H0,S0,V0=_hsv(320)
red=(V0>110)&((H0<8)|(H0>170))&(S0>110)
elem["W"]=cv2.dilate(red.astype(np.uint8),np.ones((5,5)))>0           # garage door + front door outlines
tree=np.zeros((360,640),bool); tree[262:320,411:432]=True
elem["T"]=cv2.dilate(tree.astype(np.uint8),np.ones((3,3)))>0         # white spiral tree
_,H1,S1,V1=_hsv(720)
grn=(V1>110)&(H1>40)&(H1<90)&(S1>110); grn[250:]=False
elem["E"]=cv2.dilate(grn.astype(np.uint8),np.ones((7,7)))>0          # roofline eaves
ebig=cv2.dilate(cv2.morphologyEx(elem["E"].astype(np.uint8),cv2.MORPH_CLOSE,np.ones((1,41))),np.ones((9,9)))>0
roof=np.load(S+"/roofmask.npy")&~ebig
roof[195:213,413:433]=False   # star topper
roof[203:238,455:477]=False   # chimney
roof[232:,270:]=False         # leftover eave-line pixels
elem["R"]=roof                                                    # red roof ridge/hip lines
pp=np.zeros((360,640),bool); pp[268:340,596:630]=True
pl=np.zeros((360,640),bool); pl[295:329,0:25]=True
elem["L"]=pl                                                      # two small green trees, far left
ps=np.zeros((360,640),bool); ps[268:300,228:268]=True
elem["S"]=ps                                                      # bright pink bare tree -> pixie spheres
bb=np.zeros((360,640),bool); bb[246:262,128:224]=True
elem["B"]=bb&~elem["W"]                                           # back-and-forth bar above garage door
am=np.zeros((360,640),bool); am[222:300,402:454]=True
elem["AM"]=am                                                     # tall white spiral (upper part) -> AA Mega Tree
ms=np.zeros((360,640),bool); ms[196:218,405:429]=True
elem["M"]=ms                                                       # star/spinner above it -> Mega Star
lt=np.zeros((360,640),bool); lt[232:276,36:58]=True
elem["LT"]=lt                                                     # red cone tree at far left -> AA Mega Tree
ls=np.zeros((360,640),bool); ls[212:232,37:57]=True
elem["LS"]=ls                                                      # white ball topper -> Mega Super Star
st=np.zeros((360,640),bool); st[280:322,50:71]=True
elem["ST"]=st                                                     # small white tree, left -> Group - Spiral Trees (white pixels only)
for _i,_x in enumerate([354,379,405,428,456,482,508,533]):
    _m=np.zeros((360,640),bool); _m[303:324,_x-6:_x+7]=True; elem[f"C{_i+1}"]=_m   # candy canes, left to right
elem["P"]=pp                                                      # rightmost front tree -> pixie poles
MAP={}
ORN=["Sphere 1","Sphere 2","Sphere 3","Sphere 4","Sphere 5","Sphere 6","BigBulb - 1","BigBulb - 2","BigBulb - 3","BigBulb - 4","BigBulb - 5","Bulb Red","Bulb Green","Bulb Blue","Bulb Yellow","Ornament Left"]
for n,mdl in enumerate(ORN): MAP[f"O{n+1}"]=[mdl]
MAP.update({"E":["Group - Eaves"],"R":["Group - Yard Boarders"],"W":["Group - Window Frames and Doors"],"T":["Group - Trees"],
 "H3":["Matrix Garage New"],"C1":["PixStake-R1"],"C2":["PixStake-R2"],"C3":["PixStake-R3"],"C4":["PixStake-R4"],"C5":["PixStake-R5"],"C6":["PixStake-R6"],"C7":["PixStake-R7"],"C8":["Group - Candy Canes"],
 "H31":["Lg Star - 01"],"P":["Group - Pixie Poles"],"L":["Group - Pixel Tree"],"B":["Group - House Horizontals"],"AM":["AA Mega Tree"],"LT":["AAA Mega Super Tree"],"LS":["Mega Super Star"],"ST":["Group - Spiral Trees"],"M":["Mega Star"],"S":["Group - Pixie Spheres"],"H11":["Arches-6-R"]})
for _j in range(10):
    MAP[f"C{round(_j*7/9)+1}"].append(f"MickeyStake-{_j+1:02d}")
# brightness signals at full res (one pass over the frames)
ids=[k for k in MAP if k in elem]
sig={k:np.zeros(T,np.float32) for k in ids}
for t in range(T):
    fc=np.asarray(F[t]); f=fc.max(axis=2); hv=cv2.cvtColor(fc[280:322,50:71],cv2.COLOR_BGR2HSV)
    for k in ids:
        if k=='B': sig[k][t]=(f[elem[k]]>150).mean()*255
        elif k=='AM': sig[k][t]=(f[elem[k]]>150).mean()*255
        elif k=='ST': sig[k][t]=((hv[...,1]<90)&(hv[...,2]>150)).mean()*255
        else: sig[k][t]=f[elem[k]].mean()
def snap(ms): return int(round(ms/25))*25
def color(k,a,b):
    m=elem[k]; t=(a+b)//2
    px=np.asarray(F[t])[m].astype(np.float32)[:,::-1]  # RGB
    v=px.max(1); sel=px[v>=max(v.max()*0.7,40)]
    if len(sel)==0: return "#FFFFFF"
    c=sel.mean(0); c=c/c.max()*255
    c=np.clip(np.round(c/32)*32,0,255).astype(int)
    return "#%02X%02X%02X"%tuple(c)
def bounce_rate():
    ys,xs=np.where(elem["B"]); x0,x1,y0,y1=xs.min(),xs.max()+1,ys.min(),ys.max()+1
    cx=[];br=[]
    for t in range(T):
        a=np.asarray(F[t])[y0:y1,x0:x1].max(axis=2).astype(np.float32); a=np.where(a>a.max()*0.6,a,0)
        br.append(a.mean()); w=a.sum(0); cx.append((w*np.arange(len(w))).sum()/w.sum() if w.sum()>0 else np.nan)
    cx=np.array(cx); br=np.array(br); on=br>np.percentile(br,5)+0.5*(np.percentile(br,97)-np.percentile(br,5))
    rev=[]
    d=np.sign(np.diff(ndi.uniform_filter1d(np.nan_to_num(cx,nan=np.nanmean(cx)),3)))
    for t in range(1,len(d)):
        if on[t] and on[t-1] and d[t]!=0 and d[t-1]!=0 and d[t]!=d[t-1]: rev.append(t)
    gaps=np.diff(rev); gaps=gaps[(gaps>=3)&(gaps<=60)]
    print("bar: lit frames",int(on.sum()),"reversals",len(rev),"median half-period frames",np.median(gaps) if len(gaps) else None)
    return (fps/(2*np.median(gaps))) if len(gaps) else 1.0
BPS=bounce_rate(); print("bounces/sec (back-and-forth cycles):",round(BPS,2))
plan=pts.Plan(); tot=int(T/fps*1000); rep=[]; missing=[]
for k in MAP:
    if k not in sig: missing.append(k); continue
    s=ndi.uniform_filter1d(sig[k],2); lo,hi=np.percentile(s,5),np.percentile(s,97)
    if hi-lo<12: missing.append(k); continue
    fo,ff=(0.35,0.2) if k=='B' else (0.55,0.40); on_t,off_t=lo+fo*(hi-lo),lo+ff*(hi-lo); st=False; ons=[]
    for t,v in enumerate(s):
        if not st and v>=on_t: st=True; start=t
        elif st and v<=off_t:
            st=False
            if t-start>=2: ons.append((start,t))
    if st: ons.append((start,T-1))
    mg=[]
    for a,b in ons:
        if mg and a-mg[-1][1]<(10 if k=='B' else 3): mg[-1]=(mg[-1][0],b)
        else: mg.append((a,b))
    for a,b in mg:
        s0=snap(a/fps*1000); e0=max(s0+25,snap(b/fps*1000)); c=color(k,a,b)
        if k!="B" and (b-a)/fps>1.5:
            step=int(fps); cuts=list(range(a,b,step))+[b]; segs=[]
            for x0,x1 in zip(cuts,cuts[1:]):
                cc=color(k,x0,x1)
                if segs and segs[-1][2]==cc: segs[-1][1]=x1
                else: segs.append([x0,x1,cc])
            for x0,x1,cc in segs:
                t0=snap(x0/fps*1000); t1=max(t0+25,snap(x1/fps*1000))
                for mdl in MAP[k]: plan.add(mdl,"On",t0,t1,pts.ON,[cc])
            plan.label(k,"on",s0,e0); continue
        if k=="B":
            dur=(e0-s0)/1000; rot=int(np.clip(round(10*dur*BPS),1,200))
            st=("B_CHOICE_BufferStyle=Per Model Default,E_NOTEBOOK_SSEFFECT_TYPE=Chase,E_CHOICE_Chase_Type1=Bounce from Left,"
                f"E_SLIDER_Number_Chases=1,E_SLIDER_Color_Mix1=10,E_CHECKBOX_Chase_3dFade1=0,E_CHECKBOX_Chase_Group_All=0,E_SLIDER_Chase_Rotations={rot}")
            for mdl in MAP[k]: plan.add(mdl,"SingleStrand",s0,e0,st,[c])
        else:
            for mdl in MAP[k]: plan.add(mdl,"On",s0,e0,pts.ON,[c])
        plan.label(k,"on",s0,e0)
    rep.append((k,len(mg)))
print("flashes per element:",rep); print("missing/too quiet:",missing)
# a model driven by several video elements: sort and trim so effects on one layer never overlap
by={}
for e in plan.effects: by.setdefault(e[0],[]).append(e)
fixed=[]
for m,lst in by.items():
    lst.sort(key=lambda e:e[3]); out=[]
    for e in lst:
        if out and e[3]<out[-1][4]:
            o=out[-1]; out[-1]=o[:4]+(e[3],)+o[5:]
            if out[-1][4]-out[-1][3]<25: out.pop()
        out.append(e)
    fixed+=out
print("overlaps trimmed:",len(plan.effects)-len(fixed) if len(fixed)<len(plan.effects) else 0,"dropped")
plan.effects=fixed
VIDEOS=r"F:\ShowFolderQA\Videos"          # show-folder video directory (Windows path stored in the .xsq)
VID=VIDEOS+"\\Christmas Techno Mix 2011.mp4"
vend=int(tot//25*25)
plan.add("TV-Right","Video",0,vend,
 "E_CHECKBOX_SynchroniseWithAudio=0,E_CHECKBOX_Video_AspectRatio=1,E_CHECKBOX_Video_TransparentBlack=0,"
 "E_CHOICE_Video_DurationTreatment=Normal,E_FILEPICKERCTRL_Video_Filename="+VID+",E_TEXTCTRL_Duration=3:30.843,"
 "E_TEXTCTRL_SampleSpacing=0,E_TEXTCTRL_Video_CropBottom=0,E_TEXTCTRL_Video_CropLeft=0,E_TEXTCTRL_Video_CropRight=100,"
 "E_TEXTCTRL_Video_CropTop=100,E_TEXTCTRL_Video_Starttime=0.00,E_TEXTCTRL_Video_TransparentBlack=0",["#FFFFFF"])
for _m,_vf in (("Matrix - 1L","Abstract Bounce 96x16.mp4"),("Matrix - 2R","Spectrum Bars 96x16.mp4")):
    plan.add(_m,"Video",0,vend,
     "E_CHECKBOX_SynchroniseWithAudio=0,E_CHECKBOX_Video_AspectRatio=0,E_CHECKBOX_Video_TransparentBlack=0,"
     "E_CHOICE_Video_DurationTreatment=Normal,E_FILEPICKERCTRL_Video_Filename="+VIDEOS+"\\"+_vf+",E_TEXTCTRL_Duration=3:30.933,"
     "E_TEXTCTRL_SampleSpacing=0,E_TEXTCTRL_Video_CropBottom=0,E_TEXTCTRL_Video_CropLeft=0,E_TEXTCTRL_Video_CropRight=100,"
     "E_TEXTCTRL_Video_CropTop=100,E_TEXTCTRL_Video_Starttime=0.00,E_TEXTCTRL_Video_TransparentBlack=0",["#FFFFFF"])
for _m,_f in (("Matrix Garage Left","Garage Santa 48x27.mp4"),("Matrix-mini-left","Mini Snowflakes Cycle 50x12.mp4"),("Matrix-mini-right","Mini Snowflakes 50x12.mp4"),("Matrix - ColL","Column Left 8x40.mp4"),("Matrix - ColR","Column Right 8x40.mp4"),("Matrix Garage Right","Garage Bells 48x27.mp4")):
    plan.add(_m,"Video",0,vend,
     "E_CHECKBOX_SynchroniseWithAudio=0,E_CHECKBOX_Video_AspectRatio=0,E_CHECKBOX_Video_TransparentBlack=0,"
     "E_CHOICE_Video_DurationTreatment=Normal,E_FILEPICKERCTRL_Video_Filename="+VIDEOS+"\\"+_f+",E_TEXTCTRL_Duration=3:31.000,"
     "E_TEXTCTRL_SampleSpacing=0,E_TEXTCTRL_Video_CropBottom=0,E_TEXTCTRL_Video_CropLeft=0,E_TEXTCTRL_Video_CropRight=100,"
     "E_TEXTCTRL_Video_CropTop=100,E_TEXTCTRL_Video_Starttime=0.00,E_TEXTCTRL_Video_TransparentBlack=0",["#FFFFFF"])
sys.path.insert(0,str(__import__("pathlib").Path(__file__).resolve().parent))
from mhmarks import mh_tracks
_rows=mh_tracks(AUDIO,plan,tot)
import video_beams_to_xsq as v2x
_MH=v2x.mh_settings(0.0,0.0,15.0,15.0,(0.0,0.0,1.0),"Dimmer: 0.000000&comma;1.000000&comma;1.000000&comma;1.000000",True,False)   # pan 0, tilt +15 (leans toward the front), white, full dimmer, shutter on
_LINK=v2x.mh_settings(0.0,0.0,15.0,15.0,(0.0,0.0,1.0),"",False,True)    # linked: holds the lit pose (pan 0, tilt +15); end position follows the next effect
PRE=2000                                                                 # lead-in for a head's first beat (nothing before it to hold from)
_last_end={}
_GH,_GS=v2x.snap_to_wheel(1.0/3.0,r"F:/ShowFolderQA")                         # the colour wheel's green
_KICK=v2x.mh_settings(0.0,0.0,15.0,40.0,(_GH,_GS,1.0),"Dimmer: 0.000000&comma;1.000000&comma;1.000000&comma;1.000000",True,False)   # flick: tilt 15 -> 40, all heads lit
_FLICK={a:b for (l,a,b) in plan.tracks["MH Accents"] if l.startswith("flick")}
def _mh(_lab,_a,_b,_set,_pal="#FFFFFF"):
    _ps=_last_end[_lab] if _lab in _last_end else max(_a-PRE,0)           # lead-in: from the end of this head's previous effect
    if _a-_ps>=100: plan.add(_lab,"Moving Head",_ps,_a,_LINK,["#FFFFFF"])
    plan.add(_lab,"Moving Head",_a,_b,_set,[_pal]); _last_end[_lab]=_b
_nflick=0
def _sine(axis,centre,amp,cycles):
    # Sine value curve on the effect's +-180 deg scale (same encoding as mh_fan.sine_vc): P1 phase %, P2 amplitude, P3 cycles x 10, P4 centre
    return (f"{axis} VC: Active=TRUE|Id=ID_VALUECURVE_MH{axis}|Type=Sine|Min=-1800.00|Max=1800.00|"
            f"P1=0.0000|P2={20.0*amp-1800.0:.4f}|P3={cycles*10.0:.4f}|P4={5.0*centre:.4f}|RV=TRUE|")
_BH,_BS=v2x.snap_to_wheel(2.0/3.0,r"F:/ShowFolderQA")                         # the colour wheel's blue (the sweep is blue so it reads apart from the white chase and green flicks)
def _sweep_settings(pan_amp,pan_cycles,tilt_amp,tilt_cycles):
    dim="Dimmer: 0.000000&comma;0.000000&comma;0.080000&comma;0.600000&comma;0.920000&comma;0.600000&comma;1.000000&comma;0.000000"   # fade in, hold 60%, fade out
    slot=(f"Color: {_BH:.6f}&comma;{_BS:.6f}&comma;1.000000;{dim};{_sine('Pan',0.0,pan_amp,pan_cycles)};{_sine('Tilt',15.0,tilt_amp,tilt_cycles)};"
          "PanOffset: 0.0;TiltOffset: 0.0;Groupings: 1.0;Cycles: 1.0;Heads: 1;Shutter: On")
    return v2x.mh_effect_settings(0,0,{1:slot})
_SWEEP=_sweep_settings(45.0,2.0,8.0,4.0)       # pan +-45 deg x2 cycles, tilt 15 +-8 deg x4 cycles (starts and ends at pan 0 / tilt 15)
_calm=[(int(_r[3]*1000),int(_r[4]*1000)) for _r in _rows if _r[0]=="CALM"]; STAG=300     # wave: each head starts 300 ms after the one before
def _do_sweeps(_s0,_e0):
    for _n in range(8):
        _mh(f"MH-{_n+1}",_s0+_n*STAG,_e0-(7-_n)*STAG,_SWEEP,"#0000FF")
for _lab,_a,_b in plan.tracks["MH Chase"]:
    while _calm and _a>=_calm[0][0]: _do_sweeps(*_calm.pop(0))
    if _a in _FLICK:                                                      # flick beat: all eight heads kick, in place of the single chase head
        _nflick+=1
        for _n in range(1,9): _mh(f"MH-{_n}",_a,_FLICK[_a],_KICK,"#00FF00")
    else: _mh(_lab,_a,_b,_MH)
while _calm: _do_sweeps(*_calm.pop(0))
print("flick beats:",_nflick,"of",len(_FLICK),"flick marks")
for _r in _rows: print("MH section",_r[0],"bars",_r[1],"-",_r[2],"%.1fs-%.1fs"%(_r[3],_r[4]))
pts.write(plan,tot,OUT)
import xml.etree.ElementTree as ET
tree=ET.parse(OUT); h=tree.getroot().find("head"); h.find("mediaFile").text=AUDIO; h.find("sequenceType").text="Media"
h.find("song").text="Christmas Techno Mix 2011"
ET.indent(tree,space="  "); tree.write(OUT,encoding="UTF-8",xml_declaration=True)
print("effects",len(plan.effects),"->",OUT)

import pickle as _p; _p.dump((sig,fps),open(S+'/sig.pkl','wb'))
