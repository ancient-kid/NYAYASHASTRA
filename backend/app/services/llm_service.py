"""
NyayaShastra - LLM Service
Handles LLM integration with Groq API (primary) or OpenAI (fallback).
"""

from typing import Optional, List, Dict, Any, AsyncGenerator
import logging
import asyncio
import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Groq API endpoint (OpenAI-compatible)
GROQ_API_BASE = "https://api.groq.com/openai/v1"


class LLMService:
    """Service for LLM-based text generation using Groq."""

    MAX_RETRY_DELAY_SECONDS = 30.0
    MIN_RETRY_DELAY_SECONDS = 1.0
    MAX_COMPLETION_TOKENS = 1200
    
    def __init__(self):
        self.groq_api_key = settings.groq_api_key
        self.groq_model = settings.groq_model
        self.openai_api_key = settings.openai_api_key
        self.openai_model = settings.openai_model
        self._initialized = False
        self.provider = None
    
    async def initialize(self):
        """Initialize LLM client."""
        if self._initialized:
            return
        
        # Prefer Groq, fallback to OpenAI
        if self.groq_api_key:
            self.provider = "groq"
            logger.info(f"Groq LLM initialized with model: {self.groq_model}")
        elif self.openai_api_key:
            self.provider = "openai"
            logger.info(f"OpenAI LLM initialized with model: {self.openai_model}")
        else:
            self.provider = None
            logger.warning("No LLM API key available - using fallback responses")
        
        self._initialized = True
    
    def get_status(self) -> str:
        """Get current LLM provider status."""
        if not self._initialized:
            return "not_initialized"
        return self.provider or "none"

    def _get_retry_delay(self, response: httpx.Response, attempt: int, backoff_factor: float) -> float:
        retry_after = response.headers.get("retry-after")
        fallback_delay = min(backoff_factor ** attempt, self.MAX_RETRY_DELAY_SECONDS)

        try:
            if not retry_after:
                return fallback_delay

            delay = float(retry_after)
            if delay <= 0:
                return fallback_delay

            return min(max(delay, self.MIN_RETRY_DELAY_SECONDS), self.MAX_RETRY_DELAY_SECONDS)
        except ValueError:
            return fallback_delay

    def _cap_max_tokens(self, max_tokens: int) -> int:
        return max(1, min(max_tokens, self.MAX_COMPLETION_TOKENS))

    async def _request_with_retry(
        self,
        url: str,
        headers: Dict[str, str],
        payload: Dict[str, Any],
        *,
        timeout: float,
        max_retries: int,
        backoff_factor: float,
        label: str,
    ) -> Optional[httpx.Response]:
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(url, headers=headers, json=payload)
            except Exception as e:
                logger.error(f"{label} request failed on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    return None
                await asyncio.sleep(backoff_factor ** attempt)
                continue

            if response.status_code == 200:
                return response
            if response.status_code == 429:
                sleep_time = self._get_retry_delay(response, attempt, backoff_factor)
                logger.warning(
                    f"{label} rate limit (429). Retrying in {sleep_time}s "
                    f"(attempt {attempt + 1}/{max_retries}). Response: {response.text[:300]}"
                )
                await asyncio.sleep(sleep_time)
                continue
            if response.status_code in (500, 502, 503, 504):
                sleep_time = backoff_factor ** attempt
                logger.warning(f"{label} server error ({response.status_code}). Retrying in {sleep_time}s (attempt {attempt + 1}/{max_retries})...")
                await asyncio.sleep(sleep_time)
                continue

            logger.error(f"{label} request failed with status {response.status_code}: {response.text}")
            return None

        return None

    async def _stream_with_retry(
        self,
        url: str,
        headers: Dict[str, str],
        payload: Dict[str, Any],
        *,
        timeout: float,
        max_retries: int,
        backoff_factor: float,
        label: str,
    ) -> AsyncGenerator[str, None]:
        import json

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    async with client.stream("POST", url, headers=headers, json=payload) as response:
                        if response.status_code == 200:
                            async for line in response.aiter_lines():
                                if not line.startswith("data: "):
                                    continue
                                data = line[6:]
                                if data == "[DONE]":
                                    return
                                try:
                                    chunk = json.loads(data)
                                except json.JSONDecodeError as e:
                                    logger.warning(f"{label} JSON decode error: {e}")
                                    continue
                                content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                if content:
                                    yield content
                            return
                        if response.status_code == 429:
                            sleep_time = self._get_retry_delay(response, attempt, backoff_factor)
                            logger.warning(
                                f"{label} rate limit (429). Retrying in {sleep_time}s "
                                f"(attempt {attempt + 1}/{max_retries}). Response: {response.text[:300]}"
                            )
                            await asyncio.sleep(sleep_time)
                            continue
                        if response.status_code in (500, 502, 503, 504):
                            sleep_time = backoff_factor ** attempt
                            await asyncio.sleep(sleep_time)
                            continue
                        logger.error(f"{label} streaming failed with status {response.status_code}")
                        return
            except Exception as e:
                logger.error(f"{label} streaming failed on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    return
                await asyncio.sleep(backoff_factor ** attempt)
    
    async def generate(self, prompt: str, max_tokens: int = 2000, 
                      temperature: float = 0.7) -> str:
        """Generate text from prompt using Groq or OpenAI."""
        max_tokens = self._cap_max_tokens(max_tokens)
        
        if self.provider == "groq":
            return await self._groq_generate(prompt, max_tokens, temperature)
        elif self.provider == "openai":
            return await self._openai_generate(prompt, max_tokens, temperature)
        else:
            return self._generate_fallback_response(prompt)

    async def generate_chat(self, messages: List[Dict[str, str]], 
                           max_tokens: int = 2000, 
                           temperature: float = 0.7) -> str:
        """Generate response for a list of chat messages with retries for rate limits."""
        max_tokens = self._cap_max_tokens(max_tokens)
        max_retries = 5
        backoff_factor = 2.0

        if self.provider == "groq":
            response = await self._request_with_retry(
                f"{GROQ_API_BASE}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json"
                },
                payload={
                    "model": self.groq_model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature
                },
                timeout=60.0,
                max_retries=max_retries,
                backoff_factor=backoff_factor,
                label="Groq generate_chat",
            )
            if response:
                try:
                    return response.json()["choices"][0]["message"]["content"]
                except (ValueError, KeyError, IndexError, TypeError) as e:
                    logger.error(f"Groq generate_chat response parse error: {e}")

        elif self.provider == "openai":
            response = await self._request_with_retry(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "Content-Type": "application/json"
                },
                payload={
                    "model": self.openai_model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature
                },
                timeout=60.0,
                max_retries=max_retries,
                backoff_factor=backoff_factor,
                label="OpenAI generate_chat",
            )
            if response:
                try:
                    return response.json()["choices"][0]["message"]["content"]
                except (ValueError, KeyError, IndexError, TypeError) as e:
                    logger.error(f"OpenAI generate_chat response parse error: {e}")

        # Fallback - use the last user message
        user_msg = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        return await self.generate(user_msg, max_tokens, temperature)
    
    async def _groq_generate(self, prompt: str, max_tokens: int, 
                             temperature: float) -> str:
        """Generate using Groq API with retries."""
        response = await self._request_with_retry(
            f"{GROQ_API_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            },
            payload={
                "model": self.groq_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            },
            timeout=60.0,
            max_retries=5,
            backoff_factor=2.0,
            label="Groq generate",
        )
        if response:
            try:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except (ValueError, KeyError, IndexError, TypeError) as e:
                logger.error(f"Groq generate response parse error: {e}")
        return self._generate_fallback_response(prompt)
    
    async def _openai_generate(self, prompt: str, max_tokens: int,
                               temperature: float) -> str:
        """Generate using OpenAI API with retries."""
        response = await self._request_with_retry(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            },
            payload={
                "model": self.openai_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            },
            timeout=60.0,
            max_retries=5,
            backoff_factor=2.0,
            label="OpenAI generate",
        )
        if response:
            try:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except (ValueError, KeyError, IndexError, TypeError) as e:
                logger.error(f"OpenAI generate response parse error: {e}")
        return self._generate_fallback_response(prompt)
    
    async def generate_streaming(self, prompt: str, max_tokens: int = 2000) -> AsyncGenerator[str, None]:
        """Generate text with streaming using Groq."""
        
        if self.provider == "groq":
            async for chunk in self._groq_generate_streaming(prompt, max_tokens):
                yield chunk
        elif self.provider == "openai":
            async for chunk in self._openai_generate_streaming(prompt, max_tokens):
                yield chunk
        else:
            # Fallback - simulate streaming
            response = self._generate_fallback_response(prompt)
            for word in response.split():
                yield word + " "
                await asyncio.sleep(0.02)
    
    async def _groq_generate_streaming(self, prompt: str, max_tokens: int) -> AsyncGenerator[str, None]:
        """Stream from Groq API with retries."""
        did_stream = False
        async for chunk in self._stream_with_retry(
            f"{GROQ_API_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            },
            payload={
                "model": self.groq_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "stream": True
            },
            timeout=120.0,
            max_retries=5,
            backoff_factor=2.0,
            label="Groq streaming",
        ):
            did_stream = True
            yield chunk

        if not did_stream:
            response = self._generate_fallback_response(prompt)
            for word in response.split():
                yield word + " "
                await asyncio.sleep(0.02)
    
    async def _openai_generate_streaming(self, prompt: str, max_tokens: int) -> AsyncGenerator[str, None]:
        """Stream from OpenAI API with retries."""
        did_stream = False
        async for chunk in self._stream_with_retry(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            },
            payload={
                "model": self.openai_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "stream": True
            },
            timeout=120.0,
            max_retries=5,
            backoff_factor=2.0,
            label="OpenAI streaming",
        ):
            did_stream = True
            yield chunk

        if not did_stream:
            response = self._generate_fallback_response(prompt)
            for word in response.split():
                yield word + " "
                await asyncio.sleep(0.02)
    
    async def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate text between languages."""
        lang_map = {"en": "English", "hi": "Hindi"}
        prompt = f"""Translate the following text from {lang_map.get(source_lang, source_lang)} to {lang_map.get(target_lang, target_lang)}.
