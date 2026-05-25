import os
import sys
import asyncio

class CodeMutator:
    """
    Uses LLM and AST strategies to dynamically rewrite Python code and hot-reload it.
    """
    def __init__(self, llm_adapter):
        self.llm = llm_adapter

    async def heal_codebase(self, target_file: str, vulnerability_report: str) -> bool:
        """Uses LLM to rewrite and patch a vulnerable source file."""
        if not os.path.exists(target_file):
            return False
            
        try:
            with open(target_file, "r", encoding="utf-8") as f:
                original_code = f.read()

            prompt = f"""
            The following Python code has a reported vulnerability or issue.
            Vulnerability Report: {vulnerability_report}
            
            Code:
            {original_code}
            
            Rewrite the code to fix the vulnerability. Ensure the code remains valid Python and retains its original purpose.
            Return ONLY valid JSON with a 'patched_code' field containing the fixed source code.
            """
            
            response = await self.llm.generate_structured(prompt, system_prompt="You are an expert Python developer and security auditor. Return only JSON.")
            patched_code = response.get("patched_code")
            
            if patched_code:
                # Compile to verify syntax before saving
                compile(patched_code, target_file, 'exec')
                with open(target_file, "w", encoding="utf-8") as f:
                    f.write(patched_code)
                return True
            return False
        except Exception as e:
            return False
