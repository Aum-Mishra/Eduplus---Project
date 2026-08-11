import os
from typing import Any, Dict

import google.generativeai as genai
from langchain_core.documents import Document


SYSTEM_PROMPT = (
    "You are EduNavigator, an expert career guide. Given a student profile and retrieved context, "
    "produce a concise, step-by-step learning roadmap tailored to the profile. "
    "Return JSON with keys: careerPath, roadmap, resources, projects. "
    "- careerPath: string\n"
    "- roadmap: array of phases, each with title and steps[]\n"
    "- resources: array of {title, type, url?}\n"
    "- projects: array of short project ideas\n"
    "Be practical, prioritize fundamentals, and align with the student's interests and skills."
)


def _format_context(profile: Dict[str, Any], docs: list[Document]) -> str:
    blocks = [
        "PROFILE:",
        f"Branch: {profile.get('branch','')}",
        f"Interests: {', '.join(profile.get('interests') or [])}",
        f"Skills: {', '.join(profile.get('skills') or [])}",
        f"Goal: {profile.get('goal','')}",
        "\nCONTEXT:"
    ]
    for i, d in enumerate(docs[:10]):
        blocks.append(
            f"[Doc#{i+1}] source={d.metadata.get('source')} section={d.metadata.get('section')}\n{d.page_content}"
        )
    return "\n\n".join(blocks)


class GenerationService:
    def __init__(self) -> None:
        api_key = os.getenv("GOOGLE_API_KEY")
        self.model = None
        self._fallback_mode = not bool(api_key)
        if api_key:
            genai.configure(api_key=api_key)
            # Use a reliable text model
            self.model = genai.GenerativeModel("gemini-1.5-pro")

    def _fallback_plan(self, profile: Dict[str, Any], retrieved: Dict[str, Any]) -> Dict[str, Any]:
        branch = profile.get("branch") or "your branch"
        goal = profile.get("goal") or "your target role"
        top_docs = retrieved.get("documents", [])[:3]
        resources = []
        for doc in top_docs:
            source = doc.metadata.get("source", "reference material")
            resources.append({"title": str(source), "type": "reference"})
        return {
            "careerPath": f"A practical roadmap for {branch} students targeting {goal}.",
            "roadmap": [
                {
                    "title": "Foundation",
                    "steps": [
                        "Review the most relevant topics from the retrieved roadmap material.",
                        "Focus on the core skills repeatedly mentioned in the context.",
                    ],
                },
                {
                    "title": "Practice",
                    "steps": [
                        "Work through short projects aligned to the target role.",
                        "Use the provided documents as the primary study guide.",
                    ],
                },
            ],
            "resources": resources,
            "projects": ["Build one portfolio project grounded in the retrieved material."],
        }

    def _fallback_answer(self, question: str, profile: Dict[str, Any], retrieved: Dict[str, Any]) -> str:
        docs = retrieved.get("documents", [])
        if docs:
            source = docs[0].metadata.get("source", "the provided context")
            return (
                f"I cannot generate a Gemini-backed answer right now, but the most relevant source is {source}. "
                f"Use the retrieved roadmap material to answer: {question}"
            )
        return f"I do not have enough context to answer: {question}"

    def generate_plan(self, profile: Dict[str, Any], retrieved: Dict[str, Any]) -> Dict[str, Any]:
        if self.model is None:
            return self._fallback_plan(profile, retrieved)
        prompt = (
            SYSTEM_PROMPT
            + "\n\n" + _format_context(profile, retrieved["documents"]) + "\n\n"
            + "Return ONLY valid JSON as described."
        )
        response = self.model.generate_content(prompt)
        text = response.text or "{}"
        try:
            import json
            return json.loads(text)
        except Exception:
            # Best-effort JSON extraction
            import re, json
            m = re.search(r"\{[\s\S]*\}", text)
            if m:
                try:
                    return json.loads(m.group(0))
                except Exception:
                    pass
            return {"careerPath": "", "roadmap": [], "resources": [], "projects": []}

    def answer_question(self, question: str, profile: Dict[str, Any], retrieved: Dict[str, Any]) -> str:
        if self.model is None:
            return self._fallback_answer(question, profile, retrieved)
        context = _format_context(profile, retrieved["documents"])
        prompt = (
            "You answer questions grounded strictly in the provided context.\n"
            "If the answer is not in context, say you don't have enough info.\n\n"
            f"Question: {question}\n\n{context}"
        )
        response = self.model.generate_content(prompt)
        return (response.text or "").strip()


