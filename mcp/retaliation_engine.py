import asyncio
from datetime import datetime, timezone
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core.qvoid_core import EventBus

class RetaliationEngine:
    """
    Subscribes to THREAT_DETECTED and AUTONOMOUS_RESPONSE_INITIATED.
    Generates dynamic counter-exploits or deception payloads using the LLM.
    """
    def __init__(self, event_bus: EventBus, llm_adapter):
        self.bus = event_bus
        self.llm = llm_adapter
        self.bus.subscribe("AUTONOMOUS_RESPONSE_INITIATED", self._handle_response)

    async def _handle_response_async(self, event):
        data = event.get("data", {})
        await self.generate_and_deploy_payload(data)

    def _handle_response(self, event):
        """Handle threat response asynchronously."""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._handle_response_async(event))
        except RuntimeError:
            asyncio.run(self._handle_response_async(event))
            
    async def generate_and_deploy_payload(self, threat_data: dict):
        prompt = f"""
        Threat detected: {threat_data.get('threat_type', 'Unknown')}
        Confidence: {threat_data.get('confidence', 0)}
        Signal: {threat_data.get('signal', '')}

        Generate a Python script that deploys a deceptive honeypot environment tailored specifically to this threat. 
        Only return valid JSON with a 'payload_code' field.
        """
        
        try:
            response = await self.llm.generate_structured(prompt, system_prompt="You are a cyber warfare AI. Return valid JSON only with payload_code field.")
            payload_code = response.get("payload_code")
            
            if payload_code:
                self.bus.publish("RETALIATION_PAYLOAD_GENERATED", {
                    "threat": threat_data.get('threat_type'),
                    "payload_length": len(payload_code),
                    "code_preview": payload_code[:100]
                }, severity="CRITICAL")
                
                # Further execution can be handed off to Digital Forge
        except Exception as e:
            self.bus.publish("RETALIATION_FAILED", {"error": str(e)}, severity="ERROR")
