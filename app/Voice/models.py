import logging
from dataclasses import dataclass, field
from typing import Annotated, Optional, List, Dict
from enum import Enum

import yaml
from dotenv import load_dotenv
from livekit.agents.voice import Agent

load_dotenv()

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"

class PainSeverity(str, Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    UNKNOWN = "unknown"

@dataclass
class MedicalData:
    patient_name: Optional[str] = None
    patient_age: Optional[int] = None
    patient_gender: Optional[Gender] = None
    patient_contact: Optional[str] = None
    patient_email: Optional[str] = None
    patient_address: Optional[str] = None
    
    pain_location: Optional[str] = None
    pain_severity: Optional[PainSeverity] = None
    pain_duration: Optional[str] = None
    
    medication: Optional[List[Dict[str, str]]] = field(default_factory=list)
    symptoms: Optional[List[Dict[str, str]]] = field(default_factory=list)
    allergies: Optional[List[Dict[str, str]]] = field(default_factory=list)
    surgeries: Optional[List[Dict[str, str]]] = field(default_factory=list)
    family_history: Optional[List[Dict[str, str]]] = field(default_factory=list)
    lifestyle_factors: Optional[List[Dict[str, str]]] = field(default_factory=list)
    
    notes: Optional[str] = None
    
    service_requested: Optional[str] = None
    
    agents: dict[str, Agent] = field(default_factory=dict)
    prev_agent: Optional[Agent] = None
    
    mandatory_fields_collected: bool = False
    
    def summarize(self) -> str:
        """Create a summary of the patient data in YAML format"""
        data = {
            "patient_details": {
                "name": self.patient_name or "unknown",
                "age": self.patient_age or "unknown",
                "gender": self.patient_gender or "unknown",
                "contact": self.patient_contact or "unknown",
                "email": self.patient_email or "unknown",
                "address": self.patient_address or "unknown",
            },
            "medical_details": {
                "pain": {
                    "location": self.pain_location or "unknown",
                    "severity": self.pain_severity or "unknown",
                    "duration": self.pain_duration or "unknown",
                },
                "medication": self.medication or [],
                "symptoms": self.symptoms or [],
                "allergies": self.allergies or [],
                "surgeries": self.surgeries or [],
                "family_history": self.family_history or [],
                "lifestyle_factors": self.lifestyle_factors or [],
            },
            "service_requested": self.service_requested or "unknown",
            "notes": self.notes or "",
            "mandatory_fields_collected": self.mandatory_fields_collected,
        }
        return yaml.dump(data)
    
    def check_mandatory_fields(self) -> bool:
        """Check if all mandatory fields have been collected"""
        mandatory_fields = [
            self.patient_name,
            self.patient_age,
            self.patient_gender,
            self.patient_contact,
            self.patient_email,
            self.patient_address
        ]
        self.mandatory_fields_collected = all(field is not None for field in mandatory_fields)
        return self.mandatory_fields_collected
