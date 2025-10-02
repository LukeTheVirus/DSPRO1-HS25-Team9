from backend.workflow.default_workflow import default_workflow


def main(data, workflow_name: str = "default", **kwargs):
    if workflow_name == "default":
        return default_workflow(data, **kwargs)
    else:
        raise Exception("Workflow not found")