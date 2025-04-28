from pydantic import BaseModel


class StationRasp(BaseModel):
    stl_name: str
    norad_id: int
    start: str
    end: str
    tle1: str
    tle2: str

class SatelliteRasp(BaseModel):
    id_obs: int
    st_name: str
    st_id: int
    start: str
    end: str
    tle: str

