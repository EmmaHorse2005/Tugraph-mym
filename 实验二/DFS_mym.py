# coding=gbk
import json

def Process(db, input):
    raw_data = input
    parsed_data = json.loads(raw_data)
    if "times" in parsed_data:
        start_vid = int(str(parsed_data["times"]))
    txn = db.CreateReadTxn()
    
    visited = {start_vid}
    stack = [start_vid]
    dfs_order = []
    
    while stack:
        current_vid = stack.pop()
        dfs_order.append(current_vid)
        vertex = txn.GetVertexIterator(current_vid)
        if not vertex.IsValid():
            continue
        
        out_edge_it = vertex.GetOutEdgeIterator()
        while out_edge_it.IsValid():
            dst_vid = out_edge_it.GetDst()
            if dst_vid not in visited:
                visited.add(dst_vid)
                stack.append(dst_vid)
            out_edge_it.Next()
        
        in_edge_it = vertex.GetInEdgeIterator()
        while in_edge_it.IsValid():
            src_vid = in_edge_it.GetSrc()
            if src_vid not in visited:
                visited.add(src_vid)
                stack.append(src_vid)
            in_edge_it.Next()
            
    txn.Abort()
    return (True, str(dfs_order))
