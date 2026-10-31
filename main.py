from fastapi import FastAPI
from schemas import IncomingTicket, FinalResponse, build_response

app = FastAPI()


@app.post("/triage", response_model=FinalResponse)
def analyze(ticket: IncomingTicket):
    return build_response(ticket)
