import numpy as np, cv2, subprocess, sys
sys.path.insert(0,str(__import__("pathlib").Path(__file__).resolve().parents[2]/"src"))
from xlights_mcp.audio.beats import detect_beats
AUDIO,OUTL,OUTR,PREV=sys.argv[1:5]
W,H,FPS,SS,UP=48,27,30,8,10
bm=detect_beats(AUDIO); beats=np.array(bm.beat_times_ms)/1000.0; bpb=bm.beats_per_bar
dur=211.0; T=int(dur*FPS)
COLS=[(255,30,50),(0,255,90),(255,255,255),(255,60,255)]   # RGB: red, green, white, magenta accent
def state(t):
    i=np.searchsorted(beats,t,side="right")-1
    ph=0.0 if i<0 else t-beats[i]; bar=0 if i<0 else i//bpb
    return i,ph,bar
def snow(t):
    i,ph,bar=state(t); pulse=np.exp(-ph*5)
    S=np.zeros((H*SS,W*SS,3),np.uint8); cx,cy=W*SS/2,H*SS/2
    c=COLS[bar%3]; R=(H*SS/2)*(0.62+0.30*pulse); ang0=t*0.35
    th=max(1,int(SS*(1.0+0.6*pulse)))
    for k in range(6):
        a=ang0+k*np.pi/3; ux,uy=np.cos(a),np.sin(a)
        end=(cx+ux*R,cy+uy*R); cv2.line(S,(int(cx),int(cy)),(int(end[0]),int(end[1])),c,th,cv2.LINE_AA)
        for f,L in ((0.45,0.38),(0.72,0.26)):
            bx,by=cx+ux*R*f,cy+uy*R*f
            for s in (-1,1):
                b=a+s*np.pi/3; ex,ey=bx+np.cos(b)*R*L,by+np.sin(b)*R*L
                cv2.line(S,(int(bx),int(by)),(int(ex),int(ey)),c,max(1,th-SS//2),cv2.LINE_AA)
    cv2.circle(S,(int(cx),int(cy)),int(SS*(1.2+1.5*pulse)),(255,255,255),-1,cv2.LINE_AA)
    return S
def rings(t):
    i,ph,bar=state(t); S=np.zeros((H*SS,W*SS,3),np.uint8); cx,cy=W*SS/2,H*SS/2
    for j in range(0,4):
        if i-j<0: continue
        age=t-beats[i-j]
        if age>1.4: continue
        r=age*W*SS*0.55; fade=max(0.0,1-age/1.4); c=COLS[((i-j)//bpb)%3]
        col=tuple(int(v*fade) for v in c); cv2.ellipse(S,(int(cx),int(cy)),(int(r),int(r*0.62)),0,0,360,col,max(1,int(SS*1.6)),cv2.LINE_AA)
    pulse=np.exp(-ph*6); cv2.circle(S,(int(cx),int(cy)),int(SS*(1.0+2.2*pulse)),COLS[bar%3] if pulse>0.3 else (255,255,255),-1,cv2.LINE_AA)
    return S
def small(S): return cv2.resize(S,(W,H),interpolation=cv2.INTER_AREA)
def enc(path,fn):
    p=subprocess.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W*UP}x{H*UP}","-r",str(FPS),"-i","-",
        "-c:v","libx264","-crf","10","-pix_fmt","yuv420p","-movflags","+faststart",path],stdin=subprocess.PIPE)
    for k in range(T): p.stdin.write(cv2.resize(small(fn(k/FPS)),(W*UP,H*UP),interpolation=cv2.INTER_NEAREST).tobytes())
    p.stdin.close(); p.wait()
enc(OUTL,snow); enc(OUTR,rings)
rows=[]
for sec in (30.1,80.3,130.2,170.4):
    a=cv2.resize(small(snow(sec)),(W*8,H*8),interpolation=cv2.INTER_NEAREST); b=cv2.resize(small(rings(sec)),(W*8,H*8),interpolation=cv2.INTER_NEAREST)
    for im in (a,b): im[::8]=0; im[:,::8]=0
    rows.append(np.hstack([a,np.zeros((H*8,12,3),np.uint8),b])); rows.append(np.zeros((8,rows[-1].shape[1],3),np.uint8))
cv2.imwrite(PREV,cv2.cvtColor(np.vstack(rows),cv2.COLOR_RGB2BGR)); print("beats",len(beats),"bpb",bpb)
