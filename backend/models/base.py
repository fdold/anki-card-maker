from pydantic import BaseModel, Field


class ModelInvocation(BaseModel):
    provider: str = Field(..., description="Central provider identifier.")
    model_name: str = Field(..., description="Configured model name.")
    purpose: str = Field(..., description="Why the model is being used.")

