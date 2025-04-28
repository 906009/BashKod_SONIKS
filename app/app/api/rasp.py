from fastapi import APIRouter, Query

import requests
from app.models.rasp import StationRasp, SatelliteRasp
from datetime import datetime, timezone, timedelta
from urllib.parse import quote

router = APIRouter()


@router.get("/")
async def get_rasp(
        st_id: int = Query(None),
        stl_id: int = Query(None)
):
    if (st_id is None and stl_id is None) or (st_id is not None and stl_id is not None):
        return "Необходим один аргумент."

    if stl_id is not None:
        return await get_satellite_rasp(stl_id)
    else:
        return await get_station_rasp(st_id)


async def get_station_rasp(st_id):
    # ?st_id=3
    now = datetime.now(timezone.utc)
    rounded = now.replace(hour=0, minute=0, second=0, microsecond=0)
    tom = rounded + timedelta(days=1)
    iso_date = tom.strftime("%Y-%m-%dT%H:%M:00.000000Z")
    encoded_date = quote(iso_date)
    # https://sonik.space/api/observations/?id=&status=future&ground_station=3&start=&end=2025-04-26T00%3A00%3A00.000000Z
    url = f"https://sonik.space/api/observations/?status=future&ground_station={st_id}&end={encoded_date}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            response = response.json()
            if response != []:
                output = []
                for obs in response:
                    try:
                        stl_name = obs["tle"]["tle0"]
                        tle1 = obs["tle"]["tle1"]
                        tle2 = obs["tle"]["tle2"]
                    except:
                        stl_name = ""
                        tle1 = ""
                        tle2 = ""
                    try:
                        norad_id = obs["norad_cat_id"]
                        start = obs["start"]
                        end = obs["end"]
                    except:
                        norad_id = ""
                        start = ""
                        end = ""
                    obj = StationRasp(
                        stl_name=stl_name,
                        norad_id=norad_id,
                        start=start,
                        end=end,
                        tle1=tle1,
                        tle2=tle2
                    )
                    output.append(obj)
                output.reverse()
                return output
    except:
        return ["Нет данных."]


async def get_satellite_rasp(stl_id):
    # ?stl_id=25544
    now = datetime.now(timezone.utc)
    rounded = now.replace(second=0, microsecond=0)
    tom = rounded + timedelta(minutes=10)
    iso_date = tom.strftime("%Y-%m-%dT%H:%M:00.000000Z")
    encoded_date = quote(iso_date)
    # https://sonik.space/api/observations/?status=future&ground_station=&start=2025-04-26T10%3A00%3A00.000000Z&end=&satellite__norad_cat_id=25544
    url = f"https://sonik.space/api/observations/?status=future&start={encoded_date}&satellite__norad_cat_id={stl_id}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            response = response.json()
            if response != []:
                output = []
                for obs in response:
                    try:
                        tle1 = obs["tle"]["tle1"]
                        tle2 = obs["tle"]["tle2"]
                        tle = f"{tle1}\n{tle2}"
                    except:
                        tle = ""
                    try:
                        id_obs = obs["id"]
                        start = obs["start"]
                        end = obs["end"]
                        st_name = obs['station_name']
                        st_id = obs['ground_station']
                    except:
                        id_obs = ""
                        start = ""
                        end = ""
                        st_name = ""
                        st_id = ""
                    obj = SatelliteRasp(
                        id_obs=id_obs,
                        st_name=st_name,
                        st_id=st_id,
                        start=start,
                        end=end,
                        tle=tle
                    )
                    output.append(obj)
                output.reverse()
                return output
    except:
        return ["Нет данных."]
