import numpy as np, librosa, sys
sys.path.insert(0,str(__import__("pathlib").Path(__file__).resolve().parents[2]/"src"))
from xlights_mcp.audio.beats import detect_beats
LAB={"CALM":"Calm: slow sweep, soft colours","GROOVE":"Groove: steady chase, light flicks","BUILD":"Build: open the fan, rising tilt","DROP":"Drop: tight beams, strobe + chase"}
def sections(audio):
    bm=detect_beats(audio); beats=np.array(bm.beat_times_ms,float); bpb=bm.beats_per_bar
    y,sr=librosa.load(audio,sr=22050,mono=True); hop=512
    rms=librosa.feature.rms(y=y,hop_length=hop)[0]; tt=librosa.frames_to_time(np.arange(len(rms)),sr=sr,hop_length=hop)*1000
    S=np.abs(librosa.stft(y,n_fft=2048,hop_length=hop)); fr=librosa.fft_frequencies(sr=sr,n_fft=2048)
    low=S[fr<150].mean(0); high=S[fr>4000].mean(0)
    nb=len(beats)//bpb; F=[]
    for k in range(nb):
        m=(tt>=beats[k*bpb])&(tt<beats[min((k+1)*bpb,len(beats)-1)])
        F.append([rms[m].mean(),low[m].mean(),high[m].mean()] if m.any() else [0,0,0])
    F=np.array(F)
    for c in range(3): F[:,c]/=np.percentile(F[:,c],95)
    W=4; nov=np.zeros(nb)
    for k in range(W,nb-W+1): nov[k]=np.linalg.norm(F[k:k+W].mean(0)-F[k-W:k].mean(0))
    cuts=[]
    for k in np.argsort(-nov):
        if nov[k]<0.22 or len(cuts)>=9: break
        if all(abs(k-c)>=6 for c in cuts): cuts.append(int(k))
    cuts=[0]+sorted(cuts)+[nb]; segs=[]
    for a,b in zip(cuts,cuts[1:]):
        segs.append([a,b,F[a:b,0].mean()])
    out=[]
    for n,(a,b,r) in enumerate(segs):
        nxt=segs[n+1][2] if n+1<len(segs) else r
        if r<0.5: s="CALM"
        elif r>=0.85: s="DROP"
        elif nxt-r>0.12 and r<0.8: s="BUILD"
        else: s="GROOVE"
        out.append((s,a,b))
    return beats,bpb,nb,out
def mh_tracks(audio, plan, total_ms):
    beats,bpb,nb,secs=sections(audio); snap=lambda ms:int(round(ms/25))*25
    bar_t=lambda k:beats[min(k*bpb,len(beats)-1)]
    order=[1,2,3,4,5,6,7,8,7,6,5,4,3,2]; rows=[]; prev=None; jc=0   # 14-count bounce: each end head once per sweep
    for bi in range(0,len(beats)-1):                          # Beats (1-2-3-4) and Bars tracks from the same grid as the chase marks
        st=snap(beats[bi]); en=snap(beats[bi+1]); plan.label("Beats",str(bi%bpb+1),st,max(en,st+25))
    for k in range(nb):
        st=snap(bar_t(k)); en=snap(bar_t(k+1)) if k+1<nb else snap(beats[-1]); plan.label("Bars",str(k+1),st,max(en,st+25))
    for s,a,b in secs:
        s0=snap(bar_t(a)); e0=snap(bar_t(b)) if b<nb else int(total_ms)
        plan.label("MH Sections",LAB[s],s0,e0); rows.append((s,a,b,s0/1000,e0/1000))
        if s in ("GROOVE","DROP"):
            if prev not in ("GROOVE","DROP"): jc=0               # restart the sweep after a calm/build; otherwise keep going
            for bi in range(a*bpb,min(b*bpb,len(beats)-1)):
                st=snap(beats[bi]); en=snap(beats[bi+1]) if bi+1<len(beats) else st+400
                plan.label("MH Chase",f"MH-{order[jc%len(order)]}",st,max(en,st+25)); jc+=1
            step=2 if s=="DROP" else 4
            for bar in range(a,b):
                if (bar-a)%step==0:
                    st=snap(bar_t(bar)); plan.label("MH Accents","flick: tilt kick on all heads",st,st+250)
        if s=="BUILD":
            st=snap(bar_t(b-1)); en=snap(bar_t(b)) if b<nb else st+1800; plan.label("MH Accents","strobe: shutter strobe, building",st,en)
        if s=="DROP" or (prev=="CALM" and s!="CALM"):
            st=snap(bar_t(a)); plan.label("MH Accents","strobe: hit, all heads",st,snap(beats[a*bpb+1]))
        prev=s
    return rows
