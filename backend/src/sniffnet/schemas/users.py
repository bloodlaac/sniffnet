from pydantic import BaseModel, EmailStr, ConfigDict


class UserRequest(BaseModel):
    user_id: int
    username: str | None = None
    email: EmailStr | None = None

    model_config = ConfigDict(from_attributes=True)