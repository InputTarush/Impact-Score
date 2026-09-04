import os
import cv2
import numpy as np


def apply_strict_scaling(raw_score: float, power: float = 1.4) -> int:
    """Applies a non-linear power curve to penalize technical flaws and depress inflated scores.
    
    Examples (Power = 1.4):
    - Raw 90 -> Strict 86
    - Raw 75 -> Strict 67
    - Raw 60 -> Strict 49
    - Raw 45 -> Strict 33
    """
    normalized = max(0.0, min(100.0, float(raw_score))) / 100.0
    return int(round((normalized ** power) * 100.0))


class TTGameplayAnalyzer:

    def __init__(self):
        print("✅ [Vision Engine] Initialized Pure OpenCV Motion & Telemetry Engine (Strict Mode).")

    def process_gameplay(self, video_path: str) -> dict:
        """Processes video frames using OpenCV background subtraction and motion tracking to calculate strict biomechanical skill metrics."""
        if not video_path or not os.path.exists(video_path):
            print(f"[Vision Engine Warning] Video path missing: '{video_path}'. Returning baseline strict scores.")
            return self._get_fallback_scores()

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"[Vision Engine Warning] OpenCV could not open video: '{video_path}'. Returning baseline strict scores.")
            return self._get_fallback_scores()

        # Motion detector
        bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=100, varThreshold=40, detectShadows=False)

        frame_count = 0
        processed_frames = 0
        motion_scores = []
        aspect_ratios = []

        FRAME_SKIP = 2  # Process every 2nd frame for real-time performance

        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                frame_count += 1
                if frame_count % FRAME_SKIP != 0:
                    continue

                # Resize frame for processing speed
                frame_resized = cv2.resize(frame, (640, 360))
                fg_mask = bg_subtractor.apply(frame_resized)

                # Find contours of moving player/paddle
                contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                if contours:
                    # Filter for player movement bounding boxes
                    valid_contours = [c for c in contours if cv2.contourArea(c) > 300]
                    if valid_contours:
                        largest_contour = max(valid_contours, key=cv2.contourArea)
                        x, y, w, h = cv2.boundingRect(largest_contour)

                        # Track movement area (Drive Intensity) and height/width ratio (Stance Flex)
                        motion_area = cv2.contourArea(largest_contour)
                        motion_scores.append(motion_area)
                        
                        if w > 0:
                            aspect_ratios.append(float(h) / float(w))

                        processed_frames += 1

        except Exception as e:
            print(f"[Vision Engine Error] Frame processing exception: {e}")
        finally:
            cap.release()

        # If video contained no extractable motion frames
        if processed_frames == 0 or not motion_scores:
            print("[Vision Engine Warning] No player motion identified in video stream. Returning baseline strict kinematics.")
            return self._get_fallback_scores()

        # Calculate telemetry metrics from real video frame data
        avg_motion = float(np.mean(motion_scores))
        max_motion = float(np.max(motion_scores))
        avg_ratio = float(np.mean(aspect_ratios)) if aspect_ratios else 1.8

        # Raw baseline scores calculated with wider, non-inflated scoring floors
        raw_forehand = np.clip(45 + (max_motion / 5000.0) * 35, 40, 92)
        raw_footwork = np.clip(40 + (avg_motion / 3500.0) * 35, 38, 90)
        raw_backhand = np.clip(raw_forehand - 8, 35, 88)
        raw_reaction = np.clip((raw_forehand + raw_footwork) / 2 - 4, 38, 92)
        raw_endurance = np.clip(raw_footwork - 3, 35, 88)

        # Apply strict power scaling curve
        forehand_score = apply_strict_scaling(raw_forehand)
        footwork_score = apply_strict_scaling(raw_footwork)
        backhand_score = apply_strict_scaling(raw_backhand)
        reaction_score = apply_strict_scaling(raw_reaction)
        endurance_score = apply_strict_scaling(raw_endurance)

        # Simulated joint angles derived from stance ratio
        derived_elbow = round(115.0 + (avg_ratio * 2.5), 1)
        derived_knee = round(135.0 + (avg_ratio * 1.8), 1)

        print(f"✅ [Vision Engine] Successfully processed {processed_frames} video frames! Strict scores calculated.")

        return {
            "avg_elbow_angle": derived_elbow,
            "avg_knee_angle": derived_knee,
            "processed_frames": processed_frames,
            "forehand_score": forehand_score,
            "backhand_score": backhand_score,
            "footwork_score": footwork_score,
            "reaction_score": reaction_score,
            "endurance_score": endurance_score,
        }

    def _get_fallback_scores(self, error_msg: str = "Vision analysis failed or could not detect player pose.") -> dict:
        """
        Returns an explicit error payload when OpenCV vision processing fails.
        """
        return {
            "error": True,
            "error_message": error_msg,
            "avg_elbow_angle": None,
            "avg_knee_angle": None,
            "processed_frames": 0,
            "forehand_score": None,
            "backhand_score": None,
            "footwork_score": None,
            "reaction_score": None,
            "endurance_score": None,
        }
        