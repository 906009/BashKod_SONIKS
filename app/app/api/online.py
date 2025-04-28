import asyncio
import json
import math
import os
from idlelib.rpc import response_queue
from typing import Optional
import time

from bs4 import BeautifulSoup
from fastapi import APIRouter, Query
import requests
from datetime import datetime, timezone, timedelta
from urllib.parse import quote
from skyfield.api import EarthSatellite, load, utc

tle_cache = {"1900-01-01": {"0": "0"}}
CACHE_FILE = "tle_cache.json"
cache_satellites_info = {}
cache_satellites = {}


async def cache_sat_info():
    global cache_satellites_info
    response = requests.get("https://sonik.space/api/satellites/?status=alive")
    cache_satellites_info = response.json()


async def cache_sat():
    global cache_satellites
    if not cache_satellites_info:
        await cache_sat_info()
    satellites = cache_satellites_info
    while satellites == {}:
        satellites = cache_satellites_info
        time.sleep(1)
    current_date = datetime.utcnow().strftime("%Y-%m-%d")
    norads = list(tle_cache[current_date].keys())
    geojson = {
        "type": "FeatureCollection",
        "features": []
    }

    loop = asyncio.get_running_loop()
    ts = load.timescale()
    t = ts.now()

    async def process_tle(i, tle):
        if not tle:
            return None
        norad = norads[i]
        name = "None"
        for satellite in satellites:
            if str(norad) == str(satellite["norad"]):
                if satellite['names']:
                    name = satellite['name'] + f" ({satellite['names']})"
                else:
                    name = satellite['name']

        line1 = tle[:tle.find("\r\n")]
        line2 = tle[tle.rfind("\r\n") + 4:]

        sat = await loop.run_in_executor(None, EarthSatellite, line1, line2, name, ts)
        geocentric = await loop.run_in_executor(None, sat.at, t)
        subpoint = geocentric.subpoint()
        coordinates = [f"{subpoint.latitude.degrees:.2f}", f"{subpoint.longitude.degrees:.2f}"]

        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": coordinates
            },
            "properties": {
                "norad_id": norad,
                "name": name
            }
        }
        return feature

    tasks = [process_tle(i, tle) for i, tle in enumerate(tle_cache.get(current_date, {}).values())]
    features = await asyncio.gather(*tasks)

    geojson["features"] = [feature for feature in features if feature]
    cache_satellites = geojson


async def cache():
    global tle_cache

    def today():
        return datetime.utcnow().strftime("%Y-%m-%d")

    def load_cache():
        if not os.path.exists(CACHE_FILE):
            return {}

        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            full_cache = json.load(f)

        return full_cache

    def save_cache(tle_data):
        full_cache = {}
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                full_cache = json.load(f)

        full_cache[today()] = tle_data

        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(full_cache, f, ensure_ascii=False, indent=2)

    def get_tle(norad, cached_tle):
        if str(norad) in cached_tle:
            return cached_tle[str(norad)]

        url = f"https://www.n2yo.com/satellite/?s={norad}#results"
        try:
            html = requests.get(url).text
            soup = BeautifulSoup(html, "html.parser")
            tle_element = soup.find(id="tle")
            if tle_element:
                tle = tle_element.get_text(strip=True)
                if "Source" in tle:
                    tle = tle[:tle.find("Source")]
                cached_tle[str(norad)] = tle
                return tle
        except:
            pass
        return None

    tle_cache = load_cache()
    if today() in list(tle_cache.keys())[0]:
        pass
    else:
        updated_tle = tle_cache.copy()

        response = requests.get("https://sonik.space/api/satellites/?status=alive")
        satellites = response.json()
        for sat in satellites:
            norad = sat.get("norad")
            if not norad:
                continue

            tle = get_tle(norad, updated_tle)

            time.sleep(1)

        save_cache(updated_tle)


router = APIRouter()


@router.get("/")
async def get_station_rasp_and_satellite_online(st_id: Optional[int] = Query(None)):
    # ?st_id=3
    if st_id is None:
        return cache_satellites
    now = datetime.now(timezone.utc)
    adjusted = now - timedelta(minutes=10)
    rounded = adjusted.replace(second=0, microsecond=0)
    iso_date = rounded.strftime("%Y-%m-%dT%H:%M:00.000000Z")
    encoded_date = quote(iso_date)
    # https://sonik.space/api/observations/?status=unknown&ground_station=3&start=2025-04-25T15%3A20%3A00.000000Z
    url = f"https://sonik.space/api/observations/?status=unknown&ground_station={st_id}&start={encoded_date}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            response = response.json()
            if response != []:
                try:
                    name = response[0]["tle"]["tle0"]
                except:
                    name = ""
                return "Приём", name
            else:
                return ["Ожидание"]
    except:
        return ["Ошибка"]
