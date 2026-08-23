# api/main.py
from fastapi import FastAPI, Query
from typing import List
from . import crud, schemas

app = FastAPI(title="Kara Medical Analytical API")

@app.get("/api/reports/top-products", response_model=List[schemas.TopProduct])
def top_products(limit: int = 10):
    return crud.get_top_products(limit)

@app.get("/api/channels/{channel_name}/activity", response_model=List[schemas.ChannelActivity])
def channel_activity(channel_name: str):
    return crud.get_channel_activity(channel_name)

@app.get("/api/search/messages", response_model=List[schemas.SearchResult])
def search_messages(query: str = Query(..., min_length=2)):
    return crud.search_messages(query)
