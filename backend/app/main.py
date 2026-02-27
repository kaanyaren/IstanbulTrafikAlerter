from fastapi import FastAPI

from app.routers import predictions

app = FastAPI(title="Istanbul Traffic Alerter API")

app.include_router(predictions.router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
