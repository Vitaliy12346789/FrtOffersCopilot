"""
AI Service for intelligent clause selection using Claude API.
"""
import os
import json
from typing import Optional
from pathlib import Path

# Try to import anthropic, fallback to rule-based if not available
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


def get_anthropic_client():
    """Get Anthropic client if API key is available."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    if not ANTHROPIC_AVAILABLE:
        return None
    return anthropic.Anthropic(api_key=api_key)


def load_master_library() -> dict:
    """Load Master Library for AI context."""
    library_path = Path(__file__).parent / "master_library.json"
    with open(library_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_clause_summary(clauses: list) -> str:
    """Create a summary of available clauses for AI prompt."""
    summary_lines = []
    for clause in clauses:
        summary_lines.append(
            f"- {clause['clause_id']}: {clause['title']} "
            f"[{clause['category']}/{clause.get('subcategory', 'General')}] "
            f"{'(MANDATORY)' if clause.get('is_mandatory') else ''} "
            f"{'(CHRTR REVIEW)' if clause.get('requires_charterer_review') else ''}"
        )
    return "\n".join(summary_lines)


def rule_based_clause_selection(
    load_port: str,
    discharge_port: str,
    cargo: str,
    port_type: str,
    discharge_country: str,
    cargo_category: str
) -> list[dict]:
    """
    Rule-based clause selection as fallback when AI is not available.
    Returns list of selected clauses with reasons.
    """
    library = load_master_library()
    clauses = library.get("clauses", [])
    selected = []

    for clause in clauses:
        conditions = clause.get("conditions", {})
        reason = None

        # Check port type conditions (Danube vs POC)
        if "port_type" in conditions:
            if conditions["port_type"].upper() == port_type.upper():
                reason = f"Required for {port_type} ports"

        # Check discharge country conditions
        if "discharge_country" in conditions:
            if conditions["discharge_country"].lower() == discharge_country.lower():
                reason = f"Required for {discharge_country} discharge"

        # Check load country conditions
        if "load_country" in conditions:
            if conditions["load_country"].lower() == "ukraine":
                reason = "Required for Ukraine loading"

        # Check cargo category conditions
        if "cargo_category" in conditions:
            if conditions["cargo_category"].lower() == cargo_category.lower():
                reason = f"Required for {cargo_category} cargo"

        # Check specific port conditions
        if "load_port" in conditions:
            if conditions["load_port"].lower() == load_port.lower():
                reason = f"Specific to {load_port} port"

        if "discharge_port" in conditions:
            if conditions["discharge_port"].lower() == discharge_port.lower():
                reason = f"Specific to {discharge_port} port"

        # Always include mandatory clauses without conditions
        if clause.get("is_mandatory") and not conditions:
            reason = "Standard mandatory clause"

        if reason:
            selected.append({
                "clause_id": clause["clause_id"],
                "title": clause["title"],
                "text": clause["text"],
                "category": clause["category"],
                "is_mandatory": clause.get("is_mandatory", False),
                "requires_charterer_review": clause.get("requires_charterer_review", False),
                "reason": reason
            })

    return selected


async def ai_clause_selection(
    load_port: str,
    discharge_port: str,
    cargo: str,
    quantity: int,
    port_type: str,
    discharge_country: str,
    cargo_category: str,
    charterer_name: Optional[str] = None
) -> dict:
    """
    Use Claude AI to intelligently select and explain clause selection.
    Falls back to rule-based selection if AI is not available.
    """
    client = get_anthropic_client()

    if not client:
        # Fallback to rule-based selection
        selected = rule_based_clause_selection(
            load_port=load_port,
            discharge_port=discharge_port,
            cargo=cargo,
            port_type=port_type,
            discharge_country=discharge_country,
            cargo_category=cargo_category
        )
        return {
            "method": "rule-based",
            "clauses": selected,
            "explanation": "AI not available. Using rule-based clause selection based on port type, country, and cargo category.",
            "warnings": []
        }

    # Load Master Library for context
    library = load_master_library()
    clause_summary = get_clause_summary(library.get("clauses", []))

    # Build the prompt
    prompt = f"""You are an expert maritime freight broker assistant. Your task is to select appropriate contract clauses for a firm offer.

