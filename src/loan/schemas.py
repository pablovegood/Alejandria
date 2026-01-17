from pydantic import BaseModel, ConfigDict

class LoanRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str
    guten_id: int
    title: str = ""
    author: str = ""
