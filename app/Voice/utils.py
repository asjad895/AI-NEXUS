import logging
from dataclasses import dataclass, field
from typing import Annotated, Optional, List, Dict
from enum import Enum

import yaml
from dotenv import load_dotenv
from pydantic import Field

from livekit.agents.llm import function_tool
from livekit.agents.voice import Agent, RunContext
from opik import track
# add track on all tool

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

RunContext_T = RunContext[MedicalData]


@track
@function_tool()
async def update_name(
    name: Annotated[str, Field(description="The patient's full name")],
    context: RunContext_T,
) -> str:
    """Called when the patient provides their name.
    Confirm the spelling with the patient before calling this function."""
    userdata = context.userdata
    userdata.patient_name = name
    return f"Thank you, {name}. I've updated your name in our records."


@track
@function_tool()
async def update_age(
    age: Annotated[int, Field(description="The patient's age in years")],
    context: RunContext_T,
) -> str:
    """Called when the patient provides their age."""
    userdata = context.userdata
    userdata.patient_age = age
    return f"Thank you for sharing that you are {age} years old."


@track
@function_tool()
async def update_gender(
    gender: Annotated[str, Field(description="The patient's gender (male, female, other)")],
    context: RunContext_T,
) -> str:
    """Called when the patient provides their gender."""
    userdata = context.userdata
    if gender.lower() in ["male", "m"]:
        userdata.patient_gender = Gender.MALE
    elif gender.lower() in ["female", "f"]:
        userdata.patient_gender = Gender.FEMALE
    else:
        userdata.patient_gender = Gender.OTHER
    return f"Thank you for sharing your gender information."

@track
@function_tool()
async def update_contact(
    contact: Annotated[str, Field(description="The patient's contact number")],
    context: RunContext_T,
) -> str:
    """Called when the patient provides their contact number.
    Confirm the number with the patient before calling this function."""
    userdata = context.userdata
    userdata.patient_contact = contact
    return f"Thank you. I've recorded your contact number as {contact}."

@track
@function_tool()
async def update_email(
    email: Annotated[str, Field(description="The patient's email address")],
    context: RunContext_T,
) -> str:
    """Called when the patient provides their email address.
    Confirm the spelling with the patient before calling this function."""
    userdata = context.userdata
    userdata.patient_email = email
    return f"Thank you. I've updated your email address as {email}."


@track
@function_tool()
async def update_address(
    address: Annotated[str, Field(description="The patient's residential address")],
    context: RunContext_T,
) -> str:
    """Called when the patient provides their address.
    Confirm the address with the patient before calling this function."""
    userdata = context.userdata
    userdata.patient_address = address
    return f"Thank you. I've recorded your address."

@track
@function_tool()
async def update_pain_details(
    location: Annotated[str, Field(description="Location of the pain")],
    severity: Annotated[str, Field(description="Severity of the pain (mild, moderate, severe)")],
    duration: Annotated[str, Field(description="Duration of the pain (e.g., '2 days', '3 weeks')")],
    context: RunContext_T,
) -> str:
    """Called when the patient provides details about their pain."""
    userdata = context.userdata
    userdata.pain_location = location
    
    if severity.lower() == "mild":
        userdata.pain_severity = PainSeverity.MILD
    elif severity.lower() == "moderate":
        userdata.pain_severity = PainSeverity.MODERATE
    elif severity.lower() == "severe":
        userdata.pain_severity = PainSeverity.SEVERE
    else:
        userdata.pain_severity = PainSeverity.UNKNOWN
        
    userdata.pain_duration = duration
    return f"Thank you for sharing about your {severity} pain in the {location} area for {duration}. This helps us understand your condition better."

@track
@function_tool()
async def add_medication(
    name: Annotated[str, Field(description="Name of the medication")],
    dosage: Annotated[str, Field(description="Dosage of the medication")],
    frequency: Annotated[str, Field(description="Frequency of taking the medication")],
    context: RunContext_T,
) -> str:
    """Called when the patient provides details about a medication they're taking."""
    userdata = context.userdata
    if userdata.medication is None:
        userdata.medication = []
        
    userdata.medication.append({
        "name": name,
        "dosage": dosage,
        "frequency": frequency
    })
    return f"I've noted that you're taking {name} {dosage} {frequency}."

@track
@function_tool()
async def add_symptom(
    symptom: Annotated[str, Field(description="Description of the symptom")],
    duration: Annotated[str, Field(description="Duration of the symptom")],
    severity: Annotated[str, Field(description="Severity of the symptom")],
    context: RunContext_T,
) -> str:
    """Called when the patient provides details about a symptom they're experiencing."""
    userdata = context.userdata
    if userdata.symptoms is None:
        userdata.symptoms = []
        
    userdata.symptoms.append({
        "symptom": symptom,
        "duration": duration,
        "severity": severity
    })
    return f"I've noted your {severity} {symptom} that you've been experiencing for {duration}."

@track
@function_tool()
async def add_allergy(
    allergy: Annotated[str, Field(description="Type of allergy")],
    severity: Annotated[str, Field(description="Severity of the allergy")],
    context: RunContext_T,
) -> str:
    """Called when the patient provides details about an allergy they have."""
    userdata = context.userdata
    if userdata.allergies is None:
        userdata.allergies = []
        
    userdata.allergies.append({
        "allergy": allergy,
        "severity": severity
    })
    return f"I've recorded your {severity} allergy to {allergy}."

@track
@function_tool()
async def add_surgery(
    surgery: Annotated[str, Field(description="Type of surgery")],
    date: Annotated[str, Field(description="Date of the surgery")],
    context: RunContext_T,
) -> str:
    """Called when the patient provides details about a surgery they've had."""
    userdata = context.userdata
    if userdata.surgeries is None:
        userdata.surgeries = []
        
    userdata.surgeries.append({
        "surgery": surgery,
        "date": date
    })
    return f"I've noted your {surgery} procedure from {date}."

@track
@function_tool()
async def add_family_history(
    condition: Annotated[str, Field(description="Medical condition in family history")],
    relation: Annotated[str, Field(description="Relation of the family member")],
    context: RunContext_T,
) -> str:
    """Called when the patient provides details about their family medical history."""
    userdata = context.userdata
    if userdata.family_history is None:
        userdata.family_history = []
        
    userdata.family_history.append({
        "condition": condition,
        "relation": relation
    })
    return f"I've recorded that your {relation} has {condition} in your family medical history."

@track
@function_tool()
async def add_lifestyle_factor(
    factor: Annotated[str, Field(description="Lifestyle factor")],
    details: Annotated[str, Field(description="Details about the lifestyle factor")],
    context: RunContext_T,
) -> str:
    """Called when the patient provides details about relevant lifestyle factors."""
    userdata = context.userdata
    if userdata.lifestyle_factors is None:
        userdata.lifestyle_factors = []
        
    userdata.lifestyle_factors.append({
        "factor": factor,
        "details": details
    })
    return f"Thank you for sharing about your {factor}: {details}."


@track
@function_tool()
async def update_service_requested(
    service: Annotated[str, Field(description="Service requested by the patient")],
    context: RunContext_T,
) -> str:
    """Called when the patient specifies what service they're looking for."""
    userdata = context.userdata
    userdata.service_requested = service
    return f"I understand you're looking for {service}. We can definitely assist you with that."


@track
@function_tool()
async def add_notes(
    notes: Annotated[str, Field(description="Additional notes about the patient")],
    context: RunContext_T,
) -> str:
    """Called to add additional notes to the patient record."""
    userdata = context.userdata
    userdata.notes = notes
    return "I've added these additional notes to your record."
