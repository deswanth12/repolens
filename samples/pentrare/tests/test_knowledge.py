from app.knowledge.retriever import KnowledgeRetriever

def test_query():
    r = KnowledgeRetriever()
    res = r.query("test")
    assert len(res) == 1
