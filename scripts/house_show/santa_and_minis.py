import numpy as np, cv2, subprocess, sys
sys.path.insert(0,str(__import__("pathlib").Path(__file__).resolve().parents[2]/"src"))
from xlights_mcp.audio.beats import detect_beats
AUDIO,OUT_SANTA,OUT_MINI,PREV=sys.argv[1:5]
FPS,SS,UP=30,8,10
bm=detect_beats(AUDIO); beats=np.array(bm.beat_times_ms)/1000.0; bpb=bm.beats_per_bar
T=int(211*FPS)
COLS=[(255,30,50),(0,255,90),(255,255,255)]
def state(t):
    i=np.searchsorted(beats,t,side="right")-1
    if i<0: return -1,0.0,0.0
    per=(beats[i+1]-beats[i]) if i+1<len(beats) else 0.44
    return i,t-beats[i],i+(t-beats[i])/per
P=lambda x,y:(int(round(x*SS)),int(round(y*SS)))
def ell(S,c,ax,col): cv2.ellipse(S,P(*c),(int(ax[0]*SS),int(ax[1]*SS)),0,0,360,col,-1,cv2.LINE_AA)
def poly(S,pts,col): cv2.fillPoly(S,[np.array([P(*p) for p in pts],np.int32)],col,cv2.LINE_AA)
FONT={"H":["101","101","111","101","101"],"O":["111","101","101","101","111"]}
def text(S,word,x0,y0,col):
    for ci,ch in enumerate(word):
        for ry,row in enumerate(FONT[ch]):
            for rx,b in enumerate(row):
                if b=="1": cv2.rectangle(S,P(x0+ci*4+rx,y0+ry),P(x0+ci*4+rx+1,y0+ry+1),col,-1)
