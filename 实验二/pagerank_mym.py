# -*- coding: utf-8 -*-
import json

def Process(db, input):
    data = json.loads(input)
    max_iter = int(data.get("max_iter", 20))
    damping = float(data.get("damping", 0.85))
    top_k = int(data.get("top_k", 10))

    txn = db.CreateReadTxn()

    vids = []
    out_deg = {}
    it = txn.GetVertexIterator()
    while it.IsValid():
        vid = it.GetId()
        vids.append(vid)
        deg = 0
        v = txn.GetVertexIterator(vid)
        if v.IsValid():
            eit = v.GetOutEdgeIterator()
            while eit.IsValid():
                deg += 1
                eit.Next()
        out_deg[vid] = deg
        it.Next()

    N = len(vids)
    if N == 0:
        txn.Abort()
        return (True, "[]")

    pr = {vid: 1.0 / N for vid in vids}

    for _ in range(max_iter):
        new_pr = {vid: (1.0 - damping) / N for vid in vids}
        dangling_mass = sum(pr[vid] for vid in vids if out_deg[vid] == 0) * damping

        it = txn.GetVertexIterator()
        while it.IsValid():
            vid = it.GetId()
            if out_deg[vid] > 0:
                contrib = pr[vid] * damping / out_deg[vid]
                v = txn.GetVertexIterator(vid)
                if v.IsValid():
                    eit = v.GetOutEdgeIterator()
                    while eit.IsValid():
                        dst = eit.GetDst()
                        if dst in new_pr:
                            new_pr[dst] += contrib
                        eit.Next()
            it.Next()

        if dangling_mass > 0:
            equal_share = dangling_mass / N
            for vid in vids:
                new_pr[vid] += equal_share

        diff = sum(abs(new_pr[vid] - pr[vid]) for vid in vids)
        pr = new_pr
        if diff < 1e-6:
            break

    txn.Abort()

    sorted_pr = sorted(pr.items(), key=lambda x: x[1], reverse=True)
    top_result = sorted_pr[:top_k]
    result_list = [[vid, round(score, 6)] for vid, score in top_result]
    return (True, str(result_list))