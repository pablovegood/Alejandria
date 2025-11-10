from pydantic import BaseModel, ConfigDict

class BookDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    guten_id: int
    title: str
    author: str
    language: str | None = None
    has_text: bool | None = None
    text_url: str | None = None
    downloaded_at: str | None = None
