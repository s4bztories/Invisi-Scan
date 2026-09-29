import pytest
from backend.core.rag_engine import RAGEngine
from backend.core.ai_chatbot import AIChatbot
from backend.core.ml_risk_scorer import MLRiskScorer
from backend.mcp_server import InvisiScanMCPServer


def test_rag_engine_search():
    rag = RAGEngine()
    rag.add_document("test_doc", "EternalBlue SMB Patch", "Port 445 SMB vulnerability requires patch KB4012598.")
    results = rag.search("EternalBlue SMB", top_k=2)
    assert len(results) > 0
    assert "EternalBlue" in results[0]["title"] or "SMB" in results[0]["title"]


def test_ai_chatbot_response():
    rag = RAGEngine()
    chatbot = AIChatbot(rag_engine=rag)
    res = chatbot.chat("Suggest Metasploit commands for port 445")
    assert "answer" in res
    assert "Metasploit" in res["answer"] or "msfconsole" in res["answer"]
    assert "rag_sources font" not in res  # Check structure


def test_ml_risk_scorer():
    scorer = MLRiskScorer()
    res = scorer.evaluate([445, 3389], {445: [{"id": "CVE-2017-0144", "summary": "EternalBlue Remote Code Execution"}]})
    assert res["risk_score"] > 70.0
    assert res["threat_level"] == "CRITICAL"
    assert res["total_open_ports"] == 2


@pytest.mark.asyncio
async def test_mcp_server():
    server = InvisiScanMCPServer()
    manifest = server.get_manifest()
    assert len(manifest["tools"]) == 4

    result = await server.execute_tool("invisi_ml_risk_analysis", {"open_ports": [80, 443], "cves": {}})
    assert "risk_score" in result
