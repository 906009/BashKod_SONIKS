from fastapi import APIRouter, Query

import requests
from app.models.history import History
from datetime import datetime, timezone, timedelta
from urllib.parse import quote

router = APIRouter()


@router.get("/")
async def get_history(
        st_id: int = Query(None),
        stl_id: int = Query(None)
):
    if (st_id is None and stl_id is None) or (st_id is not None and stl_id is not None):
        return "Необходим один аргумент."

    if stl_id is not None:
        return await get_satellite_history(stl_id)
    else:
        return await get_station_history(st_id)

async def get_station_history(st_id):
    # ?st_id=3
    now = datetime.now(timezone.utc)
    rounded = now.replace(second=0, microsecond=0)
    time = rounded - timedelta(minutes=10)
    iso_date = time.strftime("%Y-%m-%dT%H:%M:00.000000Z")
    encoded_date = quote(iso_date)
    # https://sonik.space/api/observations/?id=&status=future&ground_station=3&start=&end=2025-04-26T00%3A00%3A00.000000Z
    url = f"https://sonik.space/api/observations/?ground_station={st_id}&end={encoded_date}"
    response = requests.get(url)
    try:
        if response.status_code == 200:
            if response.json() != []:
                output = []
                for obs in response.json():
                    obj = History(
                        obs_id=obs['id'],
                        start=obs['start'],
                        end=obs['end'],
                        status=obs['status'],
                        payload=obs['payload'],
                        waterfall=obs['waterfall'],
                        tle1=obs['tle']['tle1'],
                        tle2=obs['tle']['tle2']
                    )
                    output.append(obj)
                return output
    except:
        return ["Ошибка"]

async def get_satellite_history(stl_id):
    # ?stl_id=3
    now = datetime.now(timezone.utc)
    rounded = now.replace(second=0, microsecond=0)
    time = rounded - timedelta(minutes=10)
    iso_date = time.strftime("%Y-%m-%dT%H:%M:00.000000Z")
    encoded_date = quote(iso_date)
    # https://sonik.space/api/observations/?id=&status=future&ground_station=3&start=&end=2025-04-26T00%3A00%3A00.000000Z
    url = f"https://sonik.space/api/observations/?&satellite__norad_cat_id={stl_id}&end={encoded_date}"
    response = requests.get(url)
    try:
        if response.status_code == 200:
            if response.json() != []:
                output = []
                for obs in response.json():
                    obj = History(
                        obs_id=obs['id'],
                        start=obs['start'],
                        end=obs['end'],
                        status=obs['status'],
                        payload=obs['payload'],
                        waterfall=obs['waterfall'],
                        tle1=obs['tle']['tle1'],
                        tle2=obs['tle']['tle2']
                    )
                    output.append(obj)
                return output
    except:
        return ["Ошибка"]

