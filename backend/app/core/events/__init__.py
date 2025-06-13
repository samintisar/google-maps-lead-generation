"""
Event System - Placeholder.
"""

# TODO: Implement event system for domain events
# This would handle events like:
# - LeadCreated
# - CampaignStarted
# - WorkflowCompleted
# - etc.

class EventBus:
    """Simple event bus implementation - placeholder."""
    
    def __init__(self):
        self.handlers = {}
    
    def subscribe(self, event_type: str, handler):
        """Subscribe to an event type."""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
    
    def publish(self, event_type: str, data: dict):
        """Publish an event."""
        if event_type in self.handlers:
            for handler in self.handlers[event_type]:
                handler(data)


# Global event bus instance
event_bus = EventBus()

__all__ = ["EventBus", "event_bus"]