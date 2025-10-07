from .workflows.default.workflow import default_workflow

def call_workflow(user_query, workflow_name: str = "default", **kwargs):
    if workflow_name == "default":
        return default_workflow(user_query, **kwargs)
    else:
        raise Exception("Workflow not found")