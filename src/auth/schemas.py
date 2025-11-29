from pydantic import BaseModel, ConfigDict

class SignupReq(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str
    password: str


class LoginReq(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str
    password: str


class LogoutReq(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str
