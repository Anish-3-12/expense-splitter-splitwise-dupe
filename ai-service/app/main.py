from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.logging import logger
from app.api import health, receipts, splits, categories, analytics

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Splitwise AI Microservice started successfully.")
    yield
    logger.info("Splitwise AI Microservice shutting down.")

app = FastAPI(
    title="Splitwise AI Microservice",
    description="Intelligent financial processing microservice: receipt OCR, natural language splitting, categorization, and anomaly detection.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration - allow internal calls
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(health.router)
app.include_router(receipts.router)
app.include_router(splits.router)
app.include_router(categories.router)
app.include_router(analytics.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
