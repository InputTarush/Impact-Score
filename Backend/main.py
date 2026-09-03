# backend/main.py
import os
import shutil
import tempfile
from typing import Optional
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from vision_engine import TTGameplayAnalyzer
from llm_evaluator import generate_impact_scorecard

app = FastAPI(title="Impact Score AI Backend")

# Enable CORS for Streamlit frontend interaction
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize global vision analyzer
analyzer = TTGameplayAnalyzer()


@app.get("/")
def read_root():
    return {"status": "online", "engine": "Impact Score FastAPI AI Pipeline"}


@app.post("/analyze_applicant")
async def analyze_applicant(
    player_name: str = Form(...),
    claimed_level: str = Form("State Level"),
    video_file: Optional[UploadFile] = File(None),
    proof_file: Optional[UploadFile] = File(None),
):
    temp_dir = tempfile.mkdtemp()
    temp_video_path = None

    try:
        # 1. Save uploaded video to a temporary path if provided
        if video_file:
            temp_video_path = os.path.join(temp_dir, video_file.filename)
            with open(temp_video_path, "wb") as buffer:
                shutil.copyfileobj(video_file.file, buffer)

        # 2. Run Vision Analysis (MediaPipe Kinematics)
        kinematics = analyzer.process_gameplay(temp_video_path)

        # 3. Calculate overall score
        scores = [
            kinematics.get("forehand_score", 80),
            kinematics.get("backhand_score", 78),
            kinematics.get("footwork_score", 80),
            kinematics.get("reaction_score", 82),
            kinematics.get("endurance_score", 80),
        ]
        overall_score = sum(scores) // len(scores)

        # 4. Generate LLM Analysis & Coaching Commentary
        llm_insights = generate_impact_scorecard(
            player_name=player_name,
            level=claimed_level,
            kinematics=kinematics
        )

        return {
            "status": "success",
            "player_name": player_name,
            "claimed_level": claimed_level,
            "overall_score": overall_score,
            "kinematics": kinematics,
            "llm_evaluation": llm_insights,
        }

    except Exception as e:
        print(f"[Main API Error]: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Clean up temporary directory and files
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)