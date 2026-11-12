import numpy as np, cv2, subprocess, sys
sys.path.insert(0,str(__import__("pathlib").Path(__file__).resolve().parents[2]/"src"))
from xlights_mcp.audio.beats import detect_beats
AUDIO,OUT,PREV=sys.argv[1:4]
W,H,FPS,SS,UP=96,16,30,6,8
bm=detect_beats(AUDIO); beats=np.array(bm.beat_times_ms)/1000.0; bpb=bm.beats_per_bar
T=int(211*FPS); rng=np.random.RandomState(11)
PAL=[(255,70,110),(90,255,170),(255,255,255),(255,215,90),(120,170,255)]
P=lambda x,y:(int(round(x*SS)),int(round(y*SS)))
class Shape:
    def __init__(s,kind,size,col):
        s.kind,s.size,s.col=kind,size,col
        s.x,s.y=rng.uniform(size,W-size),rng.uniform(size*0.6,H-size*0.6)
        a=rng.uniform(0,2*np.pi); sp=rng.uniform(14,26); s.vx,s.vy=sp*np.cos(a),sp*np.sin(a)*0.6
        s.rot=rng.uniform(0,6.28); s.spin=rng.uniform(-1.6,1.6)*(1 if kind=="tri" else 0.5)
    def step(s,dt,boost):
        k=1+boost
        s.x+=s.vx*dt*k; s.y+=s.vy*dt*k; s.rot+=s.spin*dt*(1+boost*2)
        m=s.size*0.55 if s.kind=="tri" else s.size*0.5
        if s.x<m: s.x=m; s.vx=abs(s.vx)
        if s.x>W-m: s.x=W-m; s.vx=-abs(s.vx)
        if s.y<m*0.7: s.y=m*0.7; s.vy=abs(s.vy)
        if s.y>H-m*0.7: s.y=H-m*0.7; s.vy=-abs(s.vy)
    def draw(s,S,col,glow):
        c=tuple(int(min(255,v*(0.7+0.3*glow)+60*glow)) for v in col)
        if s.kind=="tri":
            pts=np.array([P(s.x+s.size*0.62*np.cos(s.rot+k*2.094),s.y+s.size*0.62*np.sin(s.rot+k*2.094)) for k in range(3)],np.int32)
            cv2.polylines(S,[pts],True,c,max(1,int(SS*0.8)),cv2.LINE_AA)
        else:
            dx,dy=np.cos(s.rot)*s.size*0.5,np.sin(s.rot)*s.size*0.5
            cv2.line(S,P(s.x-dx,s.y-dy),P(s.x+dx,s.y+dy),c,max(1,int(SS*0.7)),cv2.LINE_AA)
shapes=[Shape("tri",7,0),Shape("tri",5,1),Shape("tri",8,2),Shape("line",13,3),Shape("line",10,4),Shape("line",15,0)]
def beatstate(t):
    i=np.searchsorted(beats,t,side="right")-1
    return (-1,9.0) if i<0 else (i,t-beats[i])
def run():
    trail=np.zeros((H*SS,W*SS,3),np.float32); frames=[]; prev_i=-2
    for k in range(T):
        t=k/FPS; i,ph=beatstate(t); pulse=np.exp(-ph*6); bar=0 if i<0 else i//bpb
        if i!=prev_i:                                    # on every beat: shove velocities a little
            for s in shapes:
                a=rng.uniform(-0.5,0.5); c,sn=np.cos(a),np.sin(a); s.vx,s.vy=s.vx*c-s.vy*sn,s.vx*sn+s.vy*c
            prev_i=i
        trail*=0.62
        S=np.zeros_like(trail,dtype=np.uint8)
        for n,s in enumerate(shapes):
            s.step(1/FPS,1.6*pulse); s.draw(S,PAL[(s.col+bar)%len(PAL)],pulse)
        trail=np.maximum(trail,S.astype(np.float32))
        frames.append(np.clip(trail,0,255).astype(np.uint8))
        yield frames[-1]
def small(S): return cv2.resize(S,(W,H),interpolation=cv2.INTER_AREA)
p=subprocess.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W*UP}x{H*UP}","-r",str(FPS),"-i","-",
    "-c:v","libx264","-crf","10","-pix_fmt","yuv420p","-movflags","+faststart",OUT],stdin=subprocess.PIPE)
keep={}
for k,fr in enumerate(run()):
    im=small(fr); p.stdin.write(cv2.resize(im,(W*UP,H*UP),interpolation=cv2.INTER_NEAREST).tobytes())
    if k in (int(40*FPS),int(40.4*FPS),int(80*FPS),int(80.4*FPS),int(130*FPS),int(130.4*FPS)): keep[k]=im
p.stdin.close(); p.wait()
rows=[]
for k in sorted(keep):
    a=cv2.resize(keep[k],(W*8,H*8),interpolation=cv2.INTER_NEAREST); a[::8]=0; a[:,::8]=0; rows+=[a,np.zeros((8,W*8,3),np.uint8)]
cv2.imwrite(PREV,cv2.cvtColor(np.vstack(rows),cv2.COLOR_RGB2BGR))
