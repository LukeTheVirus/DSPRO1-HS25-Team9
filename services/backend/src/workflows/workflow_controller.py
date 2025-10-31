from .default.workflow import default_workflow

from ..container import Container

async def call_workflow(container: Container, user_query, workflow_name: str = "default", **kwargs):
    if workflow_name == "default":
        return await default_workflow(container, user_query, **kwargs)
    else:
        raise Exception("Workflow not found")