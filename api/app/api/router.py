"""
Central API router that aggregates all feature-level routers.

Why a single aggregation point: This keeps main.py clean and lets
each feature register its own prefix/tags independently.  Adding a
new feature is a one-line import + include here.
"""

from fastapi import APIRouter

from app.features.historic_data.router import router as historic_data_router
from app.features.prediction.router import router as prediction_router

api_router = APIRouter()

api_router.include_router(
    historic_data_router,
    prefix="/historic-data",
    tags=["Historic Data"],
)

api_router.include_router(
    prediction_router,
    prefix="/prediction",
    tags=["Prediction"],
)
