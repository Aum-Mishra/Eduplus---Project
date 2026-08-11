"""
Local Mistral-based generation service for EduNavigator.
Uses Ollama for local LLM inference - no API keys needed.
"""

import os
import json
import re
from typing import Any, Dict
import requests
from langchain_core.documents import Document


SYSTEM_PROMPT = (
    "You are EduNavigator, an expert career guide. Given a student profile and retrieved context, "
    "produce a concise, step-by-step learning roadmap tailored to the profile. "
    "Return ONLY valid JSON with keys: careerPath, roadmap, resources, projects. "
    "- careerPath: string\n"
    "- roadmap: array of phases, each with title and steps[]\n"
    "- resources: array of {title, type, url?}\n"
    "- projects: array of short project ideas\n"
    "Be practical, prioritize fundamentals, and align with the student's interests and skills."
)


def _format_context(profile: Dict[str, Any], docs: list[Document]) -> str:
    """Format profile and documents for context."""
    blocks = [
        "STUDENT PROFILE:",
        f"Branch: {profile.get('branch', '')}",
        f"Interests: {', '.join(profile.get('interests') or [])}",
        f"Skills: {', '.join(profile.get('skills') or [])}",
        f"Career Goal: {profile.get('goal', '')}",
        "\nLEARNING RESOURCES & CONTEXT:"
    ]
    for i, d in enumerate(docs[:8]):
        blocks.append(
            f"[Source {i+1}] {d.metadata.get('source')} | {d.metadata.get('section')}\n{d.page_content[:300]}..."
        )
    return "\n\n".join(blocks)


class LocalGenerationService:
    """Uses Ollama Mistral for local LLM generation."""
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url.rstrip("/")
        self.model = "mistral"
        self._verify_ollama()
    
    def _verify_ollama(self) -> None:
        """Check if Ollama is running and Mistral is available."""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=2)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                if not any("mistral" in name for name in model_names):
                    print(f"⚠️  Warning: Mistral not found in Ollama. Available: {model_names}")
                    print(f"Pull Mistral with: ollama pull mistral")
                else:
                    print("✅ Ollama and Mistral verified")
            else:
                raise RuntimeError(f"Ollama returned status {response.status_code}")
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                f"Cannot connect to Ollama at {self.ollama_url}. "
                "Ensure Ollama is running with: ollama serve"
            )
        except Exception as e:
            raise RuntimeError(f"Ollama verification failed: {e}")
    
    def _call_mistral(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """Call Mistral via Ollama API."""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
                timeout=60
            )
            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                raise RuntimeError(f"Ollama error: {response.status_code} - {response.text}")
        except requests.exceptions.Timeout:
            raise RuntimeError("Ollama request timed out. Response generation took too long.")
        except requests.exceptions.ConnectionError:
            raise RuntimeError("Cannot reach Ollama. Make sure it's running with: ollama serve")
        except Exception as e:
            raise RuntimeError(f"Mistral generation failed: {e}")
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract and parse JSON from response."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON block in response
            m = re.search(r"\{[\s\S]*\}", text)
            if m:
                try:
                    return json.loads(m.group(0))
                except json.JSONDecodeError:
                    pass
        
        # Fallback: return minimal structure
        return {
            "careerPath": "Career path generation failed - try rephrasing your goal",
            "roadmap": [],
            "resources": [],
            "projects": []
        }
    
    def generate_plan(self, profile: Dict[str, Any], retrieved: Dict[str, Any]) -> Dict[str, Any]:
        """Generate personalized learning roadmap."""
        context = _format_context(profile, retrieved["documents"])
        prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"{context}\n\n"
            "Respond ONLY with valid JSON as specified above."
        )
        
        response = self._call_mistral(prompt, temperature=0.6, max_tokens=1500)
        return self._extract_json(response)
    
    def answer_question(self, question: str, profile: Dict[str, Any], retrieved: Dict[str, Any]) -> str:
        """Answer a career guidance question grounded in context."""
        context = _format_context(profile, retrieved["documents"])
        prompt = (
            "You are a career advisor. Answer the following question based STRICTLY on the provided context.\n"
            "If the answer is not in the context, say you don't have enough information.\n\n"
            f"STUDENT PROFILE: {profile.get('branch', 'N/A')} | Goals: {profile.get('goal', 'N/A')}\n\n"
            f"CONTEXT:\n{context}\n\n"
            f"QUESTION: {question}\n\n"
            "ANSWER:"
        )
        
        response = self._call_mistral(prompt, temperature=0.5, max_tokens=1000)
        return response.strip()
