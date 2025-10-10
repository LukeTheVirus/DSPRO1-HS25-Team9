from fastapi import APIRouter
from ...workflow_controller import call_workflow

class GenerateRouter(APIRouter):
    def __init__(self, container, **kwargs):
        super().__init__(**kwargs)
        self._container = container
        
        self.post("")(self.generate_response)

    async def generate_response(self, query: str, workflow_name: str = "default", **kwargs):
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