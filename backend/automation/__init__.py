"""
LMA Automation Engine

Python-based automation system for lead management,
replacing n8n workflows with custom Python scripts.
"""

from .scheduler import AutomationScheduler
from .engine import AutomationEngine
from .scripts import ScriptManager

__all__ = [
    "AutomationScheduler", 
    "AutomationEngine", 
    "ScriptManager"
] 