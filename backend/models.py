from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime


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


# ============================================================================
# SAVED OFFER MODELS
# ============================================================================

class SaveOfferRequest(BaseModel):
    """Request to save a generated offer"""
    load_port: str
    discharge_port: str
    cargo: str
    quantity: int
    freight_rate: float
    demurrage_rate: float
    laycan_start: date
    laycan_end: date
    charterer_id: Optional[str] = None
    charterer_name: Optional[str] = None
    or_sub: bool = False
    quantity_tolerance: float = 5.0
    offer_text: str
    summary: dict
    status: str = "draft"


class SavedOffer(BaseModel):
    """Saved offer with all details"""
    id: int
    load_port: str
    discharge_port: str
    cargo: str
    quantity: int
    quantity_tolerance: float
    freight_rate: float
    demurrage_rate: float
    laycan_start: date
    laycan_end: date
    charterer_id: Optional[str] = None
    charterer_name: Optional[str] = None
    or_sub: bool
    offer_text: str
    summary: Optional[dict] = None
    status: str
    version: int
    version_type: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OfferListItem(BaseModel):
    """Brief offer info for list display"""
    id: int
    load_port: str
    discharge_port: str
    cargo: str
    quantity: int
    freight_rate: float
    laycan_start: date
    laycan_end: date
    charterer_name: Optional[str] = None
    status: str
    version_type: str
    created_at: datetime

    class Config:
        from_attributes = True


class OfferListResponse(BaseModel):
    """Response with list of offers and pagination info"""
    offers: List[OfferListItem]
    total: int
    page: int
    per_page: int


class UpdateOfferRequest(BaseModel):
    """Request to update an existing offer"""
    offer_text: Optional[str] = None
    status: Optional[str] = None
