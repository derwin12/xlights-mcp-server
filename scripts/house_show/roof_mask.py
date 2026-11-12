import cv2, numpy as np, sys
S=sys.argv[1]; F=np.load(S+"/F.npy",mmap_mode="r")
cnt=np.zeros((360,640),np.float32); n=0
for t in range(0,len(F),6):
    h=cv2.cvtColor(np.asarray(F[t]),cv2.COLOR_BGR2HSV)
    cnt+=((h[...,2]>110)&((h[...,0]<8)|(h[...,0]>170))&(h[...,1]>90)); n+=1
reg=np.zeros((360,640),bool); reg[185:247,75:490]=True
c=cnt*reg; thr=np.percentile(c[reg],97)*0.5
m=(c>=max(thr,0.04*n))
m=cv2.morphologyEx(m.astype(np.uint8),cv2.MORPH_CLOSE,np.ones((5,5)))>0
np.save(S+"/roofmask.npy",m); print(n,thr,m.sum())
f=(np.asarray(F[5350])*0.5).astype(np.uint8); f[m]=(0,0,255)
cv2.imwrite(S+"/roof2.png",cv2.resize(f,(1280,720),interpolation=cv2.INTER_NEAREST))