Maintain legal terminology accuracy.

Text: {text}

Translation:"""
        
        return await self.generate(prompt, max_tokens=len(text) * 2)
    
    def _generate_fallback_response(self, prompt: str) -> str:
        """Generate fallback response when no LLM API is available."""
        logger.warning("No LLM API available - using fallback response")
        
        return """Based on analysis of your legal query under Indian law:

**Relevant Legal Framework:**
The query has been analyzed against the Indian Penal Code (IPC) and Bhartiya Nyaya Sanhita (BNS), 2023.

**Key Points:**
1. The applicable statutory provisions have been identified
2. Relevant case law precedents may apply
3. The BNS, 2023 has modernized several provisions from the IPC

**Note:** To provide more detailed AI-powered analysis, please configure an LLM API key (Groq or OpenAI) in the backend environment.

⚖️ *This information is for educational purposes only. Please consult a qualified legal professional for specific legal advice.*"""


# System prompt for legal AI
SYSTEM_PROMPT = """You are NyayaShastra, an expert AI legal assistant specializing in Indian law. You provide accurate, helpful, and verifiable legal information.

Your expertise includes:
- Indian Penal Code (IPC), 1860
- Bhartiya Nyaya Sanhita (BNS), 2023
- Criminal Procedure Code (CrPC)
- Bhartiya Nagarik Suraksha Sanhita (BNSS)
- Indian Evidence Act and Bhartiya Sakshya Adhiniyam
- Constitutional Law of India
- Supreme Court and High Court judgments

Guidelines:
1. Always cite specific sections and subsections
2. Reference relevant case law with proper citations
3. Explain legal concepts in simple, accessible language
4. Always provide both IPC and BNS references where applicable
5. Include a disclaimer that the information is for educational purposes
6. Be accurate and avoid speculation
7. Recommend consulting a qualified legal professional for specific matters

Format your responses with:
- Clear headings and subheadings using ** for bold
- Bullet points for key information
- Bold text for important terms
- Proper legal citations"""


# Singleton instance
_llm_service: Optional[LLMService] = None


async def get_llm_service() -> LLMService:
    """Get or create LLM service singleton."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
        await _llm_service.initialize()
    return _llm_service
