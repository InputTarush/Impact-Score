import cv2
import mediapipe as mp
import numpy as np
from ultralytics import YOLO

class TTGameplayAnalyzer:
    def _init_(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        # Load lightweight YOLO model for ball/bat/person detection
        self.yolo_model = YOLO("yolov8n.pt")

    def _calc_angle(self, a, b, c):
        a, b, c = np.array(a), np.array(b), np.array(c)
        radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
        angle = np.abs(radians * 180.0 / np.pi)
        return float(360.0 - angle if angle > 180.0 else angle)

    def process_gameplay(self, video_path: str) -> dict:
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        
        elbow_angles = []
        knee_angles = []
        object_detections = {"ball_tracked_frames": 0, "person_tracked_frames": 0}
        total_frames = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            total_frames += 1

            # Run Pose Analysis on every 2nd frame for speed
            if total_frames % 2 == 0:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.pose.process(rgb)

                if results.pose_landmarks:
                    lm = results.pose_landmarks.landmark
                    # Arm Kinematics (Right Shoulder 12, Elbow 14, Wrist 16)
                    r_shoulder = [lm[12].x, lm[12].y]
                    r_elbow = [lm[14].x, lm[14].y]
                    r_wrist = [lm[16].x, lm[16].y]
                    elbow_angles.append(self._calc_angle(r_shoulder, r_elbow, r_wrist))

                    # Lower Body Stance (Hip 24, Knee 26, Ankle 28)
                    r_hip = [lm[24].x, lm[24].y]
                    r_knee = [lm[26].x, lm[26].y]
                    r_ankle = [lm[28].x, lm[28].y]
                    knee_angles.append(self._calc_angle(r_hip, r_knee, r_ankle))

            # Run YOLO Bounding Box checks periodically
            if total_frames % 10 == 0:
                yolo_res = self.yolo_model(frame, verbose=False)[0]
                for box in yolo_res.boxes:
                    cls_id = int(box.cls[0])
                    # Class 0: Person, Class 32: Sports ball
                    if cls_id == 0:
                        object_detections["person_tracked_frames"] += 1
                    elif cls_id == 32:
                        object_detections["ball_tracked_frames"] += 1

        cap.release()

        # Compute averages & technique consistency metrics
        avg_elbow = np.mean(elbow_angles) if elbow_angles else 0.0
        avg_knee = np.mean(knee_angles) if knee_angles else 0.0
        # Optimal forehand loop stroke joint flexion window: 105 - 135 deg
        optimal_stroke_pct = (np.mean([105 <= a <= 135 for a in elbow_angles]) * 100) if elbow_angles else 0.0
        # Good athletic crouching stance: Knee angle <= 145 deg
        good_stance_pct = (np.mean([a <= 145 for a in knee_angles]) * 100) if knee_angles else 0.0

        return {
            "total_frames_analyzed": total_frames,
            "avg_elbow_angle": round(float(avg_elbow), 2),
            "avg_knee_angle": round(float(avg_knee), 2),
            "stroke_consistency_pct": round(float(optimal_stroke_pct), 1),
            "footwork_readiness_pct": round(float(good_stance_pct), 1),
            "tracking_stats": object_detections
        }