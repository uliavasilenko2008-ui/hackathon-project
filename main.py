from contextlib import asynccontextmanager
from fastapi import FastAPI
from schemas import IncomingTicket, FinalResponse, build_response
from rules_model import get_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        get_model()   # модель обучается или грузится при старте, а не на первом запросе
    except Exception as e:
        print("Модель не загружена (проверьте папку data/):", e)
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/triage", response_model=FinalResponse)
def analyze(ticket: IncomingTicket):
    return build_response(ticket)