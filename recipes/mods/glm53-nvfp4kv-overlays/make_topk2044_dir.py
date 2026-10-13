import os,glob,json
hub=os.path.expanduser("~/.cache/huggingface")
snap=glob.glob(hub+"/hub/models--drowzeys--keys-GLM-5.3-Flash-NVFP4-ablit-l15-43-mtp-l45/snapshots/cecebc0ff0bbce8eefaa19667290a79d0216cd0e")[0]
dst=hub+"/spark-forge-local/glm53-flash-ablit-topk2044"; os.makedirs(dst,exist_ok=True)
n=0
for f in os.listdir(snap):
    s=os.path.join(snap,f); d=os.path.join(dst,f)
    if os.path.isdir(s) or f=="config.json" or os.path.exists(d): continue
    os.link(os.path.realpath(s),d); n+=1
c=json.load(open(os.path.join(snap,"config.json"))); tc=c.get("text_config",c); old=tc.get("index_topk"); tc["index_topk"]=2044
json.dump(c,open(os.path.join(dst,"config.json"),"w"),indent=2)
w=sum(os.path.getsize(os.path.join(dst,f)) for f in os.listdir(dst) if f.endswith(".safetensors"))
print(os.uname().nodename,"linked",n,"index_topk",old,"->",2044,"in","text_config" if "text_config" in c else "root","weights GiB %.1f"%(w/2**30))
