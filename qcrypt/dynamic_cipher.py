import asyncio
from typing import Dict, Any

class LLMDynamicCipher:
    """
    Uses an LLM to invent and apply a novel encryption schema on the fly.
    This creates an 'insane' level of polymorphic encryption where the algorithm
    itself is generated at runtime and unique to every payload.
    """
    def __init__(self, llm_adapter):
        self.llm = llm_adapter

    async def encrypt(self, plaintext: str) -> Dict[str, Any]:
        """Asks the LLM to invent a new cipher, apply it, and return the ciphertext and decryption routine."""
        prompt = f"""
        Invent a brand new, highly complex symmetric encryption algorithm (e.g., bitwise shifts, substitutions, prime-modulus math).
        Do NOT use standard algorithms like AES or Base64.
        
        Encrypt the following plaintext using your new algorithm:
        '{plaintext}'
        
        Return a JSON response with:
        - "ciphertext": The encrypted data (string)
        - "key": The generated key used (string)
        - "decryption_python_code": A valid Python function named `decrypt(ciphertext: str, key: str) -> str` that implements the reverse of your algorithm.
        """
        
        try:
            response = await self.llm.generate_structured(prompt, system_prompt="You are a brilliant cryptographer. Output only valid JSON.")
            return {
                "ciphertext": response.get("ciphertext", ""),
                "key": response.get("key", ""),
                "decryption_routine": response.get("decryption_python_code", "")
            }
        except Exception as e:
            return {"error": str(e)}

    def decrypt(self, envelope: Dict[str, Any]) -> str:
        """Executes the dynamically generated LLM decryption routine to recover the plaintext."""
        code = envelope.get("decryption_routine", "")
        if not code:
            return ""
            
        local_scope = {}
        try:
            # DANGEROUS: Executing LLM-generated code. This fits the "insane" moving-target defense paradigm.
            exec(code, {}, local_scope)
            decrypt_fn = local_scope.get("decrypt")
            if decrypt_fn:
                return decrypt_fn(envelope.get("ciphertext", ""), envelope.get("key", ""))
        except Exception as e:
            print(f"[DynamicCipher] Decryption execution failed: {e}")
        return ""
