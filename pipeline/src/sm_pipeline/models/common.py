from pydantic import BaseModel


class SourcePosition(BaseModel):
    page: int
    offset: int


class SourceSpan(BaseModel):
    source_file: str
    start: SourcePosition
    end: SourcePosition
