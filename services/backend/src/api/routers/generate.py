from fastapi import APIRouter
# Import Pydantic's BaseModel
from pydantic import BaseModel

# Import the container type for type hinting
from ...container import Container
from ...workflows.workflow_controller import call_workflow


# 1. Define the shape of the request body
class GenerateRequest(BaseModel):
    query: str
    workflow_name: str = "default"
    # We can add other optional fields here later if needed


class GenerateRouter(APIRouter):
    def __init__(self, container, **kwargs):
        super().__init__(**kwargs)
        self._container: Container = container

        self.post("")(self.generate_response)

    # 2. Change the signature to accept the Pydantic model
    async def generate_response(self, request: GenerateRequest):
        """
        Generate a response using the specified workflow.
        
        Args:
            request: A GenerateRequest object containing the query.
            
        Returns:
            The generated response from the workflow
        """
        # 3. Access data from the validated request object
        response = await call_workflow(
            self._container, 
            request.query, 
            workflow_name=request.workflow_name
        )
        return response