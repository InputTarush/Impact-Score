# backend/llm_evaluator.py
import json
import requests

OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:1.5b"
REQUEST_TIMEOUT = 30.0  # Increased timeout from 8.0s to 30.0s


def generate_impact_scorecard(player_name: str, level: str, kinematics: dict) -> dict:
    """Queries local Ollama (Qwen2.5) to evaluate player kinematics and produce AI coaching feedback.

    Falls back smoothly to a rule engine if Ollama is unreachable.
    """
    elbow = kinematics.get("avg_elbow_angle", 118.5)
    knee = kinematics.get("avg_knee_angle", 138.2)
    fh = kinematics.get("forehand_score", 80)
    bh = kinematics.get("backhand_score", 78)
    fw = kinematics.get("footwork_score", 80)

    prompt = f"""You are an elite sports biomechanics AI coach analyzing a table tennis athlete.
    Player Name: {player_name}
    Claimed Level: {level}
    Biomechanical Telemetry:
    - Average Elbow Stroke Angle: {elbow}° (Optimal range: 115° - 125°)
    - Average Ready Stance Knee Flex: {knee}° (Optimal range: 130° - 142°)
    - Mechanics Scores: Forehand ({fh}/100), Backhand ({bh}/100), Footwork ({fw}/100)

    Provide a concise 3-sentence technical coaching assessment. Highlight one major strength in stroke form and one practical training exercise to improve footwork or stance recovery.
    """

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,
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
    """Generates structured fallback commentary using algorithmic heuristic rules."""
    elbow = kinematics.get("avg_elbow_angle", 118.5)
    knee = kinematics.get("avg_knee_angle", 138.2)
    fh = kinematics.get("forehand_score", 80)
    fw = kinematics.get("footwork_score", 80)

    # Technique checks
    elbow_status = "optimal extension" if 110 <= elbow <= 130 else "excessive arm tension"
    knee_status = "excellent center of gravity" if 128 <= knee <= 145 else "high athletic stance"

    summary = (
        f"{player_name} demonstrates solid execution at the {level} level with a forehand score of {fh}/100. "
        f"Kinematic tracking shows an average elbow flex of {elbow}°, indicating {elbow_status} during drive phases. "
        f"To improve stance transitions, work on multi-directional footwork ladder drills to optimize the {knee}° knee flex posture."
    )

    return {
        "source": "Rule-Engine Fallback",
        "summary": summary,
        "status": "fallback"
    }