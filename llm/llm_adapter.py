import os
from dotenv import load_dotenv
load_dotenv()
import json
import httpx
import asyncio
from typing import Optional, Dict, Any, Callable

class LLMResponse:
    def __init__(self, content: str, raw_response: Dict[str, Any] = None):
        self.content = content
        self.raw_response = raw_response or {}
        
    def to_dict(self):
        try:
            # Try to parse the content directly
            return json.loads(self.content)
        except json.JSONDecodeError:
            # Sometimes models wrap json in markdown block
            content = self.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            try:
                return json.loads(content.strip())
            except json.JSONDecodeError:
                return {"error": "Invalid JSON response", "raw": self.content}

class LLMAdapter:
    """Unified interface for LLM providers."""
    
    def __init__(self, provider: str = "openrouter", model: str = "anthropic/claude-3-opus", api_key: str = None):
        self.provider = provider.lower()
        self.model = model
        
        if self.provider == "openrouter":
            self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
            self.base_url = "https://openrouter.ai/api/v1"
        elif self.provider == "ollama":
            self.base_url = "http://localhost:11434/api"
            self.api_key = None
        elif self.provider == "openai":
            self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
            self.base_url = "https://api.openai.com/v1"
        else:
            raise ValueError(f"Unsupported provider: {provider}")
            
        self.client = httpx.AsyncClient(timeout=60.0)

    async def _generate_openrouter_like(self, messages: list, temperature: float, max_tokens: int, response_format: dict = None) -> LLMResponse:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/qvoid-os",
            "X-Title": "Q-VOID OS"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if response_format:
            payload["response_format"] = response_format
            
        response = await self.client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        content = data['choices'][0]['message']['content']
        return LLMResponse(content, raw_response=data)

    async def _generate_ollama(self, messages: list, temperature: float, max_tokens: int, response_format: dict = None) -> LLMResponse:
        system_prompt = next((m['content'] for m in messages if m['role'] == 'system'), "")
        user_prompt = "\n".join([m['content'] for m in messages if m['role'] != 'system'])
        
        payload = {
            "model": self.model,
            "prompt": f"{system_prompt}\n\n{user_prompt}" if system_prompt else user_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        if response_format and response_format.get("type") == "json_object":
            payload["format"] = "json"
            
        response = await self.client.post(f"{self.base_url}/generate", json=payload)
        response.raise_for_status()
        data = response.json()
        content = data['response']
        return LLMResponse(content, raw_response=data)

    async def generate(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.7, max_tokens: int = 2048) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            if self.provider in ["openrouter", "openai"]:
                res = await self._generate_openrouter_like(messages, temperature, max_tokens)
                return res.content
            elif self.provider == "ollama":
                res = await self._generate_ollama(messages, temperature, max_tokens)
                return res.content
        except Exception as e:
            return f"Error: {str(e)}"

    async def generate_structured(self, prompt: str, schema: dict = None, system_prompt: Optional[str] = None) -> dict:
        """Force JSON output mode if supported, and parse the response."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        else:
            messages.append({"role": "system", "content": "You must output valid JSON only."})
            
        messages.append({"role": "user", "content": prompt})
        
        response_format = {"type": "json_object"}
        
        try:
            if self.provider in ["openrouter", "openai"]:
                res = await self._generate_openrouter_like(messages, temperature=0.1, max_tokens=2048, response_format=response_format)
            elif self.provider == "ollama":
                res = await self._generate_ollama(messages, temperature=0.1, max_tokens=2048, response_format=response_format)
            else:
                return {"error": "Unsupported provider"}
                
            return res.to_dict()
        except Exception as e:
            return {"error": str(e)}

    async def stream(self, prompt: str, callback: Callable[[str], None], system_prompt: Optional[str] = None):
        """Streaming response implementation. Fallback to full generation."""
        res = await self.generate(prompt, system_prompt=system_prompt)
        callback(res)
        return res
        
    def get_status(self) -> dict:
        return {
            "provider": self.provider,
            "model": self.model,
            "has_api_key": bool(self.api_key) if self.provider != "ollama" else True,
            "base_url": self.base_url
        }
