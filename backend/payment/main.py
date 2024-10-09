import os
import requests
import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.background import BackgroundTasks
from redis_om import HashModel
from redis_om import get_redis_connection
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List

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


# This is an event order
class Order(HashModel):
    event_id: str
    fees: float
    vat: float
    quantity: int
    status: str  # [pending, completed, refunded]

    class Meta:
        database = redis


class Purchase(BaseModel):
    event_id: str
    quantity: int


@app.post("/orders")
async def create(purchase: Purchase, background_task: BackgroundTasks):

    req = requests.get(f"http://127.0.0.1:8000/events/{purchase.event_id}")
    event = req.json()
    print(event)
    order = Order(
        event_id=purchase.event_id,
        fees=event.get("fees"),
        vat=5,
        quantity=purchase.quantity,
        status="pending",
    )

    order.save()

    # Executing the payment simulation in the background
    # without blocking the request
    background_task.add_task(order_completed, order)

    return order


def order_completed(order: Order):
    # Simulates payment processing
    time.sleep(10)
    order.status = "completed"
    order.save()


@app.get("/orders", response_model=List[Order])
async def get_orders():
    orders = [Order.get(pk) for pk in Order.all_pks()]
    return orders
