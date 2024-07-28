from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from redis_om import HashModel
import os
from redis_om import get_redis_connection
from dotenv import load_dotenv


app = FastAPI()

origins = ["http://localhost", "http://localhost:8000", "http://example.com"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


load_dotenv()


redis = get_redis_connection(
    host=os.getenv("REDIS_URL"),
    port=os.getenv("REDIS_PORT"),
    password=os.getenv("REDIS_PASSWORD"),
)


class Event(HashModel):
    name: str
    desc: str
    capacity: int
    fees: float

    class Meta:
        database = redis


# Helper fun
def format_event(pk: str):
    event = Event.get(pk)

    return {
        "id": event.pk,
        "name": event.name,
        "desc": event.desc,
        "capacity": event.capacity,
        "fees": event.fees,
    }


# Endpoints


@app.get("/events")
async def get_events():

    return [format_event(pk) for pk in Event.all_pks()]


@app.get("/events/{pk}")
async def get_single_event(pk: str):

    print("I am triggered")

    return Event.get(pk)


@app.post("/create_event")
async def create_event(event: Event):

    return event.save()


# @app.delete("/delete_event/{pk}")
# async def delete_event(pk: str):

#     Event.delete(pk)


@app.delete("/delete_event/{event_id}", status_code=204)
async def delete_event(event_id: str):
    try:
        event = Event.get(event_id)
        if event:
            Event.delete(event_id)
        else:
            raise HTTPException(status_code=404, detail="Event not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
