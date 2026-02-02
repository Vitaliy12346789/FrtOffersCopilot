"""
CRUD operations for FrtOffersCopilot database.
"""
from datetime import date
from typing import Optional, Sequence
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from .models_db import Offer, Clause, Charterer, Cargo


# ============================================================================
# OFFER CRUD
# ============================================================================

async def create_offer(
    db: AsyncSession,
    load_port: str,
    discharge_port: str,
    cargo: str,
    quantity: int,
    freight_rate: float,
    demurrage_rate: float,
    laycan_start: date,
    laycan_end: date,
    offer_text: str,
    summary: dict,
    charterer_id: Optional[str] = None,
    charterer_name: Optional[str] = None,
    or_sub: bool = False,
    quantity_tolerance: float = 5.0,
    user_id: Optional[str] = None,
    status: str = "draft"
) -> Offer:
    """Create a new offer in the database."""
    offer = Offer(
        load_port=load_port,
        discharge_port=discharge_port,
        cargo=cargo,
        quantity=quantity,
        quantity_tolerance=quantity_tolerance,
        freight_rate=freight_rate,
        demurrage_rate=demurrage_rate,
        laycan_start=laycan_start,
        laycan_end=laycan_end,
        charterer_id=charterer_id,
        charterer_name=charterer_name,
        or_sub=or_sub,
        offer_text=offer_text,
        summary=summary,
        status=status,
        user_id=user_id
    )
    db.add(offer)
    await db.flush()
    await db.refresh(offer)
    return offer


async def get_offer(db: AsyncSession, offer_id: int) -> Optional[Offer]:
    """Get an offer by ID."""
    result = await db.execute(select(Offer).where(Offer.id == offer_id))
    return result.scalar_one_or_none()


async def get_offers(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
    user_id: Optional[str] = None,
    status: Optional[str] = None
) -> Sequence[Offer]:
    """Get list of offers with optional filtering."""
    query = select(Offer).order_by(desc(Offer.created_at))

    if user_id:
        query = query.where(Offer.user_id == user_id)
    if status:
        query = query.where(Offer.status == status)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def update_offer(
    db: AsyncSession,
    offer_id: int,
    **kwargs
) -> Optional[Offer]:
    """Update an offer with given fields."""
    offer = await get_offer(db, offer_id)
    if not offer:
        return None

    for key, value in kwargs.items():
        if hasattr(offer, key):
            setattr(offer, key, value)

    await db.flush()
    await db.refresh(offer)
    return offer


async def delete_offer(db: AsyncSession, offer_id: int) -> bool:
    """Delete an offer by ID."""
    offer = await get_offer(db, offer_id)
    if not offer:
        return False

    await db.delete(offer)
    await db.flush()
    return True


async def count_offers(
    db: AsyncSession,
    user_id: Optional[str] = None,
    status: Optional[str] = None
) -> int:
    """Count offers with optional filtering."""
    from sqlalchemy import func

    query = select(func.count(Offer.id))

    if user_id:
        query = query.where(Offer.user_id == user_id)
    if status:
        query = query.where(Offer.status == status)

    result = await db.execute(query)
    return result.scalar() or 0


# ============================================================================
# CLAUSE CRUD
# ============================================================================

async def create_clause(
    db: AsyncSession,
    clause_id: str,
    title: str,
    text: str,
    category: str,
    subcategory: Optional[str] = None,
    is_mandatory: bool = False,
    requires_charterer_review: bool = False,
    conditions: Optional[dict] = None,
    sort_order: int = 0
) -> Clause:
    """Create a new clause in the Master Library."""
    clause = Clause(
        clause_id=clause_id,
        title=title,
        text=text,
        category=category,
        subcategory=subcategory,
        is_mandatory=is_mandatory,
        requires_charterer_review=requires_charterer_review,
        conditions=conditions,
        sort_order=sort_order
    )
    db.add(clause)
    await db.flush()
    await db.refresh(clause)
    return clause


async def get_clause_by_id(db: AsyncSession, clause_id: str) -> Optional[Clause]:
    """Get a clause by its clause_id (e.g., COUNTRY-UKR-001)."""
    result = await db.execute(select(Clause).where(Clause.clause_id == clause_id))
    return result.scalar_one_or_none()


