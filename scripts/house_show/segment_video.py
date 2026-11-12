import cv2, numpy as np, sys, pickle
from scipy import ndimage as ndi
V=r"C:\Users\daryl\.cache\xlights-mcp\videos\vtZ5pX00MfI.mp4"
S=sys.argv[1]
cap=cv2.VideoCapture(V); fps=cap.get(cv2.CAP_PROP_FPS)
frames=[]
while True:
    ok,f=cap.read()
    if not ok: break
    frames.append(cv2.resize(f,(640,360),interpolation=cv2.INTER_AREA))
F=np.array(frames); print(F.shape,fps)
np.save(S+"/F.npy",F)
g=F.max(axis=3).astype(np.float32)
std=g.std(axis=0); mx=g.max(axis=0)
act=(std>18)
act=ndi.binary_opening(act)
act=ndi.binary_dilation(act,iterations=2)
lab,n=ndi.label(act); print("components",n)
sizes=ndi.sum(act,lab,range(1,n+1))
keep=[i+1 for i,s in enumerate(sizes) if s>=30]
print(len(keep))
vis=cv2.cvtColor(np.clip(mx,0,255).astype(np.uint8),cv2.COLOR_GRAY2BGR)
for k,i in enumerate(keep):
    ys,xs=np.where(lab==i); cv2.putText(vis,str(k),(int(xs.mean()),int(ys.mean())),0,0.4,(0,255,255),1)
    vis[lab==i]=(vis[lab==i]*0.5+np.array([0,60,0])).astype(np.uint8)
cv2.imwrite(S+"/seg.png",cv2.resize(vis,(1280,720)))
pickle.dump((lab,keep,fps),open(S+"/seg.pkl","wb"))
