"""
Domain Classification Matrix endpoint.
Returns the full matrix with weights, colors, descriptions and cross-domain scores.
"""
from fastapi import APIRouter
from app.ml.training_data import get_domain_matrix

router = APIRouter(prefix="/domain-matrix", tags=["domain-matrix"])


@router.get("")
async def domain_classification_matrix():
    """
    Return the full domain classification matrix.
    Used by the frontend to render the matrix visualisation.
    """
    return get_domain_matrix()


@router.get("/domains")
async def list_domains():
    """Quick endpoint — just domain names and their colors/descriptions."""
    matrix = get_domain_matrix()
    return [
        {
            "domain": d,
            "color": matrix["color_map"][d],
            "description": matrix["description"][d],
        }
        for d in matrix["domains"]
    ]
