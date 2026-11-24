"""Run with NumPy 2.3.5 and the UCI Spambase ZIP path as the argument."""
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile
import numpy as np

with zipfile.ZipFile(sys.argv[1]) as archive:
    raw=archive.read("spambase.data")
data=np.loadtxt(io.BytesIO(raw),delimiter=",")
# Exclude ambiguous feature vectors, and keep each remaining vector exactly once.
X,inverse=np.unique(data[:,:-1],axis=0,return_inverse=True)
sums=np.bincount(inverse,weights=data[:,-1])
counts=np.bincount(inverse)
keep=(sums==0)|(sums==counts)
X,y=X[keep],(sums[keep]>0).astype(int)
rng=np.random.default_rng(1123)
parts=[[],[],[]]
for label in (0,1):
    a=rng.permutation(np.flatnonzero(y==label))
    for part,ids in zip(parts,np.split(a,[len(a)*6//10,len(a)*8//10])):
        part.extend(ids)
train,val,test=map(np.array,parts)
X=np.log1p(X)
scale=X[train].std(axis=0)
X=(X-X[train].mean(axis=0))/np.where(scale>0,scale,1)
X=np.column_stack((X,np.ones(len(y))))
w=np.zeros(X.shape[1])
def prob(ids):
    return 1/(1+np.exp(-np.clip(X[ids]@w,-50,50)))
for _ in range(600):
    grad=X[train].T@(prob(train)-y[train])/len(train)
    grad[:-1]+=0.002*w[:-1]
    w-=0.15*grad

def errors(scores,truth,t):
    p=scores>=t
    fp=int(np.sum(p&(truth==0)))
    fn=int(np.sum(~p&(truth==1)))
    return dict(false_alarms=fp,missed_spam=fn,weighted_cost=5*fp+fn)
sv=prob(val)
threshold=min(np.arange(1,100)/100,key=lambda t:(errors(sv,y[val],t)["weighted_cost"],abs(t-.5)))
st=prob(test)
out=dict(source_sha256=hashlib.sha256(raw).hexdigest(),seed=1123,split=[len(i) for i in parts],threshold=float(threshold),default=errors(st,y[test],.5),tuned=errors(st,y[test],threshold),test_scores=st.tolist(),test_labels=y[test].tolist())
Path(__file__).with_name("results.json").write_text(json.dumps(out))
print(out["split"],threshold,out["default"],out["tuned"])
