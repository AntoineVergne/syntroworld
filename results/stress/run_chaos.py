# Stress test of the model-brain path with a hostile offline "model" (synw/brains/chaos.py).
# Run from the repository root: python results/stress/run_chaos.py
import time, traceback
from collections import Counter
from synw.brains.chaos import ChaosTransport
from synw.config import load
from synw.runner import World
worlds=["worlds/a.yaml","worlds/b.yaml","worlds/c.yaml","worlds/a-text.yaml","worlds/size40/b.yaml","worlds/ablations/b-nolot.yaml"]
for wf in worlds:
    for seed in (1,2,3):
        t=time.time()
        try:
            tr=ChaosTransport(seed, bad_share=0.3)
            w=World(load(wf),seed,arm="full",brain={"type":"model","transport":tr,"budget_tokens":10**12})
            tr.world=w
            w.run()
            c=Counter(e["type"] for e in w.log.events)
            calls=Counter(e["payload"]["call"] for e in w.log.events if e["type"]=="model_call")
            print(wf,seed,"ok",round(time.time()-t,1),"s",dict(calls),"invalid",c["invalid_action"]+c["invalid_output"],"decisions",c["decision"],"departures",c["departure"],"rogue",sum(1 for e in w.log.events if e["type"]=="shock" and e["payload"].get("shock")=="rogue"))
        except Exception:
            print(wf,seed,"CRASH"); traceback.print_exc(limit=8)
