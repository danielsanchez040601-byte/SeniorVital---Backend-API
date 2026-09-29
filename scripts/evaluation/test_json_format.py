"""Quick test: can phi3:mini follow JSON format?"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from src.services.llm import LLMService


async def test_json_format():
    llm = LLMService(base_url="http://localhost:11434", model="phi3:mini", timeout=120)

    # Test 1: Simple JSON instruction
    resp = await llm.generate(
        'Responde SOLO con este JSON: {"thought": "razonamiento", "final_answer": "respuesta"}',
        system="Eres un asistente. Responde solo en JSON, sin texto adicional.",
        format_json=False,
    )
    print("Test 1 (simple JSON):")
    print(f"  Response: {repr(resp[:200])}")
    print()

    # Test 2: With tools instruction
    resp2 = await llm.generate(
        'Usuario: ¿Qué ejercicios puedo hacer?\n\nResponde con: {"thought": "razonamiento", "action": "exercise_catalog", "action_input": {"category": "strength"}}',
        system="Eres un coach. Usa herramientas cuando sea necesario. Responde solo en JSON.",
        format_json=False,
    )
    print("Test 2 (tool call):")
    print(f"  Response: {repr(resp2[:200])}")
    print()

    # Test 3: format_json=True
    resp3 = await llm.generate(
        '{"thought": "razonamiento", "final_answer": "respuesta"}',
        system="Responde solo en JSON.",
        format_json=True,
    )
    print("Test 3 (format_json=True):")
    print(f"  Response: {repr(resp3[:200])}")


if __name__ == "__main__":
    asyncio.run(test_json_format())
