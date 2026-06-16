from pydantic import BaseModel, ConfigDict


class GlossaryTermCreate(BaseModel):
    source_term: str
    target_term: str
    note: str = ""
    keep_english: bool = False


class GlossaryTermUpdate(BaseModel):
    target_term: str | None = None
    note: str | None = None
    enabled: bool | None = None
    keep_english: bool | None = None


class GlossaryTermRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_term: str
    target_term: str
    note: str
    enabled: bool
    keep_english: bool
