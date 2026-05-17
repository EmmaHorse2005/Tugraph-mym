# -*- coding: utf-8 -*-
import json
import random

def Process(db, input):
    # Parse input JSON to get max iteration number
    parsed_data = json.loads(input)
    max_iter = int(parsed_data.get("max_iter", 20))
    
    # Fix random seed to ensure reproducible results
    random.seed(42)

    # Create read-only transaction for graph traversal
    txn = db.CreateReadTxn()
    
    # Collect all vertex IDs from the graph
    vids = []
    it = txn.GetVertexIterator()
    while it.IsValid():
        vids.append(it.GetId())
        it.Next()

    # Initialize label: each vertex forms its own community at first
    labels = {vid: vid for vid in vids}

    # Core LPA iteration loop
    for _ in range(max_iter):
        changed = False
        # Use synchronous update: compute new labels based on old labels
        new_labels = labels.copy()
        
        for vid in vids:
            vertex = txn.GetVertexIterator(vid)
            if not vertex.IsValid():
                continue
            
            # Count label frequency of all outgoing neighbors
            label_freq = {}
            edge_it = vertex.GetOutEdgeIterator()
            while edge_it.IsValid():
                dst_vid = edge_it.GetDst()
                if dst_vid in labels:
                    lbl = labels[dst_vid]
                    label_freq[lbl] = label_freq.get(lbl, 0) + 1
                edge_it.Next()

            # Update label if neighbors exist
            if label_freq:
                max_count = max(label_freq.values())
                # Get all candidate labels with maximum frequency
                candidates = [lbl for lbl, cnt in label_freq.items() if cnt == max_count]
                new_label = random.choice(candidates)

                if new_label != labels[vid]:
                    new_labels[vid] = new_label
                    changed = True

        # Update labels for next iteration
        labels = new_labels
        # Early stop if no label changes (converged)
        if not changed:
            break

    # Format result: [vertex name, community id]
    result = []
    for vid, cid in labels.items():
        vtx = txn.GetVertexIterator(vid)
        name = vtx.GetField("name") if vtx.IsValid() else str(vid)
        result.append([name, cid])
    
    # Release transaction resource
    txn.Abort()
    
    return (True, str(result))