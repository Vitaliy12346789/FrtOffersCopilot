# 📊 CHARTERER DATABASE STRUCTURE
**Version:** 1.0  
**Last Updated:** 15.01.2026  
**Project:** CRM Freight Brokering - Firm Offer Automation

═══════════════════════════════════════════════════════
OVERVIEW
═══════════════════════════════════════════════════════

This database stores information about charterers (clients) including:
- Company legal details
- Multiple company entities per charterer group
- Standard commission structures
- OR SUB preferences
- Contact preferences

PURPOSE:
- Auto-fill charterer details in firm offers
- Standardize commission rates
- Track client preferences
- Enable quick offer generation

═══════════════════════════════════════════════════════
JSON DATA STRUCTURE
═══════════════════════════════════════════════════════

```json
{
  "charterers": [
    {
      "charterer_id": "CHTR-001",
      "charterer_name": "Ardi Group",
      "companies": [
        {
          "company_id": "CHTR-001-A",
          "company_name": "ARDI GROUP TRADING LTD",
          "country": "Bulgaria",
          "city": "Burgas",
          "postal_code": "8000",
          "address": "2, Ivailo Str.",
          "registration_number": "206814919",
          "vat": "BG206814919",
          "or_sub_default": true,
          "is_primary": true
        }
      ],
      "standard_commission": {
        "format": "split",
        "total_pct": 2.5,
        "breakdown": [
          {"party": "Address Commission", "pct": 1.25},
          {"party": "Navistar", "pct": 1.25}
        ]
      },
      "notes": "Typical routes: Ukraine-Egypt grain"
    }
  ]
}
```

═══════════════════════════════════════════════════════
FULL STYLE OUTPUT FORMAT
═══════════════════════════════════════════════════════

```
CHARTERERS:
{company_name} {OR_SUB_FLAG}
{country}
{city}, {postal_code}
{address}
Company registration №{registration_number}
VAT:{vat_number}
```

Example:
```
CHARTERERS:
ARDI GROUP TRADING LTD OR SUB
BULGARIA
Burgas, 8000
2, Ivailo Str.
Company registration №206814919
VAT:BG206814919
```

═══════════════════════════════════════════════════════
COMMISSION OUTPUT FORMAT
═══════════════════════════════════════════════════════

Split Commission:
```
COMMISSION: 2.5% TOTAL BROKERAGE CONSISTING OF:
- 1.25% TO ADDRESS COMMISSION
- 1.25% TO NAVISTAR
```

Total Commission:
```
COMMISSION: 3.0% TOTAL BROKERAGE TO NAVISTAR
```

═══════════════════════════════════════════════════════
VALIDATION RULES
═══════════════════════════════════════════════════════

Commission Structure:
✓ total_pct: Must be > 0, typically 2.5% - 5.0%
✓ breakdown: Sum of breakdown must equal total_pct
✓ Each party pct must be > 0
