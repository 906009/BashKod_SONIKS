from typing import Optional

from pydantic import BaseModel


class History(BaseModel):
    obs_id: int
    start: str
    end: str
    status: str
    payload: Optional[str]
    waterfall: Optional[str]
    tle1: str
    tle2: str