from pydantic import BaseModel

class StationInfo(BaseModel):
    st_id: int
    st_name: str
    lat: float
    lng: float
    st_status: str
    radius: float

