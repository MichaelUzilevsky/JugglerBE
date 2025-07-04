from typing import Optional

from pydantic import BaseModel


class BaseData(BaseModel):
    id: Optional[str] = None
