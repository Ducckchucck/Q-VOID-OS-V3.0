import asyncio
from datetime import datetime, timezone
from typing import Optional

class ThreatAssessment:
    def __init__(self, signal: str, threat_type: str, confidence: float,
                 recommended_actions: list, counter_exploit_code: str = None,
                 raw_mcp_output: dict = None, raw_rag_output: dict = None):
        self.signal = signal
        self.threat_type = threat_type
        self.confidence = confidence
        self.recommended_actions = recommended_actions
        self.counter_exploit_code = counter_exploit_code
        self.raw_mcp_output = raw_mcp_output
        self.raw_rag_output = raw_rag_output
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self):
        return {
            "signal": self.signal,
            "threat_type": self.threat_type,
            "confidence": self.confidence,
            "recommended_actions": self.recommended_actions,
            "counter_exploit_code": self.counter_exploit_code,
            "timestamp": self.timestamp
        }

class ThreatPipeline:
    """Unified Precog → MCP → RAG intelligence pipeline."""
    
    def __init__(self, precog, mcp, rag, llm_adapter, event_bus):
        self.precog = precog
        self.mcp = mcp
        self.rag = rag
        self.llm = llm_adapter
        self.bus = event_bus
    
    async def analyze_threat(self, signal: str) -> ThreatAssessment:
        """
        Full pipeline:
        1. Precog predicts attack vector + confidence
        2. MCP classifies and routes through detection models
        3. RAG retrieves similar past incidents
        4. LLM synthesizes all three into a coherent threat assessment
           with recommended countermeasures
        """
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from llm.prompts import THREAT_ANALYSIS_PROMPT
        
        # 1. Precog
        prediction = self.precog.predict_vector(signal, top_n=1)
        precog_threat = prediction[0][0] if prediction else "Unknown"
        precog_conf = prediction[0][1] if prediction else 0.0

        # 2. MCP
        mcp_results = self.mcp.route_all(signal)

        # 3. RAG
        rag_results = self.rag.query(signal, top_k=2)

        # 4. LLM Synthesis
        prompt = f"""
        Signal: {signal}
        Precog Prediction: {precog_threat} ({precog_conf}%)
        MCP Results: {mcp_results}
        RAG History: {rag_results}
        """

        # Generate structured response
        response = await self.llm.generate_structured(prompt, system_prompt=THREAT_ANALYSIS_PROMPT)
        
        assessment = ThreatAssessment(
            signal=signal,
            threat_type=response.get("threat_type", precog_threat),
            confidence=response.get("confidence", precog_conf),
            recommended_actions=response.get("recommended_actions", []),
            counter_exploit_code=response.get("counter_exploit_code", None),
            raw_mcp_output=mcp_results,
            raw_rag_output=rag_results
        )
        
        # Call publish_async if available, otherwise fallback to publish
        if hasattr(self.bus, "publish_async"):
            await self.bus.publish_async("THREAT_ASSESSMENT_COMPLETE", assessment.to_dict(), severity="HIGH")
        else:
            self.bus.publish("THREAT_ASSESSMENT_COMPLETE", assessment.to_dict(), severity="HIGH")
        return assessment
    
    async def autonomous_respond(self, assessment: ThreatAssessment, forge=None):
        """
        Based on assessment severity, autonomously:
        - Deploy honeypot (via Forge)
        - Trigger polymorphic mutation
        - Broadcast to hive mind
        """
        self.bus.publish("AUTONOMOUS_RESPONSE_INITIATED", assessment.to_dict(), severity="CRITICAL")
        
        # Trigger polymorphic and hive mind via standard event
        self.bus.publish("THREAT_DETECTED", {"threat_type": assessment.threat_type}, severity="CRITICAL")
        
        # Deploy honeypot if forge provided
        if forge and hasattr(forge, "auto_deploy_honeypot"):
            forge.auto_deploy_honeypot(assessment)
