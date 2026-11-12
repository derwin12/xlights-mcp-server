import numpy as np, cv2, subprocess, sys
sys.path.insert(0,str(__import__("pathlib").Path(__file__).resolve().parents[2]/"src"))
from xlights_mcp.audio.beats import detect_beats
AUDIO,OUT,PREV=sys.argv[1:4]
W,H,FPS,SS,UP=48,27,30,8,10
bm=detect_beats(AUDIO); beats=np.array(bm.beat_times_ms)/1000.0; bpb=bm.beats_per_bar
T=int(211*FPS)
def state(t):
    i=np.searchsorted(beats,t,side="right")-1
    if i<0: return -1,0.0,0.0
    per=(beats[i+1]-beats[i]) if i+1<len(beats) else 0.44
    return i,t-beats[i],(i+(t-beats[i])/per)
def bell_poly(cx,cy,h,wmax,ang):
    V=np.array([0,0.03,0.09,0.2,0.35,0.5,0.65,0.78,0.88,0.95,1.0]); WN=np.array([0,0.30,0.50,0.62,0.66,0.70,0.80,0.92,1.0,1.0,0.98])
    ys=np.linspace(0,h,30); w=np.interp(ys/h,V,WN)*wmax
    pts=[(-x,y) for x,y in zip(w,ys)]+[(x,y) for x,y in zip(w[::-1],ys[::-1])]
    c,s=np.cos(ang),np.sin(ang)
    return np.array([(cx+x*c-y*s,cy+x*s+y*c) for x,y in pts],np.float32)
def bell(S,cx,cy,h,wmax,ang,pulse,lag):
    P=bell_poly(cx,cy,h,wmax,ang); gold=(255,int(190+50*pulse),int(30+120*pulse))
    cv2.fillPoly(S,[P.astype(np.int32)],gold,cv2.LINE_AA)
    # highlight (left side) and darker rim
    c,s=np.cos(ang),np.sin(ang)
    def tr(x,y): return (int(cx+x*c-y*s),int(cy+x*s+y*c))
    cv2.line(S,tr(-wmax*0.30,h*0.2),tr(-wmax*0.45,h*0.7),(255,240,170),max(1,SS//2),cv2.LINE_AA)
    cv2.line(S,tr(-wmax,h),tr(wmax,h),(170,110,0),SS//2+1,cv2.LINE_AA)
    # clapper (lags the swing)
    la=ang*0.5+lag; cv2.circle(S,tr(np.sin(la)*wmax*0.35,h*1.06),int(SS*1.1),(255,210,80),-1,cv2.LINE_AA)
    # red bow at the pivot
    for sx in (-1,1): cv2.circle(S,(int(cx+sx*SS*1.5),int(cy-SS*0.6)),int(SS*1.4),(230,20,40),-1,cv2.LINE_AA)
    cv2.circle(S,(int(cx),int(cy-SS*0.4)),int(SS*0.9),(255,60,70),-1,cv2.LINE_AA)
def frame(t):
    i,ph,bp=state(t); pulse=np.exp(-ph*6)
    S=np.zeros((H*SS,W*SS,3),np.uint8)
    for cx,off in ((W*SS*0.26,0.0),(W*SS*0.74,0.2)):
        swing=np.cos(np.pi*(bp-off))*0.40          # same direction, a fifth of a beat apart: never collide
        sc=1.0+0.08*pulse
        bell(S,cx,H*SS*0.13,H*SS*0.52*sc,W*SS*0.125*sc,swing,pulse,-swing*0.8)
    # sparkles on the beat
    if i>=0 and ph<0.25:
        rng=np.random.RandomState(i*7919%100000); a=1-ph/0.25
        for _ in range(7):
            x,y=rng.randint(int(W*SS*0.05),int(W*SS*0.95)),rng.randint(int(H*SS*0.05),int(H*SS*0.95))
            r=int(SS*(0.8+1.6*a)); col=tuple(int(v*a) for v in (255,255,255))
            cv2.line(S,(x-r,y),(x+r,y),col,max(1,SS//4),cv2.LINE_AA); cv2.line(S,(x,y-r),(x,y+r),col,max(1,SS//4),cv2.LINE_AA)
    return S
small=lambda S: cv2.resize(S,(W,H),interpolation=cv2.INTER_AREA)
p=subprocess.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W*UP}x{H*UP}","-r",str(FPS),"-i","-",
    "-c:v","libx264","-crf","10","-pix_fmt","yuv420p","-movflags","+faststart",OUT],stdin=subprocess.PIPE)
for k in range(T): p.stdin.write(cv2.resize(small(frame(k/FPS)),(W*UP,H*UP),interpolation=cv2.INTER_NEAREST).tobytes())
p.stdin.close(); p.wait()
rows=[]
for t0 in (30.0,30.07,30.14,30.21):       # four moments across one beat
    a=cv2.resize(small(frame(t0+beats[np.searchsorted(beats,30)] - 30 + 0.0)),(W*8,H*8),interpolation=cv2.INTER_NEAREST); a[::8]=0; a[:,::8]=0
    rows.append(a); rows.append(np.zeros((8,W*8,3),np.uint8))
tb=beats[np.searchsorted(beats,30)]; rows=[]
for dt in (0.0,0.11,0.22,0.33):
    a=cv2.resize(small(frame(tb+dt)),(W*8,H*8),interpolation=cv2.INTER_NEAREST); a[::8]=0; a[:,::8]=0
    rows.append(a); rows.append(np.zeros((8,W*8,3),np.uint8))
cv2.imwrite(PREV,cv2.cvtColor(np.vstack(rows),cv2.COLOR_RGB2BGR))
