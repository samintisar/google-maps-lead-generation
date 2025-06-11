"""
Script Manager

Manages automation scripts, templates, and script discovery.
Provides a registry for different types of automation scripts.
"""

import logging
import os
import importlib
import inspect
from typing import Dict, Any, List, Callable, Optional
from pathlib import Path
import asyncio

logger = logging.getLogger(__name__)

class ScriptManager:
    """
    Manages automation scripts and templates.
    Handles script discovery, loading, and organization.
    """
    
    def __init__(self, scripts_directory: str = None):
        self.scripts_directory = scripts_directory or "automation/scripts"
        self.scripts: Dict[str, Dict[str, Any]] = {}
        self.templates: Dict[str, Dict[str, Any]] = {}
        
    def register_script(
        self, 
        name: str, 
        script_func: Callable,
        category: str = "general",
        description: str = "",
        parameters: Dict[str, Any] = None,
        schedule: str = None
    ):
        """
        Register an automation script
        
        Args:
            name: Unique script name
            script_func: The script function
            category: Script category (e.g., 'lead_enrichment', 'outreach', 'crm')
            description: Human-readable description
            parameters: Expected parameters schema
            schedule: Default schedule if any
        """
        self.scripts[name] = {
            'function': script_func,
            'category': category,
            'description': description,
            'parameters': parameters or {},
            'schedule': schedule,
            'is_async': asyncio.iscoroutinefunction(script_func),
            'signature': inspect.signature(script_func)
        }
        logger.info(f"Registered script: {name} in category: {category}")
    
    def get_script(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a script by name"""
        return self.scripts.get(name)
    
    def get_scripts_by_category(self, category: str) -> Dict[str, Dict[str, Any]]:
        """Get all scripts in a category"""
        return {
            name: script for name, script in self.scripts.items() 
            if script['category'] == category
        }
    
    def list_scripts(self) -> List[Dict[str, Any]]:
        """List all registered scripts"""
        return [
            {
                'name': name,
                'category': script['category'],
                'description': script['description'],
                'parameters': script['parameters'],
                'schedule': script['schedule'],
                'is_async': script['is_async']
            }
            for name, script in self.scripts.items()
        ]
    
    def list_categories(self) -> List[str]:
        """List all script categories"""
        return list(set(script['category'] for script in self.scripts.values()))
    
    def create_template(
        self, 
        name: str, 
        steps: List[Dict[str, Any]],
        description: str = "",
        parameters: Dict[str, Any] = None
    ):
        """
        Create a workflow template
        
        Args:
            name: Template name
            steps: List of workflow steps
            description: Template description
            parameters: Template parameters
        """
        self.templates[name] = {
            'steps': steps,
            'description': description,
            'parameters': parameters or {},
            'created_at': None  # Would be set in actual implementation
        }
        logger.info(f"Created template: {name}")
    
    def get_template(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a template by name"""
        return self.templates.get(name)
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """List all templates"""
        return [
            {
                'name': name,
                'description': template['description'],
                'parameters': template['parameters'],
                'step_count': len(template['steps'])
            }
            for name, template in self.templates.items()
        ]
    
    def discover_scripts(self, directory: str = None):
        """
        Discover and load scripts from a directory
        
        Args:
            directory: Directory to scan for scripts
        """
        directory = directory or self.scripts_directory
        scripts_path = Path(directory)
        
        if not scripts_path.exists():
            logger.warning(f"Scripts directory does not exist: {directory}")
            return
        
        # Scan for Python files
        for script_file in scripts_path.glob("**/*.py"):
            if script_file.name.startswith("__"):
                continue
                
            try:
                # Import the module
                module_name = script_file.stem
                spec = importlib.util.spec_from_file_location(module_name, script_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Look for automation functions
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    
                    # Check if it's a function with automation metadata
                    if (callable(attr) and 
                        hasattr(attr, '__automation_script__') and 
                        attr.__automation_script__):
                        
                        # Register the script
                        metadata = getattr(attr, '__automation_metadata__', {})
                        self.register_script(
                            name=metadata.get('name', attr_name),
                            script_func=attr,
                            category=metadata.get('category', 'discovered'),
                            description=metadata.get('description', ''),
                            parameters=metadata.get('parameters', {}),
                            schedule=metadata.get('schedule')
                        )
                        
            except Exception as e:
                logger.error(f"Failed to load script from {script_file}: {e}")

# Decorator for marking automation scripts
def automation_script(
    name: str = None,
    category: str = "general", 
    description: str = "",
    parameters: Dict[str, Any] = None,
    schedule: str = None
):
    """
    Decorator to mark a function as an automation script
    
    Args:
        name: Script name (defaults to function name)
        category: Script category
        description: Script description
        parameters: Expected parameters
        schedule: Default schedule
    """
    def decorator(func):
        func.__automation_script__ = True
        func.__automation_metadata__ = {
            'name': name or func.__name__,
            'category': category,
            'description': description,
            'parameters': parameters or {},
            'schedule': schedule
        }
        return func
    return decorator

# Built-in script templates
def create_default_templates(script_manager: ScriptManager):
    """Create default workflow templates"""
    
    # Lead enrichment template
    script_manager.create_template(
        name="lead_enrichment_workflow",
        description="Enrich lead data with external APIs",
        steps=[
            {
                'name': 'validate_email',
                'script': 'email_validation',
                'context': {'validation_level': 'strict'}
            },
            {
                'name': 'enrich_company',
                'script': 'company_enrichment',
                'context': {'include_social': True}
            },
            {
                'name': 'score_lead',
                'script': 'lead_scoring',
                'context': {'model': 'default'}
            }
        ],
        parameters={
            'lead_id': {'type': 'integer', 'required': True},
            'validation_level': {'type': 'string', 'default': 'strict'},
            'include_social': {'type': 'boolean', 'default': True}
        }
    )
    
    # Outreach template
    script_manager.create_template(
        name="email_outreach_workflow",
        description="Automated email outreach campaign",
        steps=[
            {
                'name': 'check_lead_status',
                'script': 'lead_status_check',
                'context': {}
            },
            {
                'name': 'personalize_email',
                'script': 'email_personalization',
                'context': {'template': 'default'}
            },
            {
                'name': 'send_email',
                'script': 'email_sender',
                'context': {'track_opens': True}
            },
            {
                'name': 'schedule_followup',
                'script': 'followup_scheduler',
                'context': {'delay_days': 3}
            }
        ],
        parameters={
            'lead_id': {'type': 'integer', 'required': True},
            'template': {'type': 'string', 'default': 'default'},
            'delay_days': {'type': 'integer', 'default': 3}
        }
    )
    
    # CRM sync template
    script_manager.create_template(
        name="crm_sync_workflow",
        description="Synchronize data with CRM systems",
        steps=[
            {
                'name': 'fetch_updates',
                'script': 'crm_data_fetch',
                'context': {'since_last_sync': True}
            },
            {
                'name': 'transform_data',
                'script': 'data_transformation',
                'context': {'format': 'standard'}
            },
            {
                'name': 'update_local',
                'script': 'local_data_update',
                'context': {'batch_size': 100}
            },
            {
                'name': 'push_changes',
                'script': 'crm_data_push',
                'context': {'conflict_resolution': 'merge'}
            }
        ],
        parameters={
            'crm_system': {'type': 'string', 'required': True},
            'batch_size': {'type': 'integer', 'default': 100},
            'conflict_resolution': {'type': 'string', 'default': 'merge'}
        }
    ) 