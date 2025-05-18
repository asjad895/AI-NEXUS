from __future__ import annotations

from enum import Enum
from typing import Literal
from dataclasses import dataclass

TTSModels = Literal["bulbul:v1","bulbul:v2"]


TTSLanguageCodes = Literal[
    "en-IN",
    "hi-IN",
    "bn-IN",
    "gu-IN",
    "kn-IN",
    "ml-IN",
    "mr-IN",
    "od-IN",
    "pa-IN",
    "ta-IN",
    "te-IN",
]
    

TTSSpeakers = Literal[
    "diya",
    "maya",
    "meera",
    "pavithra",
    "maitreyi",
    "misha",
    "amol",
    "arjun",
    "amartya",
    "arvind",
    "neel",
    "vian",
    "anushka",
    "manisha",
    "vidya",
    "arya",
    "abhilash",
    "karun",
    "hitesh",
]