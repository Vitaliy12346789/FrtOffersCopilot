import json
from pathlib import Path
from datetime import date
from typing import Optional

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent


def load_json(filename: str) -> dict:
    """Load JSON data from data/ or docs/ directory"""
    data_path = PROJECT_ROOT / "data" / filename
    docs_path = PROJECT_ROOT / "docs" / filename

    if data_path.exists():
        with open(data_path, "r", encoding="utf-8") as f:
            return json.load(f)
    elif docs_path.exists():
        with open(docs_path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        raise FileNotFoundError(f"File not found: {filename}")


def get_ports_data() -> dict:
    """Load ports data"""
    return load_json("ports.json")


def get_cargoes_data() -> dict:
    """Load cargo data"""
    return load_json("cargo_stw.json")


def get_charterers_data() -> dict:
    """Load charterers data"""
    return load_json("charterers.json")


def get_clauses_data() -> dict:
    """Load clauses data"""
    return load_json("clauses.json")


def get_master_library() -> dict:
    """Load Master Library with 45+ clauses"""
    backend_path = Path(__file__).parent / "master_library.json"
    if backend_path.exists():
        with open(backend_path, "r", encoding="utf-8") as f:
            return json.load(f)
    raise FileNotFoundError("master_library.json not found")


def find_load_port(ports_data: dict, port_name: str) -> Optional[dict]:
    """Find load port by name"""
    for port in ports_data["ports"]["load"]:
        if port["name"].lower() == port_name.lower():
            return port
    return None


def find_discharge_port(ports_data: dict, port_name: str) -> Optional[dict]:
    """Find discharge port by name"""
    for port in ports_data["ports"]["discharge"]:
        if port["name"].lower() == port_name.lower():
            return port
    return None


def find_cargo(cargoes_data: dict, cargo_name: str) -> Optional[dict]:
    """Find cargo by name"""
    for cargo in cargoes_data["cargoes"]:
        if cargo["name"].lower() == cargo_name.lower():
            return cargo
    return None


def find_charterer(charterers_data: dict, charterer_id: str) -> Optional[dict]:
    """Find charterer by ID"""
    for charterer in charterers_data["charterers"]:
        if charterer["charterer_id"] == charterer_id:
            return charterer
    return None


def get_port_type(port: dict) -> str:
    """Determine port type: Danube or POC"""
    region = port.get("region", "").upper()
    if region == "DANUBE":
        return "DANUBE"
    elif region == "POC":
        return "POC"
    return "UNKNOWN"


def format_quantity(quantity: int, tolerance: float = 5.0) -> str:
    """Format quantity with tolerance"""
    formatted = f"{quantity:,}".replace(",", ",")
    return f"{formatted} MTS (+/- {tolerance:.0f}% MOLCO)"


def format_cargo_description(cargo: dict, quantity: int, tolerance: float = 5.0) -> str:
    """Format cargo description line"""
    qty_str = format_quantity(quantity, tolerance)
    cargo_name = cargo["name"].upper()
    stw_min = cargo["stw_min"]
    stw_max = cargo["stw_max"]
    return f"{qty_str} OF {cargo_name} IN BULK STW ABT {stw_min}-{stw_max} WOG"


def format_laycan(start: date, end: date) -> str:
    """Format laycan dates"""
    start_day = start.day
    end_day = end.day
    month = start.strftime("%B").upper()
    year = start.year

    # Check if laycan spans year boundary (Nov-Dec)
    if start.month in [11, 12] and end.month == 1:
        return f"{start_day}-{end_day} {month} {year}/{year + 1}"

    return f"{start_day}-{end_day} {month} {year}"


def format_freight(rate: float) -> str:
    """Format freight rate"""
    return f"USD {rate:.2f} PMT FIOST"


def format_demurrage(rate: float, is_danube: bool = False) -> str:
    """Format demurrage rate"""
    formatted_rate = f"{rate:,.0f}".replace(",", ",")
    term = "DEMURRAGE/DETENTION" if is_danube else "DEMURRAGE"
    return f"{term}: USD {formatted_rate} PDPR FD BENDS (LESS BROKERAGE COMMISSION)"


def format_charterer_header(charterer: Optional[dict]) -> str:
    """Format charterer header section"""
    if not charterer:
        return "CHARTERERS: [CHARTERER NAME]\n[Full address and registration details]"

    # Get primary company
    primary = None
    for company in charterer.get("companies", []):
        if company.get("is_primary"):
            primary = company
            break

    if not primary and charterer.get("companies"):
        primary = charterer["companies"][0]

    if not primary:
        return f"CHARTERERS: {charterer['charterer_name']}"

    lines = [
        f"CHARTERERS: {primary['company_name']}",
        f"{primary['address']}",
        f"{primary['postal_code']} {primary['city']}, {primary['country']}",
        f"Reg. No: {primary['registration_number']} | VAT: {primary['vat']}"
    ]

    return "\n".join(lines)


def get_calendar_year(laycan_start: date) -> str:
    """Get calendar year(s) for holidays clause"""
    year = laycan_start.year
    month = laycan_start.month

    if month in [11, 12]:
        return f"{year}/{year + 1}"
    return str(year)


def generate_firm_offer(
    load_port: str,
    discharge_port: str,
    cargo: str,
    quantity: int,
    freight_rate: float,
    demurrage_rate: float,
    laycan_start: date,
    laycan_end: date,
    charterer_id: Optional[str] = None,
    or_sub: bool = False,
    quantity_tolerance: float = 5.0
) -> tuple[str, dict]:
    """
    Generate a firm offer text based on the provided parameters.

    Returns:
        tuple: (offer_text, summary_dict)
    """
    # Load data
    ports_data = get_ports_data()
    cargoes_data = get_cargoes_data()
    charterers_data = get_charterers_data()
    clauses_data = get_clauses_data()

    # Find entities
    load_port_data = find_load_port(ports_data, load_port)
    discharge_port_data = find_discharge_port(ports_data, discharge_port)
    cargo_data = find_cargo(cargoes_data, cargo)
    charterer_data = find_charterer(charterers_data, charterer_id) if charterer_id else None

    if not load_port_data:
        raise ValueError(f"Load port not found: {load_port}")
    if not discharge_port_data:
        raise ValueError(f"Discharge port not found: {discharge_port}")
    if not cargo_data:
        raise ValueError(f"Cargo not found: {cargo}")

    # Determine port type
    port_type = get_port_type(load_port_data)
    is_danube = port_type == "DANUBE"
    is_egypt = discharge_port_data["country"].lower() == "egypt"

    # Build offer sections
    sections = []
    clauses_count = 0

    # Header
    sections.append("FIRM OFFER")
    sections.append("")
    sections.append("=" * 43)
    sections.append(format_charterer_header(charterer_data))
    sections.append("=" * 43)
    sections.append("")

    # Main terms
    sections.append(f"LOAD PORT: 1 GSB(A) {load_port.upper()}, {load_port_data['country'].upper()}")
    sections.append("")
    sections.append(f"DISCHARGE PORT: 1 GSB(A) {discharge_port.upper()}, {discharge_port_data['country'].upper()}")
    sections.append("")
    sections.append(f"CARGO: {format_cargo_description(cargo_data, quantity, quantity_tolerance)}")
    sections.append("")
    sections.append(f"LAYCAN: {format_laycan(laycan_start, laycan_end)}")
    sections.append("")
    sections.append(f"FREIGHT: {format_freight(freight_rate)}")
    sections.append("")
    sections.append(format_demurrage(demurrage_rate, is_danube))
    sections.append("")

    # OR SUB clause if applicable
    if or_sub:
        sections.append("OR SUB: OWNERS SUBJECTS TO BE LIFTED WITHIN 24 HRS")
        sections.append("")

    # Ukraine port clauses
    sections.append("-" * 43)
    if is_danube:
        sections.append("UKRAINE - DANUBE PORT CLAUSES:")
    else:
        sections.append("UKRAINE - POC PORT CLAUSES:")
    sections.append("-" * 43)
    sections.append("")

    # Get port-specific clauses from ports.json
    for clause_id in load_port_data.get("clauses", []):
        clause = ports_data["clauses"].get(clause_id)
        if clause:
            sections.append(clause["text"])
            sections.append("")
            clauses_count += 1

    # Add berth restrictions for Danube
    if is_danube:
        sections.append("OWNRS SATSFY THEMSLVS WITH ANY KIND OF LOADING BERTH/PORT/CHANNEL/RIVER RESTRICTIONS")
        sections.append("")
        clauses_count += 1

    # NOR & Laytime section
    sections.append("-" * 43)
    sections.append("NOR & LAYTIME:")
    sections.append("-" * 43)
    sections.append("")

    # Ukraine NOR
    sections.append("AT LOAD PORT N.O.R. TO BE TENDERED ON WORKING DAYS DURING OFFICE HRS (08:00-17:00 HRS) FROM MONDAY TO FRIDAY")
    sections.append("")
    clauses_count += 1

    # Egypt NOR (if applicable)
    if is_egypt:
        sections.append("AT DISCHARGE PORT N.O.R. TO BE TENDERED ON WORKING DAYS DURING OFFICE HRS (08:00-12:00 HRS) FROM SUNDAY TO THURSDAY")
        sections.append("")
        clauses_count += 1

    # Laytime commencement
    sections.append("L/T TO COMMENCE 0800 HRS LT NEXT WORKING DAY AFTER VALID N.O.R. TENDERED, VSSL MOORED A.B.A.L.D.")
    sections.append("")
    clauses_count += 1

    # Holiday calendar
    calendar_year = get_calendar_year(laycan_start)
    sections.append(f"HOLIDAYS AS PER UKRAINE {calendar_year} CALENDAR")
    sections.append("")

    # Egypt discharge clauses
    if is_egypt:
        sections.append("-" * 43)
        sections.append("EGYPT - DISCHARGE CLAUSES:")
        sections.append("-" * 43)
        sections.append("")

        # Get Egypt-specific clauses from ports.json
        for clause_id in discharge_port_data.get("clauses", []):
            clause = ports_data["clauses"].get(clause_id)
            if clause and clause_id != "CLAUSE-EGY-NOR":  # NOR already added above
                sections.append(clause["text"])
                sections.append("")
                clauses_count += 1

        # Documents time for Egypt grain
        grain_clauses = cargoes_data.get("grain_clauses", {})
        if grain_clauses.get("documents_time"):
            sections.append(grain_clauses["documents_time"])
            sections.append("")
            clauses_count += 1

    # Cargo clauses (grain)
    if cargo_data.get("category") == "grain":
        sections.append("-" * 43)
        sections.append("CARGO CLAUSES (GRAIN):")
        sections.append("-" * 43)
        sections.append("")

        grain_clauses = cargoes_data.get("grain_clauses", {})

        if grain_clauses.get("previous_cargo"):
            sections.append(grain_clauses["previous_cargo"])
            sections.append("")
            clauses_count += 1

        if grain_clauses.get("trimming"):
            sections.append(grain_clauses["trimming"])
            sections.append("")
            clauses_count += 1

        if grain_clauses.get("surveyor"):
            sections.append(grain_clauses["surveyor"])
            sections.append("")
            clauses_count += 1

    # Standard clauses
    sections.append("-" * 43)
    sections.append("STANDARD CLAUSES:")
    sections.append("-" * 43)
    sections.append("")

    sections.append("GSB(A): GOOD SAFE BERTH ALWAYS AFLOAT")
    sections.append("")
    clauses_count += 1

    sections.append("DEMURRAGE PAYABLE WITHIN 30 DAYS UPON RECEIPT OF OWNRS SUPPORTING DOCUMENTS INCLUDING TIME SHEET AND INVOICES")
    sections.append("")
    clauses_count += 1

    sections.append("VSSL TO BE ISM/ISPS COMPLIANT WITH VALID CERTIFICATES")
    sections.append("")
    clauses_count += 1

    sections.append("ANY DISPUTE ARISING FROM THIS C/P TO BE REFERRED TO ARBITRATION IN LONDON ACCORDING TO ENGLISH LAW")
    sections.append("")
    clauses_count += 1

    # Proforma reference
    sections.append("-" * 43)
    sections.append("")
    sections.append("OWISE AS PER ATTACHED CHRTS PROFORMA CP, BASED ON SYNACOMEX 2000 C/P, LOGICALLY AMENDED AS PER MAIN TERMS AGREED (WHICH ALWAYS PREVAIL)")
    sections.append("")

    # Footer
    sections.append("-" * 43)
    sections.append("END OF FIRM OFFER")
    sections.append("-" * 43)

    # Build summary
    summary = {
        "route": f"{load_port} -> {discharge_port}",
        "cargo_description": format_cargo_description(cargo_data, quantity, quantity_tolerance),
        "total_freight": quantity * freight_rate,
        "clauses_count": clauses_count,
        "port_type": port_type
    }

    offer_text = "\n".join(sections)

    return offer_text, summary
