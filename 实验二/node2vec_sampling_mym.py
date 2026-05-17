# coding=gbk
import json
import random

# Params: start_vid=100, walk_len=10, num_walks=5, p=1.0, q=1.0
#{"start_vid": 100, "walk_len": 10, "num_walks": 5, "p": 1.0, "q": 1.0}

def Process(db, input):
    # Parse JSON input parameters
    data = json.loads(input)
    start_vid = int(data["start_vid"])
    walk_len = int(data["walk_len"])
    num_walks = int(data["num_walks"])
    p = float(data["p"])
    q = float(data["q"])

    # Create read-only transaction
    txn = db.CreateReadTxn()

    # Cache neighbors to avoid repeated DB queries
    neighbor_cache = {}

    def get_neighbors(vid):
        if vid not in neighbor_cache:
            v = txn.GetVertexIterator(vid)
            nbrs = []
            if v.IsValid():
                edge_it = v.GetOutEdgeIterator()
                while edge_it.IsValid():
                    # Get destination vertex ID (TuGraph 4.x standard API)
                    nbrs.append(edge_it.GetDst())
                    edge_it.Next()
            neighbor_cache[vid] = nbrs
        return neighbor_cache[vid]

    # Node2Vec biased random walk implementation
    def biased_walk(start_node, length):
        walk = [start_node]
        curr = start_node
        prev = start_node  # Initialize prev = curr at start

        for _ in range(length - 1):
            nbrs = get_neighbors(curr)
            if not nbrs:
                break

            # Get neighbors of previous node for fast lookup
            prev_nbrs_set = set(get_neighbors(prev))

            # Calculate transition weights following Node2Vec rules
            weights = []
            for n in nbrs:
                if n == prev:
                    weights.append(1.0 / p)      # Return to previous node
                elif n in prev_nbrs_set:
                    weights.append(1.0)          # Local BFS behavior
                else:
                    weights.append(1.0 / q)      # Outward DFS behavior

            # Normalize weights to probabilities
            total_w = sum(weights)
            norm_weights = [w / total_w for w in weights]

            # Weighted random selection for next node
            next_node = random.choices(nbrs, weights=norm_weights, k=1)[0]

            walk.append(next_node)
            prev = curr
            curr = next_node
        return walk

    # Generate multiple random walks
    all_walks = []
    for _ in range(num_walks):
        all_walks.append(biased_walk(start_vid, walk_len))

    # Release read-only transaction
    txn.Abort()

    # Return result in TuGraph standard format: (success, result string)
    return (True, str(all_walks))
