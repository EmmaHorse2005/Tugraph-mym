# coding=gbk
from neo4j import GraphDatabase

# TuGraph 配置
URI = "bolt://127.0.0.1:7687"
AUTH = ("admin", "000")
client = GraphDatabase.driver(URI, auth=AUTH)
session = client.session(database="mym")


# 1. 删除库
session.run("CALL db.dropDB()")

# 2. 创建点标签
session.run("CALL db.createVertexLabel('person', 'id', 'id', INT32, false, 'name', STRING, false)")

# 3. 创建边标签
session.run("CALL db.createEdgeLabel('is_friend','[[\"person\",\"person\"]]')")

# 4. 创建索引
session.run("CALL db.addIndex(\"person\", \"name\", false)")

# 5. 创建节点
session.run("create (n1:person {name:'jack',id:1}), (n2:person {name:'lucy',id:2})")

# 6. 创建关系
session.run("match (n1:person {id:1}), (n2:person {id:2}) create (n1)-[r:is_friend]->(n2)")

# 7. 查询数据
res = session.run("match (n)-[r]->(m) return n,r,m")
print("=== 全量查询结果 ===")
for item in res.data():
    print(item)

# 8. 参数化查询
cypherQuery = "MATCH (n1:person {id:$id})-[r]-(n2:person {name:$name}) RETURN n1, r, n2"
result1 = session.run(cypherQuery, id=1, name="lucy")
print("\n=== 参数化查询结果 ===")
for item in result1.data():
    print(item)

# 9. 删除数据
session.run("match (n1:person {id:1}) delete n1")
session.run("match (n1:person {id:1})-[r]-(n2:person{id:2}) delete r")

# 10. 删除标签
session.run("CALL db.deleteLabel('edge', 'is_friend')")
session.run("CALL db.deleteLabel('vertex', 'person')")

# 关闭
session.close()
client.close()
print("\n执行成功！")