async def get_clauses_by_category(
    db: AsyncSession,
    category: str,
    subcategory: Optional[str] = None
) -> Sequence[Clause]:
    """Get clauses by category and optional subcategory."""
    query = select(Clause).where(Clause.category == category)

    if subcategory:
        query = query.where(Clause.subcategory == subcategory)

    query = query.order_by(Clause.sort_order)
    result = await db.execute(query)
    return result.scalars().all()


async def get_all_clauses(db: AsyncSession) -> Sequence[Clause]:
    """Get all clauses from Master Library."""
    result = await db.execute(
        select(Clause).order_by(Clause.category, Clause.sort_order)
    )
    return result.scalars().all()


async def get_clauses_for_context(
    db: AsyncSession,
    port_type: Optional[str] = None,
    cargo_category: Optional[str] = None,
    discharge_country: Optional[str] = None
) -> Sequence[Clause]:
    """
    Get clauses matching the given context.
    Uses conditions JSON field for filtering.
    """
    # Get all clauses and filter by conditions in Python
    # (For production, consider using PostgreSQL JSONB operators)
    all_clauses = await get_all_clauses(db)

    matching = []
    for clause in all_clauses:
        conditions = clause.conditions or {}

        # Check if clause applies to this context
        matches = True

        if "port_type" in conditions:
            if port_type and conditions["port_type"].upper() != port_type.upper():
                matches = False

        if "cargo_category" in conditions:
            if cargo_category and conditions["cargo_category"].lower() != cargo_category.lower():
                matches = False

        if "discharge_country" in conditions:
            if discharge_country and conditions["discharge_country"].lower() != discharge_country.lower():
                matches = False

        if matches:
            matching.append(clause)

    return matching


# ============================================================================
# CHARTERER CRUD
# ============================================================================

async def create_charterer(
    db: AsyncSession,
    charterer_id: str,
    charterer_name: str,
    company_name: str,
    **kwargs
) -> Charterer:
    """Create a new charterer."""
    charterer = Charterer(
        charterer_id=charterer_id,
        charterer_name=charterer_name,
        company_name=company_name,
        **kwargs
    )
    db.add(charterer)
    await db.flush()
    await db.refresh(charterer)
    return charterer


async def get_charterer(db: AsyncSession, charterer_id: str) -> Optional[Charterer]:
    """Get a charterer by ID."""
    result = await db.execute(
        select(Charterer).where(Charterer.charterer_id == charterer_id)
    )
    return result.scalar_one_or_none()


async def get_all_charterers(
    db: AsyncSession,
    active_only: bool = True
) -> Sequence[Charterer]:
    """Get all charterers."""
    query = select(Charterer).order_by(Charterer.charterer_name)

    if active_only:
        query = query.where(Charterer.is_active == True)

    result = await db.execute(query)
    return result.scalars().all()


# ============================================================================
# CARGO CRUD
# ============================================================================

async def create_cargo(
    db: AsyncSession,
    cargo_id: str,
    name: str,
    category: str,
    stw_min: float,
    stw_max: float,
    stw_unit: str = "CF/T",
    notes: Optional[str] = None
) -> Cargo:
    """Create a new cargo type."""
    cargo = Cargo(
        cargo_id=cargo_id,
        name=name,
        category=category,
        stw_min=stw_min,
        stw_max=stw_max,
        stw_unit=stw_unit,
        notes=notes
    )
    db.add(cargo)
    await db.flush()
    await db.refresh(cargo)
    return cargo


async def get_cargo(db: AsyncSession, cargo_id: str) -> Optional[Cargo]:
    """Get a cargo by ID."""
    result = await db.execute(
        select(Cargo).where(Cargo.cargo_id == cargo_id)
    )
    return result.scalar_one_or_none()


async def get_all_cargoes(
    db: AsyncSession,
    active_only: bool = True
) -> Sequence[Cargo]:
    """Get all cargo types."""
    query = select(Cargo).order_by(Cargo.name)

    if active_only:
        query = query.where(Cargo.is_active == True)

    result = await db.execute(query)
    return result.scalars().all()
