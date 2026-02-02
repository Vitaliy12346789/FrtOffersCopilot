from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class OfferRequest(BaseModel):
    """Request model for generating a firm offer"""
    load_port: str = Field(..., description="Load port name (e.g., 'Reni', 'Odesa')")
    discharge_port: str = Field(..., description="Discharge port name (e.g., 'Alexandria')")
    cargo: str = Field(..., description="Cargo type (e.g., 'Corn', 'Wheat')")
    quantity: int = Field(..., ge=1000, description="Quantity in metric tons")
    freight_rate: float = Field(..., gt=0, description="Freight rate in USD per metric ton")
    demurrage_rate: float = Field(..., gt=0, description="Demurrage rate in USD per day")
    laycan_start: date = Field(..., description="Laycan start date")
    laycan_end: date = Field(..., description="Laycan end date")
    charterer_id: Optional[str] = Field(None, description="Charterer ID (optional)")
    or_sub: bool = Field(False, description="Include OR SUB clause")
    quantity_tolerance: float = Field(5.0, ge=0, le=10, description="Quantity tolerance percentage")


class OfferSummary(BaseModel):
    """Summary information about the generated offer"""
    route: str
    cargo_description: str
    total_freight: float
    clauses_count: int
    port_type: str


class OfferResponse(BaseModel):
    """Response model with generated firm offer"""
    firm_offer_text: str
    summary: OfferSummary


class PortInfo(BaseModel):
    """Port information for dropdowns"""
    port_id: str
    name: str
    country: str
    region: str
    port_type: str
    max_draft: float


class CargoInfo(BaseModel):
    """Cargo information for dropdowns"""
    cargo_id: str
    name: str
    stw_range: str


class ChartererInfo(BaseModel):
    """Charterer information for dropdowns"""
    charterer_id: str
    charterer_name: str
    company_name: str
    or_sub_default: bool
