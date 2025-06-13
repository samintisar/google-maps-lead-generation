"""
Workflow Execution Domain Models.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ...db.core_models import Base


class Workflow(Base):
    """Simplified Workflow System - single table instead of separate workflow/step tables"""
    __tablename__ = "workflows"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # creator
    name = Column(String(255), nullable=False)
    description = Column(Text)
    trigger_type = Column(String(100))  # manual, automatic, scheduled
    trigger_conditions = Column(JSON)  # Conditions that trigger the workflow
    steps = Column(JSON)  # Array of workflow steps with their configurations
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="workflows")
    user = relationship("User", back_populates="workflows")


class WorkflowExecution(Base):
    """Track workflow execution instances"""
    __tablename__ = "workflow_executions"
    
    id = Column(String(255), primary_key=True)  # UUID
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=True)  # Made nullable for dynamic workflows
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(100), default="running")  # running, completed, failed, cancelled
    current_step = Column(String(255))
    progress_percentage = Column(Integer, default=0)
    execution_data = Column(JSON)  # Store execution-specific data
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    workflow = relationship("Workflow")
    organization = relationship("Organization")
    user = relationship("User")