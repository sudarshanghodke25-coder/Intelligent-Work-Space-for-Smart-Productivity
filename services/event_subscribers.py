from services.event_bus import bus
from services.history_service import log_activity
# Assuming other services exist, import them here
# from services.calendar_service import add_event

def _on_task_created(payload):
    task_id = payload.get("task_id")
    user_id = payload.get("user_id")
    data = payload.get("data", {})
    
    log_activity(
        user_id=user_id,
        activity_type="Task Created",
        description=f"Created task: {data.get('title', 'Unknown')}",
        action_type="CREATE",
        entity_type="Task",
        entity_id=task_id,
        payload_json=data
    )
    # add_event(...) if Calendar integration was here

def _on_task_updated(payload):
    task_id = payload.get("task_id")
    user_id = payload.get("user_id")
    updates = payload.get("updates", {})
    
    log_activity(
        user_id=user_id,
        activity_type="Task Updated",
        description=f"Updated task #{task_id}",
        action_type="UPDATE",
        entity_type="Task",
        entity_id=task_id,
        payload_json=updates
    )

def _on_task_deleted(payload):
    task_id = payload.get("task_id")
    user_id = payload.get("user_id")
    
    log_activity(
        user_id=user_id,
        activity_type="Task Deleted",
        description=f"Deleted task #{task_id}",
        action_type="DELETE",
        entity_type="Task",
        entity_id=task_id
    )

def _on_task_completed(payload):
    task_id = payload.get("task_id")
    user_id = payload.get("user_id")
    
    log_activity(
        user_id=user_id,
        activity_type="Task Completed",
        description=f"Completed task #{task_id}",
        action_type="COMPLETE",
        entity_type="Task",
        entity_id=task_id
    )

def _on_subtask_added(payload):
    # Depending on how detailed history should be
    pass

def init_subscribers():
    """Register all decoupled event listeners."""
    bus.subscribe("TASK_CREATED", _on_task_created)
    bus.subscribe("TASK_UPDATED", _on_task_updated)
    bus.subscribe("TASK_DELETED", _on_task_deleted)
    bus.subscribe("TASK_COMPLETED", _on_task_completed)
    bus.subscribe("SUBTASK_ADDED", _on_subtask_added)
