"""Tests for RoutinePromptBuilder."""

from src.agents.wellness.prompts.routine_builder import RoutinePromptBuilder


def test_build_prompt_contains_user_age():
    builder = RoutinePromptBuilder()
    prompt = builder.build(
        profile={},
        health_profile={"age": 72},
        preferences={},
        safe_exercises=[],
    )
    assert "72" in prompt


def test_build_prompt_contains_exercise_name():
    builder = RoutinePromptBuilder()
    prompt = builder.build(
        profile={},
        health_profile={},
        preferences={},
        safe_exercises=[{"id": 1, "name": "Sentadilla", "level": 2, "duration_min": 5}],
    )
    assert "Sentadilla" in prompt


def test_build_prompt_contains_restriction():
    builder = RoutinePromptBuilder()
    prompt = builder.build(
        profile={},
        health_profile={"medical_restrictions": ["hipertensión"]},
        preferences={},
        safe_exercises=[],
    )
    assert "hipertensión" in prompt


def test_build_prompt_contains_favorites():
    builder = RoutinePromptBuilder()
    prompt = builder.build(
        profile={},
        health_profile={},
        preferences={"favorite_exercises": ["yoga", "caminata"]},
        safe_exercises=[],
    )
    assert "yoga" in prompt
    assert "caminata" in prompt


def test_build_prompt_system_prompt():
    builder = RoutinePromptBuilder()
    system = builder.build_system_prompt()
    assert "adulto mayor" in system.lower() or "adultos mayores" in system.lower()


def test_build_prompt_json_format():
    builder = RoutinePromptBuilder()
    prompt = builder.build(
        profile={},
        health_profile={},
        preferences={},
        safe_exercises=[],
    )
    assert '"exercises"' in prompt
    assert '"warmup"' in prompt
