"""
LLM wrapper supporting multiple providers behind one interface.

Why this matters: the rest of the app calls `get_llm().generate(prompt)`
and never needs to know whether that's Groq, OpenAI, or Gemini under the
hood. Switching providers is a one-line .env change (LLM_PROVIDER=...).
"""

from abc import ABC, abstractmethod
from functools import lru_cache

from app.config import (
    LLM_PROVIDER,
    GROQ_API_KEY,
    GROQ_MODEL,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    GEMINI_API_KEY,
    GEMINI_MODEL,
)


class BaseLLM(ABC):
    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = "", max_tokens: int = 1024) -> str:
        ...


class GroqLLM(BaseLLM):
    def __init__(self):
        if not GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY is not set. Get a free key at "
                "https://console.groq.com/keys and add it to your .env file."
            )
        from groq import Groq
        self.client = Groq(api_key=GROQ_API_KEY)
        self.model = GROQ_MODEL

    def generate(self, prompt: str, system_prompt: str = "", max_tokens: int = 1024) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.2,
        )
        return response.choices[0].message.content


class OpenAILLM(BaseLLM):
    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set. Add it to your .env file.")
        from openai import OpenAI
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = OPENAI_MODEL

    def generate(self, prompt: str, system_prompt: str = "", max_tokens: int = 1024) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.2,
        )
        return response.choices[0].message.content


class GeminiLLM(BaseLLM):
    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set. Add it to your .env file.")
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(GEMINI_MODEL)

    def generate(self, prompt: str, system_prompt: str = "", max_tokens: int = 1024) -> str:
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        response = self.model.generate_content(
            full_prompt,
            generation_config={"max_output_tokens": max_tokens, "temperature": 0.2},
        )
        return response.text


_PROVIDER_MAP = {
    "groq": GroqLLM,
    "openai": OpenAILLM,
    "gemini": GeminiLLM,
}


@lru_cache(maxsize=1)
def get_llm(provider: str = None) -> BaseLLM:
    """Cached singleton LLM client based on LLM_PROVIDER in config/.env."""
    provider = (provider or LLM_PROVIDER).lower()
    if provider not in _PROVIDER_MAP:
        raise ValueError(
            f"Unknown LLM_PROVIDER '{provider}'. Choose from: {list(_PROVIDER_MAP.keys())}"
        )
    return _PROVIDER_MAP[provider]()
