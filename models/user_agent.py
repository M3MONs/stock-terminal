from pydantic import BaseModel


class UserAgent(BaseModel):
    id: int | None = None
    name: str
    file_path: str
    enabled: bool = True
