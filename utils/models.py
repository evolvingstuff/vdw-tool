from pydantic import BaseModel, Field, FilePath, field_validator, model_validator
from typing import List, Optional
from datetime import datetime
from enum import Enum
from pathlib import Path


class Category(BaseModel):
    cat_id: int
    name: str


class File(BaseModel):
    file_id: int
    filename: str
    filetype: str

class Attachment(BaseModel):
    att_id: int
    filename: str
    filetype: str


class Page(BaseModel):
    page_id: int
    page_name: str
    page_slug: str
    description: Optional[str] = None
    hits: int
    data_tiki: str
    data_md: Optional[str] = None
    created: int
    last_modified: int
    sections_included: List[int] = Field(default_factory=list)
    sections_excluded: List[int] = Field(default_factory=list)


class TikiFile(BaseModel):
    file_id: int
    filename: str
