from fastapi import FastAPI, HTTPException

from .agent import AgentResult, BookingQueryAgent
from .config import settings
from .fx_client import FXClient
from .query_parser import (BookingQueryInterpreter, BookingQueryParser,
                           OpenAIQueryParser, RuleBasedQueryParser)
from .repositories import BookingRepository, TurneoBookingRepository
from .schemas import QueryRequest, QueryResponse
from .services import BookingService
from .turneo_client import TurneoClient

app = FastAPI(title="Turneo Booking Agent Demo")


def create_parser() -> BookingQueryParser:
    if settings.openai_api_key:
        return OpenAIQueryParser(
            api_key=settings.openai_api_key
        )
    return RuleBasedQueryParser()


llm_client = create_parser()
interpreter = BookingQueryInterpreter(llm_client)

turneo_client = TurneoClient()
booking_repo: BookingRepository = TurneoBookingRepository(turneo_client)

fx_client = FXClient()

booking_service = BookingService(repo=booking_repo, fx_client=fx_client)

agent = BookingQueryAgent(interpreter, booking_service)

from fastapi.responses import HTMLResponse


@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <html>
        <head>
            <title>Turneo Booking Query Demo</title>
            <style>
                body { font-family: Arial; max-width: 600px; margin: 40px auto; }
                input, textarea, button { font-size: 1rem; padding: 10px; width: 100%; margin-top: 10px; }
                button { background: black; color: white; border: none; cursor: pointer; }
                .result { margin-top: 20px; padding: 15px; border: 1px solid #ccc; }
            </style>
        </head>
        <body>
            <h2>Turneo Booking Agent</h2>

            <form onsubmit="submitQuery(event)">
                <textarea id="query" rows="3" placeholder='e.g. "Show me bookings in November 2024 in USD"'></textarea>
                <button type="submit">Submit</button>
            </form>

            <div id="output" class="result" style="display:none;"></div>

            <script>
                async function submitQuery(e) {
                    e.preventDefault();
                    const q = document.getElementById("query").value;
                    const res = await fetch("/query", {
                        method: "POST",
                        headers: {"Content-Type": "application/json"},
                        body: JSON.stringify({query: q})
                    });

                    const data = await res.json();
                    const box = document.getElementById("output");
                    box.style.display = "block";

                    if (!res.ok) {
                        box.innerHTML = "<b>Error:</b> " + data.detail;
                    } else {
                        box.innerHTML = "<b>" + data.message + "</b>";
                    }
                }
            </script>
        </body>
    </html>
    """


@app.post("/query", response_model=QueryResponse)
async def handle_query(body: QueryRequest):
    try:
        result: AgentResult = await agent.run(body.query)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return QueryResponse(
        message=result.message,
        total_value=result.total_value,
        currency=result.currency,
    )