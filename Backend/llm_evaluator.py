# backend/llm_evaluator.py
import json
import requests

OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:1.5b"
REQUEST_TIMEOUT = 120.0


def generate_impact_scorecard(player_name: str, level: str, kinematics: dict) -> dict:
    """Queries local Ollama (Qwen2.5) to evaluate player kinematics using a strict, critical coaching persona."""
    elbow = kinematics.get("avg_elbow_angle", 118.5)
    knee = kinematics.get("avg_knee_angle", 138.2)
    fh = kinematics.get("forehand_score", 62)
    bh = kinematics.get("backhand_score", 58)
    fw = kinematics.get("footwork_score", 60)

    prompt = f"""You are an uncompromising National-Level Table Tennis Head Coach.
    Your job is to provide a rigorous, critical biomechanical critique. Do NOT use soft compliments, filler, or generic praise.
    Scores above 80 are strictly reserved for elite national athletes.

    Athlete Details:
    - Player Name: {player_name}
    - Claimed Level: {level}
    - Telemetry:
      * Elbow Stroke Angle: {elbow}° (Optimal: 115° - 125°)
      * Knee Flex Angle: {knee}° (Optimal: 130° - 142°)
      * Scores: Forehand ({fh}/100), Backhand ({bh}/100), Footwork ({fw}/100)

    Provide a concise 3-sentence technical evaluation. Identify at least TWO specific mechanical flaws or form breakdowns in stroke recovery or footwork, and specify one targeted corrective drill to fix them.
    """

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,  # Low temperature forces strict adherence to prompt constraints
            "num_predict": 200
        }
    }

    try:
        response = requests.post(OLLAMA_ENDPOINT, json=payload, timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            result = response.json()
            raw_text = result.get("response", "").strip()
            if raw_text:
                return {
                    "source": "LLM Engine (Qwen2.5)",
                    "summary": raw_text,
                    "status": "success"
                }

    except requests.exceptions.Timeout:
        print(f"[LLM Evaluator] Ollama API timed out (> {REQUEST_TIMEOUT}s). Falling back to Rule Engine.")
    except Exception as e:
        print(f"[LLM Evaluator] Ollama connection error: {e}. Falling back to Rule Engine.")

    # Rule-Engine Fallback
    return _get_rule_fallback_evaluation(player_name, level, kinematics)


def _get_rule_fallback_evaluation(player_name: str, level: str, kinematics: dict) -> dict:
    """Generates structured fallback commentary using strict algorithmic heuristics."""
    elbow = kinematics.get("avg_elbow_angle", 118.5)
    knee = kinematics.get("avg_knee_angle", 138.2)
    fh = kinematics.get("forehand_score", 62)
    fw = kinematics.get("footwork_score", 60)

    elbow_status = "acceptable elbow extension" if 115 <= elbow <= 125 else "mechanical inefficiency in arm drive"
    knee_status = "adequate low center of gravity" if 130 <= knee <= 142 else "excessively upright posture delaying lateral push-off"

    summary = (
        f"{player_name} demonstrates technical flaws for the {level} tier, scoring {fh}/100 on forehand execution. "
        f"Kinematic telemetry reveals {elbow_status} ({elbow}°) and {knee_status} ({knee}°). "
        f"Immediate correction requires shadow multi-ball drills and dynamic stance recovery exercises to lower center of gravity."
    )

    return {
        "source": "Rule-Engine Fallback",
        "summary": summary,
        "status": "fallback"
    }