from pydantic import BaseModel, Field


class TaggedSymbol(BaseModel):
    symbol: str
    tags: list[str] = Field(default_factory=list)