## Context
- Load Port: {load_port} ({port_type} port in Ukraine)
- Discharge Port: {discharge_port} ({discharge_country})
- Cargo: {cargo} ({cargo_category} category)
- Quantity: {quantity:,} MT
{f'- Charterer: {charterer_name}' if charterer_name else ''}

## Available Clauses (Master Library)
{clause_summary}

## Your Task
1. Select all relevant clauses for this shipment
2. Explain WHY each clause is needed
3. Flag any clauses that require charterer review
4. Warn about any missing important clauses or potential risks

## Important Rules
- For DANUBE ports: Include Sulina/Bystroe passage, air raids, combined demurrage/detention
- For POC ports: Include JCC inspection, ERWI, war insurance clauses
- For Egypt discharge: Include NOR hours (08:00-12:00 Sun-Thu), SHINC/FHINC, sampling
- For grain cargo: Include previous cargo, trimming, STW verification clauses
- Always include: GSB(A), ISM/ISPS, arbitration, proforma reference

## Response Format
Return a JSON object with:
{{
  "selected_clauses": [
    {{"clause_id": "...", "reason": "..."}}
  ],
  "warnings": ["..."],
  "recommendations": ["..."]
}}
"""

    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",  # Using Haiku for speed and cost
            max_tokens=2000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Parse the response
        response_text = response.content[0].text

        # Extract JSON from response
        import re
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            ai_result = json.loads(json_match.group())

            # Enrich with full clause data
            selected_clauses = []
            clause_map = {c["clause_id"]: c for c in library.get("clauses", [])}

            for item in ai_result.get("selected_clauses", []):
                clause_id = item.get("clause_id")
                if clause_id in clause_map:
                    clause_data = clause_map[clause_id].copy()
                    clause_data["reason"] = item.get("reason", "Selected by AI")
                    selected_clauses.append(clause_data)

            return {
                "method": "ai",
                "clauses": selected_clauses,
                "explanation": "Clauses selected by Claude AI based on route, cargo, and maritime best practices.",
                "warnings": ai_result.get("warnings", []),
                "recommendations": ai_result.get("recommendations", [])
            }

    except Exception as e:
        # Fallback on any error
        print(f"AI selection error: {e}")

    # Fallback to rule-based
    selected = rule_based_clause_selection(
        load_port=load_port,
        discharge_port=discharge_port,
        cargo=cargo,
        port_type=port_type,
        discharge_country=discharge_country,
        cargo_category=cargo_category
    )
    return {
        "method": "rule-based-fallback",
        "clauses": selected,
        "explanation": "AI request failed. Using rule-based clause selection.",
        "warnings": ["AI service temporarily unavailable"]
    }


async def ai_offer_critique(offer_text: str, context: dict) -> dict:
    """
    Use Claude AI to critique a generated offer and suggest improvements.
    """
    client = get_anthropic_client()

    if not client:
        return {
            "available": False,
            "message": "AI critique not available. Configure ANTHROPIC_API_KEY to enable."
        }

    prompt = f"""You are an expert maritime freight broker reviewing a firm offer.

## Offer Context
- Route: {context.get('load_port', 'Unknown')} → {context.get('discharge_port', 'Unknown')}
- Cargo: {context.get('cargo', 'Unknown')} ({context.get('quantity', 0):,} MT)
- Port Type: {context.get('port_type', 'Unknown')}

## Offer Text
{offer_text}

## Your Task
Review this offer and provide:
1. Missing clauses that should be included
2. Potential risks or ambiguities
3. Suggestions for improvement
4. Overall assessment (1-5 stars)

Be specific and practical. Focus on issues that could cause problems during execution.

Return JSON:
{{
  "rating": 4,
  "missing_clauses": ["..."],
  "risks": ["..."],
  "suggestions": ["..."],
  "summary": "..."
}}
"""

    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text

        import re
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            result = json.loads(json_match.group())
            result["available"] = True
            return result

    except Exception as e:
        print(f"AI critique error: {e}")

    return {
        "available": False,
        "message": f"AI critique failed"
    }
