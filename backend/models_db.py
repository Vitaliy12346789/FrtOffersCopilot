"""
SQLAlchemy database models for FrtOffersCopilot.
"""
from datetime import datetime, date
from typing import Optional
from sqlalchemy import String, Text, Integer, Float, Boolean, Date, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Offer(Base):
    """
    Saved firm offers with all parameters and generated text.
    """
    __tablename__ = "offers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Core offer parameters
    load_port: Mapped[str] = mapped_column(String(100), nullable=False)
    discharge_port: Mapped[str] = mapped_column(String(100), nullable=False)
    cargo: Mapped[str] = mapped_column(String(100), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_tolerance: Mapped[float] = mapped_column(Float, default=5.0)
    freight_rate: Mapped[float] = mapped_column(Float, nullable=False)
    demurrage_rate: Mapped[float] = mapped_column(Float, nullable=False)
    laycan_start: Mapped[date] = mapped_column(Date, nullable=False)
    laycan_end: Mapped[date] = mapped_column(Date, nullable=False)

    # Optional fields
    charterer_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    charterer_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    or_sub: Mapped[bool] = mapped_column(Boolean, default=False)

    # Generated content
    offer_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Summary data (stored as JSON for flexibility)
    summary: Mapped[dict] = mapped_column(JSON, nullable=True)

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20),
        default="draft",
        comment="Status: draft, sent, accepted, rejected, expired"
    )

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # User identifier (for future multi-user support)
    user_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Version for counter workflow (FO=1, OC1=2, CC1=3, etc.)
    version: Mapped[int] = mapped_column(Integer, default=1)
    version_type: Mapped[str] = mapped_column(
        String(10),
        default="FO",
        comment="Version type: FO, OC1, CC1, OC2, CC2, etc."
    )
    parent_offer_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("offers.id"),
        nullable=True,
        comment="Parent offer for counter workflow"
    )

    # Relationships for counter chain
    counters: Mapped[list["Offer"]] = relationship(
        "Offer",
        backref="parent_offer",
        remote_side=[id],
        foreign_keys=[parent_offer_id]
    )

    def __repr__(self) -> str:
        return f"<Offer {self.id}: {self.load_port} -> {self.discharge_port}, {self.cargo}>"


class Clause(Base):
    """
    Master Library of contract clauses.
    45+ reusable clauses organized by category.
    """
    __tablename__ = "clauses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Clause identification
    clause_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        comment="Unique clause ID like COUNTRY-UKR-001"
    )

    # Content
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    # Categorization
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Category: COUNTRY, PORT, CARGO, OPERATION, LEGAL, FREIGHT"
    )
    subcategory: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Subcategory like Ukraine-Danube, Egypt, Grain"
    )

    # Usage flags
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_charterer_review: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Flag CHRTR REVIEW - needs charterer approval"
    )

    # Applicability conditions (stored as JSON)
    conditions: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Conditions for auto-selection: {port_type: 'DANUBE', cargo: 'grain'}"
    )

    # Ordering
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<Clause {self.clause_id}: {self.title}>"


class Charterer(Base):
    """
    Charterer database with company details and preferences.
    """
    __tablename__ = "charterers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Identification
    charterer_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        comment="Unique charterer ID like CHTR-001"
    )
    charterer_name: Mapped[str] = mapped_column(String(200), nullable=False)

    # Primary company details
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    registration_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    vat: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Contact
    email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Preferences
    or_sub_default: Mapped[bool] = mapped_column(Boolean, default=False)
    preferred_clauses: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True,
        comment="List of preferred clause IDs for this charterer"
    )

    # Proforma template reference
    proforma_template_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<Charterer {self.charterer_id}: {self.charterer_name}>"


class Cargo(Base):
    """
    Cargo types with STW (Stowage Factor) specifications.
    """
    __tablename__ = "cargoes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Identification
    cargo_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        comment="Unique cargo ID like CARGO-001"
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Category
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Category: grain, steel, fertilizer, etc."
    )

    # STW specifications
    stw_min: Mapped[float] = mapped_column(Float, nullable=False)
    stw_max: Mapped[float] = mapped_column(Float, nullable=False)
    stw_unit: Mapped[str] = mapped_column(String(20), default="CF/T")

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Important notes like 'STW varies by moisture'"
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Cargo {self.cargo_id}: {self.name}>"
