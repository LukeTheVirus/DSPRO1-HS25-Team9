from fastapi import APIRouter, Body

from ...workflows.workflow_controller import call_workflow


class GenerateRouter(APIRouter):
    def __init__(self, container, **kwargs):
        super().__init__(**kwargs)
        self._container = container

        self.post("")(self.generate_response)

    async def generate_response(self, query: str = Body(...), workflow_name: str = Body("default"), config: dict | None = Body(default=None)):
        """
        Generate a response using the specified workflow.
        
        Args:
            query: The user query to process
            workflow_name: The name of the workflow to use (default: "default")
            
        Returns:
            The generated response from the workflow
        """
        workflow_kwargs = {}
        if config is not None:
            workflow_kwargs["config"] = config

        response = call_workflow(query, workflow_name=workflow_name, **workflow_kwargs)
        return {"query": query, "response": response}