def santa(t):
    i,ph,bp=state(t); pulse=np.exp(-ph*6); bar=0 if i<0 else i//bpb; beat_in_bar=0 if i<0 else i%bpb
    S=np.zeros((27*SS,48*SS,3),np.uint8)
    rng=np.random.RandomState(5)                                    # falling snow behind everything
    for _ in range(14):
        x=rng.uniform(0,48); sp=rng.uniform(2.5,5.5); y0=rng.uniform(0,27); y=(y0+t*sp)%27
        cv2.rectangle(S,P(int(x),int(y)),P(int(x)+1,int(y)+1),(90,90,110),-1)
    ox=3.0
    # coat + white trim
    poly(S,[(ox+3,27),(ox+5.5,21),(ox+18.5,21),(ox+21,27)],(215,20,40)); cv2.rectangle(S,P(ox+11,21.5),P(ox+13,27),(255,255,255),-1)
    # waving arm (behind the beard, outside the face)
    sh=(ox+19.0,22.8); th=0.38*np.sin(2*np.pi*bp); R=9.0
    hand=(sh[0]+R*np.sin(th+0.55),sh[1]-R*np.cos(th+0.55))
    cv2.line(S,P(*sh),P(*hand),(215,20,40),int(2.6*SS),cv2.LINE_AA)
    cuff=(sh[0]+(hand[0]-sh[0])*0.82,sh[1]+(hand[1]-sh[1])*0.82); ell(S,cuff,(1.6,1.6),(255,255,255)); ell(S,hand,(1.7,1.7),(255,255,255))
    # beard, face, mustache, nose, mouth, eyes, cheeks
    ell(S,(ox+12,19.0),(7.2,5.6),(255,255,255))
    ell(S,(ox+12,12.8),(5.3,4.6),(255,205,170))
    ell(S,(ox+9.4,16.2),(2.7,1.3),(255,255,255)); ell(S,(ox+14.6,16.2),(2.7,1.3),(255,255,255))
    ell(S,(ox+12,14.6),(1.1,1.0),(255,140,150)); ell(S,(ox+12,18.2),(1.3,0.6),(190,40,70))
    ell(S,(ox+8.0,14.2),(1.1,0.9),(255,150,150)); ell(S,(ox+16.0,14.2),(1.1,0.9),(255,150,150))
    if (t%4.0)>0.14:
        ell(S,(ox+9.8,12.2),(0.95,0.95),(25,25,40)); ell(S,(ox+14.2,12.2),(0.95,0.95),(25,25,40))
    else:
        cv2.line(S,P(ox+9.0,12.3),P(ox+10.6,12.3),(60,40,40),SS//2,cv2.LINE_AA); cv2.line(S,P(ox+13.4,12.3),P(ox+15.0,12.3),(60,40,40),SS//2,cv2.LINE_AA)
    # hat with fur trim and bouncing pom-pom
    bounce=1.4*pulse
    poly(S,[(ox+6.6,9.3),(ox+17.4,9.3),(ox+14.6,3.6),(ox+19.2,5.0-bounce*0.4)],(215,20,40))
    cv2.rectangle(S,P(ox+6.4,8.2),P(ox+17.6,10.3),(255,255,255),-1); ell(S,(ox+6.4,9.25),(1.05,1.05),(255,255,255)); ell(S,(ox+17.6,9.25),(1.05,1.05),(255,255,255))
    ell(S,(ox+19.4,5.2-bounce),(1.7+0.3*pulse,1.7+0.3*pulse),(255,255,255))
    # HO HO HO: one line per beat, all three on beat 4
    col=COLS[bar%3]; dim=tuple(int(c*0.12) for c in col)
    for ln in range(3):
        lit=(beat_in_bar==ln) or (beat_in_bar==3)
        c=tuple(int(v*(0.55+0.45*pulse)) for v in col) if lit else dim
        text(S,"HO",31.0,2.0+ln*8.0,c)
    return S
def flake(S,cx,cy,R,ang,c,th):
    for k in range(6):
        a=ang+k*np.pi/3; ux,uy=np.cos(a),np.sin(a)
        cv2.line(S,P(cx,cy),P(cx+ux*R,cy+uy*R),c,th,cv2.LINE_AA)
        for f,L in ((0.5,0.38),(0.78,0.26)):
            bx,by=cx+ux*R*f,cy+uy*R*f
            for s in (-1,1):
                b=a+s*np.pi/3; cv2.line(S,P(bx,by),P(bx+np.cos(b)*R*L,by+np.sin(b)*R*L),c,max(1,th-2),cv2.LINE_AA)
def mini_cycle(t):
    i,ph,bp=state(t); pulse=np.exp(-ph*5); bar=0 if i<0 else i//bpb
    S=np.zeros((12*SS,50*SS,3),np.uint8)
    act=(i%3) if i>=0 else 0; prev=(act-1)%3             # one flake per beat: left, centre, right, repeat
    for n,(cx,d) in enumerate(((8.5,1),(25,-1),(41.5,1))):
        if n==act: k=1.0
        elif n==prev and i>0: k=max(0.0,1-ph*5)*0.55          # the last flake fades out as the next one lights
        else: continue
        base=COLS[bar%3]; c=tuple(int(v*k) for v in base); R=5.3*(0.82+0.18*pulse*(1 if n==act else 0))
        flake(S,cx,6.0,R,d*t*0.45+n,c,max(2,int(SS*(0.9+0.4*pulse*(1 if n==act else 0)))))
        cv2.circle(S,P(cx,6.0),int(SS*(0.7+0.7*pulse*(1 if n==act else 0))),tuple(int(255*k) for _ in range(3)),-1,cv2.LINE_AA)
    return S
def mini_all(t):                                          # the original: all three flakes pulse together
    i,ph,bp=state(t); pulse=np.exp(-ph*5); bar=0 if i<0 else i//bpb
    S=np.zeros((12*SS,50*SS,3),np.uint8)
    for n,(cx,d) in enumerate(((8.5,1),(25,-1),(41.5,1))):
        c=COLS[(bar+n)%3]; R=5.3*(0.82+0.18*pulse)
        flake(S,cx,6.0,R,d*t*0.45+n,c,max(2,int(SS*(0.9+0.4*pulse)))); cv2.circle(S,P(cx,6.0),int(SS*(0.7+0.7*pulse)),(255,255,255),-1,cv2.LINE_AA)
    return S
mini=mini_cycle
def enc(path,fn,W,H):
    p=subprocess.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W*UP}x{H*UP}","-r",str(FPS),"-i","-",
        "-c:v","libx264","-crf","10","-pix_fmt","yuv420p","-movflags","+faststart",path],stdin=subprocess.PIPE)
    for k in range(T): p.stdin.write(cv2.resize(cv2.resize(fn(k/FPS),(W,H),interpolation=cv2.INTER_AREA),(W*UP,H*UP),interpolation=cv2.INTER_NEAREST).tobytes())
    p.stdin.close(); p.wait()
if len(sys.argv)<6 or sys.argv[5]!='mini': enc(OUT_SANTA,santa,48,27)
enc(OUT_MINI,mini_all,50,12); enc(OUT_MINI.replace('Mini Snowflakes','Mini Snowflakes Cycle'),mini_cycle,50,12)
tb=beats[np.searchsorted(beats,40)]; tb=tb-(np.searchsorted(beats,40)%bpb)*0.0
i0=np.searchsorted(beats,40); i0=i0-(i0%bpb); rows=[]
for j in range(4):
    a=cv2.resize(cv2.resize(santa(beats[i0+j]+0.02),(48,27),interpolation=cv2.INTER_AREA),(48*8,27*8),interpolation=cv2.INTER_NEAREST); a[::8]=0; a[:,::8]=0
    rows.append(a); rows.append(np.zeros((8,48*8,3),np.uint8))
left=np.vstack(rows); rows=[]
for j in range(4):
    a=cv2.resize(cv2.resize(mini(beats[i0+j]+0.02),(50,12),interpolation=cv2.INTER_AREA),(50*8,12*8),interpolation=cv2.INTER_NEAREST); a[::8]=0; a[:,::8]=0
    rows.append(a); rows.append(np.zeros((8,50*8,3),np.uint8))
right=np.vstack(rows); pad=np.zeros((left.shape[0]-right.shape[0],right.shape[1],3),np.uint8)
cv2.imwrite(PREV,cv2.cvtColor(np.hstack([left,np.zeros((left.shape[0],16,3),np.uint8),np.vstack([right,pad])]),cv2.COLOR_RGB2BGR))
