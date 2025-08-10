from app.automation.compensation import compensator


@compensator("lead.create_record")
def undo_create_lead(context: dict) -> None:
    # Placeholder: call service to delete created lead if present
    _ = context.get("lead_id")
    # no-op
