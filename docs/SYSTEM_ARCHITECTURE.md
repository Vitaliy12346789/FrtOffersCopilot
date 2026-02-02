# SYSTEM ARCHITECTURE - Clause Selection Logic

## Port Classification

### Ukraine Danube Ports
- Reni
- Izmail  
- Orlivka
- Kilia

**Auto-include:**
- Sulina/Bystroe clause
- Air raid alerts clause
- Demurrage/Detention combined

### Ukraine POC Ports  
- Pivdennyi (Yuzhny)
- Odesa
- Chornomorsk

**Auto-include:**
- JCC inspection clause
- ERWI war insurance clause
- Cancellation option (corridor closure)
- Air raid alerts clause

### Egypt Discharge Ports
- Alexandria
- Damietta
- Port Said
- Dekheila

**Auto-include:**
- Sampling procedure clause
- NOR hours: Sun-Thu 08:00-12:00
- SHINC/FHINC time counting
- Friday holiday counting

## Decision Logic

```
IF load_port IN [Reni, Izmail, Orlivka, Kilia]:
    port_type = "DANUBE"
    include: COUNTRY-UKR-001 (Sulina)
    include: VAR-EX-001 (Air raids)
    demurrage = "DEMURRAGE/DETENTION"

ELIF load_port IN [Pivdennyi, Odesa, Chornomorsk]:
    port_type = "POC"
    include: COUNTRY-UKR-002 (JCC/ERWI)
    include: COUNTRY-UKR-003 (Cancellation)
    include: VAR-EX-001 (Air raids)
    demurrage = "DEMURRAGE"

IF discharge_port IN Egypt:
    include: COUNTRY-EGY-001 (Sampling)
    NOR_hours = "08:00-12:00 Sun-Thu"
    time_counting = "SHINC/FHINC"

IF cargo IN [Corn, Wheat, Barley, Soybeans, ...]:
    include: CARGO-GRAIN-003 (Previous cargo)
    include: CARGO-GRAIN-004 (Trimming)
    include: CARGO-GRAIN-005 (Surveyor)
    IF discharge_egypt:
        include: CARGO-GRAIN-006 (Documents EIU)
```

## NOR Hours Logic

| Load Port | Discharge Port | Load NOR | Discharge NOR |
|-----------|----------------|----------|---------------|
| Ukraine | Egypt | 08:00-17:00 Mon-Fri | 08:00-12:00 Sun-Thu |
| Ukraine | Europe | 08:00-17:00 Mon-Fri | 08:00-17:00 Mon-Fri |

## Laycan Calendar Logic

```
IF laycan_month IN [Nov, Dec]:
    calendar = "{YEAR}/{YEAR+1}"
ELSE:
    calendar = "{YEAR}"
```

Example:
- Laycan 15-20 Dec 2025 → "HOLIDAYS AS PER UKRAINE 2025/2026 CALENDAR"
- Laycan 10-15 Mar 2025 → "HOLIDAYS AS PER UKRAINE 2025 CALENDAR"
