from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    OfferRequest, OfferResponse, OfferSummary,
    PortInfo, CargoInfo, ChartererInfo,
    SaveOfferRequest, SavedOffer, OfferListItem, OfferListResponse, UpdateOfferRequest
)
from .generator import (
    generate_firm_offer,
    get_ports_data, get_cargoes_data, get_charterers_data
)
from .database import init_db, close_db, get_db
from . import crud


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup, cleanup on shutdown."""
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="FrtOffersCopilot API",
    description="API for generating maritime freight firm offers",
    version="2.0.0",
    lifespan=lifespan
)

# Get project root for static files
PROJECT_ROOT = Path(__file__).parent.parent


@app.get("/api/ports/load", response_model=List[PortInfo])
async def get_load_ports():
    """Get list of load ports for dropdown"""
    try:
        data = get_ports_data()
        ports = []
        for port in data["ports"]["load"]:
            ports.append(PortInfo(
                port_id=port["port_id"],
                name=port["name"],
                country=port["country"],
                region=port["region"],
                port_type=port["type"],
                max_draft=port["max_draft"]
            ))
        return ports
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ports/discharge", response_model=List[PortInfo])
async def get_discharge_ports():
    """Get list of discharge ports for dropdown"""
    try:
        data = get_ports_data()
        ports = []
        for port in data["ports"]["discharge"]:
            ports.append(PortInfo(
                port_id=port["port_id"],
                name=port["name"],
                country=port["country"],
                region=port["region"],
                port_type=port["type"],
                max_draft=port["max_draft"]
            ))
        return ports
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cargoes", response_model=List[CargoInfo])
async def get_cargoes():
    """Get list of cargoes for dropdown"""
    try:
        data = get_cargoes_data()
        cargoes = []
        for cargo in data["cargoes"]:
            cargoes.append(CargoInfo(
                cargo_id=cargo["cargo_id"],
                name=cargo["name"],
                stw_range=f"{cargo['stw_min']}-{cargo['stw_max']} {cargo['stw_unit']}"
            ))
        return cargoes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/charterers", response_model=List[ChartererInfo])
async def get_charterers():
    """Get list of charterers for dropdown"""
    try:
        data = get_charterers_data()
        charterers = []
        for charterer in data["charterers"]:
            # Get primary company
            primary = None
            for company in charterer.get("companies", []):
                if company.get("is_primary"):
                    primary = company
                    break
            if not primary and charterer.get("companies"):
                primary = charterer["companies"][0]

            charterers.append(ChartererInfo(
                charterer_id=charterer["charterer_id"],
                charterer_name=charterer["charterer_name"],
                company_name=primary["company_name"] if primary else charterer["charterer_name"],
                or_sub_default=primary.get("or_sub_default", False) if primary else False
            ))
        return charterers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate", response_model=OfferResponse)
async def generate_offer(request: OfferRequest):
    """Generate a firm offer based on the provided parameters"""
    try:
        offer_text, summary = generate_firm_offer(
            load_port=request.load_port,
            discharge_port=request.discharge_port,
            cargo=request.cargo,
            quantity=request.quantity,
            freight_rate=request.freight_rate,
            demurrage_rate=request.demurrage_rate,
            laycan_start=request.laycan_start,
            laycan_end=request.laycan_end,
            charterer_id=request.charterer_id,
            or_sub=request.or_sub,
            quantity_tolerance=request.quantity_tolerance
        )

        return OfferResponse(
            firm_offer_text=offer_text,
            summary=OfferSummary(
                route=summary["route"],
                cargo_description=summary["cargo_description"],
                total_freight=summary["total_freight"],
                clauses_count=summary["clauses_count"],
                port_type=summary["port_type"]
            )
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SAVED OFFERS ENDPOINTS
# ============================================================================

@app.post("/api/offers", response_model=SavedOffer)
async def save_offer(request: SaveOfferRequest, db: AsyncSession = Depends(get_db)):
    """Save a generated offer to the database"""
    try:
        offer = await crud.create_offer(
            db=db,
            load_port=request.load_port,
            discharge_port=request.discharge_port,
            cargo=request.cargo,
            quantity=request.quantity,
            freight_rate=request.freight_rate,
            demurrage_rate=request.demurrage_rate,
            laycan_start=request.laycan_start,
            laycan_end=request.laycan_end,
            offer_text=request.offer_text,
            summary=request.summary,
            charterer_id=request.charterer_id,
            charterer_name=request.charterer_name,
            or_sub=request.or_sub,
            quantity_tolerance=request.quantity_tolerance,
            status=request.status
        )
        return offer
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/offers", response_model=OfferListResponse)
async def list_offers(
    page: int = 1,
    per_page: int = 20,
    status: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Get list of saved offers with pagination"""
    try:
        skip = (page - 1) * per_page
        offers = await crud.get_offers(db, skip=skip, limit=per_page, status=status)
        total = await crud.count_offers(db, status=status)

        return OfferListResponse(
            offers=[OfferListItem.model_validate(o) for o in offers],
            total=total,
            page=page,
            per_page=per_page
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/offers/{offer_id}", response_model=SavedOffer)
async def get_offer(offer_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific offer by ID"""
    offer = await crud.get_offer(db, offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    return offer


@app.patch("/api/offers/{offer_id}", response_model=SavedOffer)
async def update_offer(
    offer_id: int,
    request: UpdateOfferRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing offer"""
    update_data = request.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    offer = await crud.update_offer(db, offer_id, **update_data)
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    return offer


@app.delete("/api/offers/{offer_id}")
async def delete_offer(offer_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an offer"""
    deleted = await crud.delete_offer(db, offer_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Offer not found")
    return {"message": "Offer deleted successfully"}


# Serve frontend static files
frontend_path = PROJECT_ROOT / "frontend"

@app.get("/")
async def serve_index():
    """Serve the main HTML page"""
    index_path = frontend_path / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Frontend not found")


@app.get("/{filename:path}")
async def serve_static(filename: str):
    """Serve static files (js, css)"""
    file_path = frontend_path / filename
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="File not found")
