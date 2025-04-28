from fastapi import APIRouter
from app.models.station import StationInfo

import requests
import concurrent.futures
import math
from typing import List

cache_stations = None


async def cache():
    global cache_stations
    STATION_URL = "https://sonik.space/api/stations/?format=json&page="
    connections = 20

    def parser_stations():
        page = 0
        while True:
            response = requests.get(STATION_URL + str(page + 1))
            if response.status_code == 200:
                page += 10
            else:
                while True:
                    page -= 1
                    response = requests.get(STATION_URL + str(page + 1))
                    if response.status_code == 200:
                        break
                break
        page += 1
        urls = []
        for i in range(1, page + 1):
            urls.append(STATION_URL + str(i))

        def fetcher(url):
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    return response.json()
            except:
                return []

        def threads_fetcher(urls):
            with concurrent.futures.ThreadPoolExecutor(max_workers=connections) as executor:
                results = list(executor.map(fetcher, urls))
            return results

        fetched_data = threads_fetcher(urls)
        data = []
        for page_data in fetched_data:
            if page_data:
                data.extend(page_data)
        return data

    stations = parser_stations()
    if cache_stations != stations:
        output = []
        for station in stations:
            def calc_radius(altitude_km: float, min_horizon_deg: float) -> float:
                R_e = 6371
                h = altitude_km
                theta_rad = math.radians(min_horizon_deg)

                term1 = math.sqrt((R_e + h) ** 2 - (R_e * math.cos(theta_rad)) ** 2)
                term2 = R_e * math.sin(theta_rad)
                radius_km = term1 - term2

                return radius_km

            obj = StationInfo(
                st_id=station["id"],
                st_name=station["name"],
                lat=station["lat"],
                lng=station["lng"],
                st_status=station["status"],
                radius=calc_radius(station["altitude"], station["min_horizon"])
            )
            output.append(obj)
        cache_stations = output

router = APIRouter()


@router.get("", response_model=List[StationInfo])
async def get_station_status():
    if cache_stations:
        return cache_stations
