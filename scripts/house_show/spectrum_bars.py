import numpy as np, librosa, cv2, subprocess, sys
AUDIO,OUT,PREVIEW=sys.argv[1],sys.argv[2],sys.argv[3]
W,H,FPS,NB,SCALE=96,16,30,32,4          # 32 bars x (2px bar + 1px gap) = 96 px
y,sr=librosa.load(AUDIO,sr=22050,mono=True)
hop=sr//FPS; nfft=2048
S=np.abs(librosa.stft(y,n_fft=nfft,hop_length=hop))**2
freqs=librosa.fft_frequencies(sr=sr,n_fft=nfft)
edges=np.geomspace(45,10000,NB+1)
bands=np.zeros((NB,S.shape[1]),np.float32)
for i in range(NB):
    m=(freqs>=edges[i])&(freqs<edges[i+1])
    if not m.any(): m=np.argmin(abs(freqs-np.sqrt(edges[i]*edges[i+1])))
    bands[i]=S[m].mean(0) if np.ndim(m)>0 and m.dtype==bool else S[m]
db=10*np.log10(bands+1e-9)
# per-band normalisation so low and high bands both move (pink-ish tilt), then global range
lo=np.percentile(db,10,axis=1,keepdims=True); hi=np.percentile(db,99.5,axis=1,keepdims=True)
lvl=np.clip((db-lo)/(hi-lo+1e-6),0,1)
# attack fast, decay slow; peak-hold caps
sm=np.zeros_like(lvl); pk=np.zeros_like(lvl); hold=np.zeros(NB); cur=np.zeros(NB); pcur=np.zeros(NB)
for t in range(lvl.shape[1]):
    cur=np.where(lvl[:,t]>cur,cur+(lvl[:,t]-cur)*0.8,cur-0.12)
    cur=np.clip(cur,0,1); sm[:,t]=cur
    up=cur>pcur; pcur=np.where(up,cur,pcur); hold=np.where(up,6,hold-1)
    pcur=np.where(hold<=0,pcur-0.05,pcur); pcur=np.clip(pcur,0,1); pk[:,t]=pcur
# colours bottom->top: green -> yellow -> white -> red tip (christmas-y neon); peak cap white
STOPS=[(0.0,(150,235,190)),(0.35,(190,240,200)),(0.55,(255,238,170)),(0.78,(255,185,205)),(1.0,(205,175,255))]  # mint > butter > blush > lavender
def rowcolor(r):                         # r=0 bottom .. H-1 top
    f=r/(H-1)
    for (f0,c0),(f1,c1) in zip(STOPS,STOPS[1:]):
        if f<=f1:
            u=(f-f0)/(f1-f0); return tuple(int(round(a+(b-a)*u)) for a,b in zip(c0,c1))
    return STOPS[-1][1]
def frame(t):
    im=np.zeros((H,W,3),np.uint8)
    for b in range(NB):
        h=int(round(sm[b,t]*H)); x=b*3
        for r in range(h): im[H-1-r,x:x+2]=rowcolor(r)
        c=int(round(pk[b,t]*H))
        if c>h and c>0: im[H-c,x:x+2]=(255,248,235)
    return im
T=lvl.shape[1]; print("frames",T,"dur",T/FPS)
p=subprocess.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W*SCALE}x{H*SCALE}","-r",str(FPS),"-i","-",
    "-c:v","libx264","-crf","10","-pix_fmt","yuv420p","-movflags","+faststart",OUT],stdin=subprocess.PIPE)
for t in range(T):
    p.stdin.write(cv2.resize(frame(t),(W*SCALE,H*SCALE),interpolation=cv2.INTER_NEAREST).tobytes())
p.stdin.close(); p.wait()
# preview strip: 4 moments, shown large with a dark pixel grid like a real matrix
rows=[]
for sec in (20,70,120,170):
    f=cv2.resize(frame(int(sec*FPS)),(W*10,H*10),interpolation=cv2.INTER_NEAREST); f[::10]=0; f[:,::10]=0
    rows.append(f); rows.append(np.zeros((10,W*10,3),np.uint8))
cv2.imwrite(PREVIEW,cv2.cvtColor(np.vstack(rows),cv2.COLOR_RGB2BGR))
