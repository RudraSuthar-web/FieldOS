"""Operational Intelligence Extraction Service.

Parses unstructured multilingual technician voice transcriptions (Gujarati, Hindi,
English, Hinglish) into structured operational field reports, assesses severity,
detects missing operational details, and generates context-aware clarification questions
and spoken confirmations for Gnani Timbre TTS.
"""

from __future__ import annotations

import logging
import re
from typing import List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

INDIC_DIGIT_MAP = str.maketrans({
    "०": "0", "१": "1", "२": "2", "३": "3", "४": "4",
    "५": "5", "६": "6", "७": "7", "૮": "8", "९": "9",
    "૦": "0", "૧": "1", "૨": "2", "૩": "3", "૪": "4",
    "૫": "5", "૬": "6", "૭": "7", "૮": "8", "૯": "9",
})

EQUIPMENT_KEYWORDS = [
    ("boiler", "Boiler"), ("બોઇલર", "Boiler"), ("બૉઇલર", "Boiler"), ("बॉयलर", "Boiler"),
    ("conveyor belt", "Conveyor"), ("conveyor", "Conveyor"), ("કન્વેયર બેલ્ટ", "Conveyor"),
    ("કન્વેયર", "Conveyor"), ("कन्वेयर", "Conveyor"),
    ("compressor", "Compressor"), ("કોમ્પ્રેસર", "Compressor"), ("कंप्रेसर", "Compressor"),
    ("generator", "Generator"), ("જનરેટર", "Generator"), ("जनरेटर", "Generator"),
    ("turbine", "Turbine"), ("ટર્બાઇન", "Turbine"), ("टर्बाइन", "Turbine"),
    ("motor", "Motor"), ("મોટર", "Motor"), ("मोटर", "Motor"),
    ("pump", "Pump"), ("પંપ", "Pump"), ("पंप", "Pump"),
    ("chiller", "Chiller"), ("ચિલર", "Chiller"), ("चिलर", "Chiller"),
    ("lathe", "Lathe"), ("લેથ", "Lathe"), ("लेथ", "Lathe"),
    ("press", "Press"), ("પ્રેસ", "Press"), ("प्रेस", "Press"),
    ("pipeline", "Pipeline"), ("પાઇપલાઇન", "Pipeline"), ("पाइपलाइन", "Pipeline"),
    ("line", "Line"), ("લાઇન", "Line"), ("लाइन", "Line"),
    ("machine", "Machine"), ("સંચો", "Machine"), ("મશીન", "Machine"), ("मशीन", "Machine"),
    ("unit", "Unit"), ("યુનિટ", "Unit"), ("यूनिट", "Unit"),
]


class ExtractedIntelligence(BaseModel):
    equipment_id: str = Field(default="M-12", description="Equipment identifier")
    equipment_name: str = Field(default="Machine 12", description="Display name of equipment")
    equipment_machine_number: str = Field(default="12", description="Machine number if present")
    issue: str = Field(default="Reported issue", description="Primary fault or observation")
    observation: Optional[str] = Field(default=None, description="Detailed observations")
    category: str = Field(default="mechanical", description="mechanical/electrical/hydraulic/safety/general")
    severity: str = Field(default="medium", description="low/medium/high/critical")
    missing_fields: List[str] = Field(default_factory=list, description="Missing operational fields")
    clarification_question: Optional[str] = Field(default=None, description="Follow-up question if details are missing")
    confirmation_message: str = Field(
        default="Work order created and recorded successfully.",
        description="Spoken confirmation message for the technician",
    )


