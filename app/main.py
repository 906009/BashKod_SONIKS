# -*- coding: utf-8 -*-

import asyncio
from contextlib import asynccontextmanager
from sys import prefix

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api import stations, online, rasp, history
import uvicorn


@asynccontextmanager
async def lifespan(app: FastAPI):
    cache_task = asyncio.create_task(cache_loop())
    cache_task_tle = asyncio.create_task(cache_tle_loop())
    cache_task_sat = asyncio.create_task(cache_loop_sat())
    cache_task_sat_info = asyncio.create_task(cache_loop_sat_info())
    yield
    cache_task.cancel()
    cache_task_tle.cancel()
    cache_task_sat.cancel()
    cache_task_sat_info.cancel()
    try:
        await cache_task
        await cache_task_sat
        await cache_task_sat_info
        await cache_task_tle
    except asyncio.CancelledError:
        print("Кэширование остановлено")


async def cache_loop():
    while True:
        try:
            await stations.cache()
        except Exception as e:
            print(e)
        await asyncio.sleep(300)


async def cache_loop_sat():
    while True:
        try:
            await online.cache_sat()
        except Exception as e:
            print(e)
        await asyncio.sleep(5)


async def cache_loop_sat_info():
    while True:
        try:
            await online.cache_sat_info()
        except Exception as e:
            print(e)
        await asyncio.sleep(300)


async def cache_tle_loop():
    while True:
        try:
            await online.cache()
        except Exception as e:
            print(e)
        await asyncio.sleep(86400)


app = FastAPI(title="WEB CCF", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(stations.router, prefix="/stations", tags=["Stations"])
app.include_router(online.router, prefix="/online", tags=["Online"])
app.include_router(rasp.router, prefix="/rasp", tags=["Rasp"])
app.include_router(history.router, prefix="/history", tags=["History"])

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
