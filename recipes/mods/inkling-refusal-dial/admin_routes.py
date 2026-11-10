# SPDX-License-Identifier: Apache-2.0
"""FastAPI admin routes for runtime refusal dial control."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from refusal_projection import InklingRefusalProjection

router = APIRouter(prefix="/admin", tags=["admin"])


class RefusalLambdaRequest(BaseModel):
    lambda_val: float

    class Config:
        fields = {"lambda_val": "lambda"}


@router.get("/refusal_lambda")
async def get_refusal_lambda():
    proj = InklingRefusalProjection.get_instance()
    return {"lambda": proj.get_lambda()}


@router.post("/refusal_lambda")
async def set_refusal_lambda(payload: dict):
    # Support both {"lambda": 1.0} and {"lambda_val": 1.0}
    val = payload.get("lambda")
    if val is None:
        val = payload.get("lambda_val")
    if val is None:
        raise HTTPException(status_code=400, detail="Missing 'lambda' parameter")

    try:
        fval = float(val)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid float for 'lambda'")

    proj = InklingRefusalProjection.get_instance()
    proj.set_lambda(fval)
    return {"status": "ok", "lambda": proj.get_lambda()}
