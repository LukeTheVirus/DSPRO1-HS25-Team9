from .workflows.default.workflow import default_workflow

def call_workflow(data, workflow_name: str = "default", **kwargs):
    if workflow_name == "default":
        return default_workflow(data, **kwargs)
    else:
        raise Exception("Workflow not found")