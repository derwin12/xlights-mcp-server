import numpy as np, cv2, subprocess, sys
sys.path.insert(0,str(__import__("pathlib").Path(__file__).resolve().parents[2]/"src"))
from xlights_mcp.audio.beats import detect_beats
AUDIO,OUTL,OUTR,PREV=sys.argv[1:5]
W,H,FPS,SS,UP=8,40,30,8,10
bm=detect_beats(AUDIO); beats=np.array(bm.beat_times_ms)/1000.0; bpb=bm.beats_per_bar
T=int(211*FPS); SEG=16                                   # 16 beats = 4 bars per block
ORN=[(255,70,110),(90,255,170),(255,215,90),(120,170,255)]
def state(t):
    i=np.searchsorted(beats,t,side="right")-1
    if i<0: return -1,0.0,0.44
    per=(beats[i+1]-beats[i]) if i+1<len(beats) else 0.44
    return i,t-beats[i],per
yy,xx=np.mgrid[0:H*SS,0:W*SS].astype(np.float32)/SS
def pole(t,direction):
    i,ph,per=state(t); c=(1-np.exp(-6*per))/6
    phase=2.2*t+14*((max(i,-1)+1)*c+(1-np.exp(-6*ph))/6)          # scroll speed + a surge on each beat
    s=((yy*direction+xx*1.0+phase*direction*-1)%14)<7
    shade=0.62+0.38*np.cos((xx-W/2)/(W/2)*np.pi/2)                  # round-pole shading
    img=np.where(s[...,None],np.array([235,25,45],np.float32),np.array([255,255,255],np.float32))*shade[...,None]
    return np.clip(img*(0.82+0.18*np.exp(-ph*6)),0,255).astype(np.uint8)
def snow(t,off):
    i,ph,per=state(t); S=np.zeros((H*SS,W*SS,3),np.uint8)
    rng=np.random.RandomState(3+off)
    for _ in range(16):
        x=rng.uniform(0,W); sp=rng.uniform(3,9); y=(rng.uniform(0,H)+t*sp)%H; r=0.5+sp/14
        cv2.circle(S,(int(x*SS),int(y*SS)),int(r*SS*0.6),(int(120+sp*15),)*3,-1,cv2.LINE_AA)
    # ornament: one bounce per beat, drops from the top and bounces off the bottom
    tau=((t-beats[i])/per if i>=0 else 0)+off*0.5; tau=tau%1.0
    y=2.5+(H-5.5)*(1-abs(np.cos(np.pi*tau))**0.7); bar=0 if i<0 else i//bpb; col=ORN[(bar+off)%4]
    cv2.line(S,(int(W/2*SS),0),(int(W/2*SS),int(y*SS)),(150,150,150),max(1,SS//4),cv2.LINE_AA)   # hanger
    cv2.circle(S,(int(W/2*SS),int(y*SS)),int(2.6*SS),col,-1,cv2.LINE_AA); cv2.circle(S,(int(W/2*SS-SS*0.8),int(y*SS-SS*0.9)),int(0.7*SS),(255,255,255),-1,cv2.LINE_AA)
    cv2.rectangle(S,(int((W/2-0.7)*SS),int((y-3.1)*SS)),(int((W/2+0.7)*SS),int((y-2.3)*SS)),(255,215,90),-1)
    return S
def frame(t,which):
    return pole(t,1) if which==0 else snow(t,0)        # left: barber pole (scrolls up); right: snow + bouncing ornament
def enc(path,which):
    p=subprocess.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W*UP}x{H*UP}","-r",str(FPS),"-i","-",
        "-c:v","libx264","-crf","10","-pix_fmt","yuv420p","-movflags","+faststart",path],stdin=subprocess.PIPE)
    for k in range(T): p.stdin.write(cv2.resize(cv2.resize(frame(k/FPS,which),(W,H),interpolation=cv2.INTER_AREA),(W*UP,H*UP),interpolation=cv2.INTER_NEAREST).tobytes())
    p.stdin.close(); p.wait()
enc(OUTL,0); enc(OUTR,1)
# preview: 4 moments in a pole block, 4 moments in a snow block (L then R side by side)
tp=beats[8]; ts=beats[SEG+2]; cols=[]
for tt in (tp,tp+0.12,tp+0.5,tp+1.0, ts,ts+0.2,ts+0.4,ts+0.6):
    pair=[]
    for w in (0,1):
        a=cv2.resize(cv2.resize(frame(tt,w),(W,H),interpolation=cv2.INTER_AREA),(W*8,H*8),interpolation=cv2.INTER_NEAREST); a[::8]=0; a[:,::8]=0; pair+= [a,np.zeros((H*8,6,3),np.uint8)]
    cols+=[np.hstack(pair),np.zeros((H*8,16,3),np.uint8)]
cv2.imwrite(PREV,cv2.cvtColor(np.hstack(cols),cv2.COLOR_RGB2BGR))
