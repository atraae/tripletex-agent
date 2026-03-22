import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.agent import TripletexAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Tripletex AI Accounting Agent")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/solve")
async def solve(request: Request):
    try:
        body = await request.json()
        prompt: str = body.get("prompt", "")
        credentials: dict = body.get("tripletex_credentials", {})
        files: list = body.get("files", [])

        logger.info(f"Received task: {prompt[:200]}")

        agent = TripletexAgent(credentials=credentials)
        result = await agent.solve(prompt=prompt, files=files)

        logger.info(f"Task completed: {result}")
        return JSONResponse({"status": "completed", "details": result})

    except Exception as e:
        logger.error(f"Error solving task: {e}", exc_info=True)
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=500
        )
