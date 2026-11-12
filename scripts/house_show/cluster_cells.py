import cv2, numpy as np, pickle, sys
from scipy import ndimage as ndi
from sklearn.cluster import AgglomerativeClustering, KMeans
S=sys.argv[1]; K=int(sys.argv[2])
F=np.load(S+"/F.npy",mmap_mode="r"); lab,keep,fps=pickle.load(open(S+"/seg.pkl","rb"))
T=F.shape[0]; B=8
H,W=360//B,640//B
# per-cell signal: mean of max-channel, plus mean hue-ish via R-G-B means
sig=np.zeros((T,H,W,3),np.float32)
for t in range(T):
    sig[t]=np.asarray(F[t],np.float32).reshape(H,B,W,B,3).mean(axis=(1,3))
np.save(S+"/cells.npy",sig)
g=sig.max(axis=3)  # T,H,W
sd=g.std(axis=0)
house=(lab>0)
# exclude ornament comps (small ones): keep only largest component
sizes=ndi.sum(lab>0,lab,range(1,lab.max()+1)); big=np.argmax(sizes)+1
mask=(lab==big).reshape(H,B,W,B).mean(axis=(1,3))>0.3
mask&=sd>6
ys,xs=np.where(mask); print("cells",len(ys))
X=g[:,ys,xs].T  # N,T
X=X-X.mean(1,keepdims=True); X/= (np.linalg.norm(X,axis=1,keepdims=True)+1e-6)
# add color channel signature
col=sig[:,ys,xs,:].mean(0); col=col/(col.sum(1,keepdims=True)+1e-6)
km=KMeans(K,n_init=4,random_state=0).fit(X)
cl=km.labels_
out=np.full((H,W),-1); out[ys,xs]=cl
pickle.dump((out,),open(S+"/clus.pkl","wb"))
img=np.zeros((H,W,3),np.uint8)
rng=np.random.RandomState(1); cols=rng.randint(60,255,(K,3))
for k in range(K): img[out==k]=cols[k]
img=cv2.resize(img,(1280,720),interpolation=cv2.INTER_NEAREST)
for k in range(K):
    yy,xx=np.where(out==k)
    cv2.putText(img,str(k),(int(xx.mean()*16+8),int(yy.mean()*16+8)),0,0.6,(255,255,255),2)
cv2.imwrite(S+"/clus.png",img)
