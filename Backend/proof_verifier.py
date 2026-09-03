import cv2
import pytesseract
import re

class CertificateProofVerifier:
    def _init_(self):
        # Mandatory sports verification keywords
        self.core_keywords = ["table tennis", "ping pong", "championship", "tournament", "association", "federation"]
        self.level_keywords = {
            "National": ["national", "india", "all india", "inter-state"],
            "State": ["state", "championship", "state level"],
            "District": ["district", "zonal", "inter-school"]
        }

    def verify_proof(self, cert_image_path: str, claimed_level: str) -> dict:
        image = cv2.imread(cert_image_path)
        if image is None:
            return {"verified": False, "trust_score": 0, "reason": "Invalid or unreadable document file."}

        # OCR Text Extraction
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        extracted_text = pytesseract.image_to_string(gray).lower()

        # Check 1: Mandatory Sports Association context
        found_core = any(kw in extracted_text for kw in self.core_keywords)
        
        # Check 2: Level-matching verification
        claimed_keywords = self.level_keywords.get(claimed_level, [])
        found_level = any(kw in extracted_text for kw in claimed_keywords)

        # Trust Score Calculation
        trust_score = 0
        if found_core:
            trust_score += 50
        if found_level:
            trust_score += 40
        if len(extracted_text.strip()) > 100:  # Valid document density check
            trust_score += 10

        verified = trust_score >= 70

        return {
            "verified": verified,
            "trust_score": trust_score,
            "claimed_level": claimed_level,
            "ocr_text_snippet": extracted_text[:200].replace("\n", " "),
            "status": "VERIFIED_GENUINE" if verified else "FLAGGED_FOR_MANUAL_REVIEW"
        }