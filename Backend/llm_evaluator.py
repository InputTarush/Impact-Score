import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"

def generate_impact_scorecard(player_name: str, level: str, kinematics: dict, proof: dict) -> dict:
    prompt = f"""
    You are an elite Table Tennis Performance Analyst evaluating a player for CSR grant funding.
    
    Player Info:
    - Name: {player_name}
    - Claimed Level: {level} (Document Verification Score: {proof['trust_score']}/100)
    
    Kinematics & Computer Vision Metrics:
    - Forehand Loop Stroke Consistency: {kinematics['stroke_consistency_pct']}%
    - Athletic Stance & Footwork Readiness: {kinematics['footwork_readiness_pct']}%
    - Average Elbow Flexion: {kinematics['avg_elbow_angle']} degrees
    
    Respond STRICTLY with a JSON object containing key fields:
    "overall_score" (number 0-100),
    "strengths" (list of strings),
    "weaknesses" (list of strings),
    "grant_priority" ("HIGH", "MEDIUM", "LOW"),
    "recommended_grant_inr" (number),
    "executive_summary" (string)
    """

    payload = {
        "model": "qwen2.5:1.5b",
        "prompt": prompt,
        "format": "json",
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=8.0)
        if response.status_code == 200:
            return json.loads(response.json()["response"])
    except Exception as e:
        print(f"LLM API Error/Timeout: {e}. Falling back to Rule Engine.")

    # Fallback response if local LLM service times out
    base_score = int((kinematics['stroke_consistency_pct'] + proof['trust_score']) / 2)
    return {
        "overall_score": base_score,
        "strengths": ["Strong forearm recovery speed", "Documented level history"],
        "weaknesses": ["Knee bend posture needs lower gravity stance"],
        "grant_priority": "HIGH" if base_score > 75 else "MEDIUM",
        "recommended_grant_inr": 100000 if base_score > 75 else 50000,
        "executive_summary": "Automated evaluation generated based on biomechanical consistency."
    }