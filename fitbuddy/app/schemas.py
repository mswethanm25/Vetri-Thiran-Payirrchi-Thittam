from pydantic import BaseModel, Field


class UserInput(BaseModel):
    user_id: int = Field(..., description="Unique user identifier")
    username: str = Field(..., min_length=1, max_length=100)
    age: int = Field(..., ge=1, le=120)
    weight: float = Field(..., gt=0)
    goal: str = Field(..., min_length=1)
    intensity: str = Field(..., min_length=1)


class WorkoutRequest(BaseModel):
    goal: str
    intensity: str


class FeedbackRequest(BaseModel):
    feedback: str = Field(..., min_length=1)