class IntelligenceService:
    """Operational reasoning engine for multilingual field operations."""

    def __init__(self):
        pass

    async def extract(self, transcription: str, language: str = "english") -> ExtractedIntelligence:
        """Extract structured operational data from voice transcription."""
        if not transcription.strip():
            return ExtractedIntelligence()

        return self._extract_operational_data(transcription, language)

    def _extract_operational_data(self, text: str, language: str) -> ExtractedIntelligence:
        # Convert Indic numerals (Gujarati, Devanagari) to ASCII digits
        normalized_text = text.translate(INDIC_DIGIT_MAP)
        text_lower = normalized_text.lower().strip()

        # -------------------------------------------------------------
        # 1. Equipment Identification
        # -------------------------------------------------------------
        eq_type = "Machine"
        for kw, label in EQUIPMENT_KEYWORDS:
            if kw in text_lower:
                eq_type = label
                break

        num = None
        # Explicit number pattern: e.g. "number 12", "no. 12", "#12", "નંબર ૧૨", "नंबर 12"
        m_explicit = re.search(r"(?:number|no\.?|#|નંબર|નં\.?|नंबर|नं\.?)\s*([0-9]{1,4})\b", text_lower)
        if m_explicit:
            num = m_explicit.group(1)

        # Pattern: equipment followed immediately by digits: e.g. "machine 12", "motor 4", "pump 3", "लाइन 6"
        if not num:
            m_adjacent = re.search(
                r"(?:machine|motor|pump|unit|equipment|turbine|conveyor|press|generator|boiler|compressor|chiller|lathe|pipeline|line|સંચો|મશીન|મોટર|પંપ|લાઇન|मशीन|मोटर|उपकरण|पंप|लाइन)\s*([0-9]{1,4})\b",
                text_lower,
            )
            if m_adjacent:
                num = m_adjacent.group(1)

        # Standalone digits (1-3 digits)
        if not num:
            m_digits = re.search(r"\b([0-9]{1,3})\b", text_lower)
            if m_digits:
                num = m_digits.group(1)

        final_num = num if num else "12"
        equipment_id = f"M-{final_num}"
        equipment_name = f"{eq_type} {final_num}"

        # -------------------------------------------------------------
        # 2. Operating Status Detection
        # -------------------------------------------------------------
        is_stopped = any(
            k in text_lower
            for k in [
                "stopped", "shut down", "shutdown", "bandh", "band", "halted",
                "turned off", "बंद", "बंद कर", "બંધ", "બંધ કરી", "અટકી"
            ]
        )
        is_running = any(
            k in text_lower
            for k in [
                "running", "operating", "chalu", "chal", "on", "chal rahi",
                "चालू", "चल रही", "चल रहा", "ચાલુ", "કામ કરે"
            ]
        )

        # -------------------------------------------------------------
        # 3. Severity Classification
        # -------------------------------------------------------------
        critical_keywords = [
            "critical", "emergency", "fire", "smoke", "blast", "danger", "exploded",
            "injur", "hazard", "ag", "aag", "dhuan", "dhunvo", "bhadko", "urgent",
            "blaze", "burning", "immediate", "catastrophic",
            "આગ", "ધુમાડો", "ધમાકો", "ખતરો", "ઈમરજન્સી", "તાત્કાલિક", "બળ", "બળી", "બ્લાસ્ટ",
            "धुआं", "खतरा", "इमरजेंसी", "धमाका", "तुरंत", "आग", "विस्फोट", "आपातकाल"
        ]
        high_keywords = [
            "overheating", "overheat", "vibration", "leak", "high", "garam", "garmi",
            "dhrujari", "risav", "tapman", "vadhi", "badh", "broken", "damage", "ruptur",
            "jam", "jammed", "stopped", "failed", "down", "halt", "crack", "seized", "overload",
            "pressure drop", "oil leak", "heavy", "severe", "burning smell",
            "ગરમ", "ગરમી", "ધ્રુજારી", "વાઇબ્રેશન", "ઓવરહીટિંગ", "ઓવરહીટ", "લીક", "રિસાવા",
            "તૂટેલું", "જામ", "બંધ", "બગડી", "તાપમાન", "વધારે", "ભારે",
            "गर्म", "गरम", "वाइब्रेशन", "कंपन", "लीक", "रिसाव", "टूटा", "जाम", "बंद", "खराब", "तापमान", "ज्यादा"
        ]
        medium_keywords = [
            "noise", "slow", "sound", "loose", "awaj", "awaaz", "ghisi", "vibrat",
            "unusual", "friction", "slip", "slipping", "wear", "worn", "fluctuat",
            "અવાજ", "ધીમા", "ઢીલું", "ઘસારો", "આવાજ", "પ્રેશર",
            "धीमा", "आवाज", "ढीला", "प्रेशर", "फिसल"
        ]

        if any(w in text_lower for w in critical_keywords):
            severity = "critical"
        elif any(w in text_lower for w in high_keywords):
            severity = "high"
        elif any(w in text_lower for w in medium_keywords):
            severity = "medium"
        else:
            severity = "low"

        # -------------------------------------------------------------
        # 4. Operational Category Classification
        # -------------------------------------------------------------
        electrical_keywords = [
            "wire", "spark", "voltage", "current", "short", "power", "electrical",
            "bijli", "circuit", "fuse", "breaker", "cable", "motor", "viijli", "switch",
            "generator", "transformer", "phase", "trip", "tripped",
            "વીજળી", "સ્પાર્ક", "વાયર", "મોટર", "શોર્ટ", "જનરેટર",
            "बिजली", "स्पार्क", "तार", "मोटर", "शॉर्ट", "जनरेटर", "करंट"
        ]
        hydraulic_keywords = [
            "oil", "leak", "pressure", "pipe", "fluid", "hydraulic", "valve", "cylinder",
            "seal", "tank", "teji", "drub", "water", "hose", "coolant", "chemical",
            "તેલ", "લીક", "પાઇપ", "પ્રેશર", "પાણી", "વાલ્વ", "કૂલન્ટ",
            "तेल", "लीक", "पाइप", "प्रेशर", "पानी", "वाल्व", "रिसाव"
        ]
        safety_keywords = [
            "safety", "hazard", "guard", "fire", "smoke", "shield", "protective", "alarm",
            "emergency", "blast", "danger", "ag", "aag", "dhuan", "dhunvo", "bhadko",
            "gas", "toxic", "injury", "chemical spill",
            "સુરક્ષા", "આગ", "ધુમાડો", "ખતરો", "ગેસ",
            "सुरक्षा", "आग", "धुआं", "खतरा", "गैस"
        ]

        if any(w in text_lower for w in safety_keywords):
            category = "safety"
        elif any(w in text_lower for w in hydraulic_keywords):
            category = "hydraulic"
        elif any(w in text_lower for w in electrical_keywords):
            category = "electrical"
        else:
            category = "mechanical"

        # -------------------------------------------------------------
        # 5. Specific Issue Extraction
        # -------------------------------------------------------------
        has_fire = any(k in text_lower for k in ["fire", "smoke", "blast", "ag", "aag", "dhuan", "आग", "धुआं", "ધુમાડો"])
        has_overheat = any(k in text_lower for k in ["overheat", "garam", "garmi", "ગરમ", "ગરમી", "गर्म", "गरम", "ઓવરહીટિંગ", "ઓવરહીટ"])
        has_vibration = any(k in text_lower for k in ["vibrat", "dhrujari", "ધ્રુજારી", "कंपन", "વાઇબ્રેશન", "वाइब्रेशन"])
        has_leak = any(k in text_lower for k in ["leak", "risav", "લીક", "રિસાવા", "रिसाव"])
        has_noise = any(k in text_lower for k in ["noise", "sound", "awaj", "awaaz", "screech", "grind", "અવાજ", "આવાજ", "आवाज"])
        has_spark = any(k in text_lower for k in ["spark", "short", "સ્પાર્ક", "स्पार्क", "शॉर्ट"])
        has_jam = any(k in text_lower for k in ["jam", "stuck", "chonti", "bind", "seized", "જામ", "जाम", "अटका"])
        has_pressure = any(k in text_lower for k in ["pressure", "drop", "pressure loss", "પ્રેશર", "प्रेशर"])
        has_loose_belt = any(k in text_lower for k in ["belt loose", "belt slipping", "loose belt", "બેલ્ટ ઢીલો", "बेल्ट ढीला"])
        has_stopped_fail = any(k in text_lower for k in ["stopped working", "won't start", "wont start", "failed to start", "काम नहीं कर रहा", "બંધ થઈ ગયું"])

        if has_fire:
            issue = "Fire or smoke hazard detected"
        elif has_overheat:
            # Overheating primary fault
            issue = "Motor overheating"
        elif has_vibration:
            issue = "Abnormal vibration"
        elif has_leak:
            issue = "Fluid leak detected"
        elif has_noise:
            issue = "Abnormal operating noise"
        elif has_spark:
            issue = "Electrical sparking or short circuit"
        elif has_jam:
            issue = "Mechanical binding or jam"
        elif has_pressure:
            issue = "Hydraulic pressure loss"
        elif has_loose_belt:
            issue = "Drive belt slipping or loose"
        elif has_stopped_fail:
            issue = "Equipment operational failure"
        else:
            # Clean up text: strip common reporting preambles
            clean = re.sub(
                r"^(?:technician\s+[\w\s]+reporting:?|reporting:?|please\s+note\s+that:?|there\s+is\s+an\s+issue\s+with:?|issue\s+with:?)\s*",
                "",
                text,
                flags=re.IGNORECASE,
            ).strip()
            # Take up to the first natural clause delimiter
            clause = re.split(r"[;,\.\n]|(?:\b(?:and|but|or|please|check)\b)", clean, flags=re.IGNORECASE)[0].strip()
            if len(clause) >= 5:
                issue = clause[:80].capitalize()
            else:
                issue = text[:60].strip() if len(text) > 5 else "Unspecified operational anomaly"

        # -------------------------------------------------------------
        # 6. Detailed Observations Extraction
        # -------------------------------------------------------------
        obs_bullets = []
        if has_fire:
            obs_bullets.append("Critical thermal hazard: active smoke or flame emission reported")
        if has_vibration:
            obs_bullets.append("Elevated vibration observed during field inspection")
        if has_overheat:
            obs_bullets.append("Abnormal heat emission detected around motor/equipment casing")
        if has_noise:
            obs_bullets.append("Audible abnormal noise, rattling or grinding reported")
        if has_leak:
            obs_bullets.append("Visible fluid residue or active leakage around joints/casing")
        if has_spark:
            obs_bullets.append("Intermittent electrical arcing or sparks observed")
        if has_pressure:
            obs_bullets.append("Hydraulic/system pressure drop recorded")
        if is_stopped:
            obs_bullets.append("Equipment status: Stopped / Shut down")
        elif is_running:
            obs_bullets.append("Equipment status: Actively operating")

        # Combine clinical diagnostic notes with technician transcription
        raw_clean = text.strip()
        if obs_bullets:
            observation = f"{'; '.join(obs_bullets)}. Reported: \"{raw_clean}\""
        else:
            observation = f"Reported: \"{raw_clean}\""

        # -------------------------------------------------------------
        # 7. Missing Fields & Conversational Clarification Question
        # -------------------------------------------------------------
        missing_fields = []
        if not (is_stopped or is_running):
            missing_fields.append("operating_status")

        lang_key = language.lower().strip()
        if "gujarati" in lang_key or "gu" == lang_key:
            clarification_question = "શું મશીન અત્યારે ચાલુ છે કે બંધ કરી દેવામાં આવ્યું છે?" if missing_fields else None
            confirmation_message = f"{equipment_name} માટે {issue} નો રિપોર્ટ રેકોર્ડ થયો છે. વર્ક ઓર્ડર સફળતાપૂર્વક જનરેટ થઈ ગયો છે."
        elif "hindi" in lang_key or "hi" == lang_key or "hinglish" in lang_key:
            clarification_question = "क्या मशीन अभी चल रही है या उसे बंद कर दिया गया है?" if missing_fields else None
            confirmation_message = f"{equipment_name} के लिए {issue} की रिपोर्ट दर्ज कर ली गई है। वर्क ऑर्डर तैयार है।"
        else:
            clarification_question = "Is the machine currently operating, or has it been shut down?" if missing_fields else None
            confirmation_message = f"Report for {equipment_name} regarding {issue} has been confirmed. Work order generated."

        return ExtractedIntelligence(
            equipment_id=equipment_id,
            equipment_name=equipment_name,
            equipment_machine_number=final_num,
            issue=issue,
            observation=observation,
            category=category,
            severity=severity,
            missing_fields=missing_fields,
            clarification_question=clarification_question,
            confirmation_message=confirmation_message,
        )


_intelligence_service: Optional[IntelligenceService] = None


def get_intelligence_service() -> IntelligenceService:
    global _intelligence_service
    if _intelligence_service is None:
        _intelligence_service = IntelligenceService()
    return _intelligence_service
