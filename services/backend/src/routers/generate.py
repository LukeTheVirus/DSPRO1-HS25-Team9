from typing import Annotated
from fastapi import APIRouter, Depends
from dependency_injector.wiring import inject, Provide
from ..workflow_controller import call_workflow
from ..container import Container

router = APIRouter()

@router.post("")
@inject
async def generate_response(
    query: str,
    workflow_name: str = "default",
    **kwargs
):
    """
    Generate a response using the specified workflow.
    
    Args:
        query: The user query to process
        workflow_name: The name of the workflow to use (default: "default")
        
    Returns:
        The generated response from the workflow
    """
    response = call_workflow(query, workflow_name=workflow_name, **kwargs)
    return {"query": query, "response": response}