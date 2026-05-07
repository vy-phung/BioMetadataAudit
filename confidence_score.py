from typing import Dict, Any, Tuple, List, Optional
import standardize_location

def set_rules() -> Dict[str, Any]:
    """
    Define weights, penalties and thresholds for the confidence score.

    V1 principles:
    - Interpretability > mathematical purity
    - Conservative > aggressive
    - Explainable > comprehensive
    """
    return {
        "direct_evidence": {
            # Based on the table we discussed:
            # Accession explicitly linked to country in paper/supplement
            "explicit_geo_pubmed_text": 40,
            # PubMed ID exists AND geo_loc_name exists
            "geo_and_pubmed": 30,
            # geo_loc_name exists (GenBank only)
            "geo_only": 20,
            # accession appears in external text but no structured geo_loc_name
            "accession_in_text_only": 10,
        },
        "consistency": {
            # Predicted country matches GenBank field
            "match": 20,
            # No contradiction detected across sources (when some evidence exists)
            "no_contradiction": 10,
            # Clear contradiction detected between prediction and GenBank
            "contradiction": -30,
        },
        "evidence_density": {
            # ≥2 linked publications
            "two_or_more_pubs": 20,
            # 1 linked publication
            "one_pub": 10,
            # 0 publications
            "none": 0,
        },
        "risk_penalties": {
            # Missing key metadata fields (geo, host, collection_date, etc.)
            "missing_key_fields": -10,
            # Known failure accession pattern (from your existing bug list)
            "known_failure_pattern": -20,
        },
        "tiers": {
            # Confidence tiers (researchers think in categories, not decimals)
            "high_min": 70,
            "medium_min": 40,  # < high_min and >= medium_min = medium; rest = low
        },
    }


def normalize_country(name: Optional[str]) -> Optional[str]:
    """
    Normalize country names to improve simple equality checks.

    This is intentionally simple and rule-based.
    You can extend the mapping as you see real-world variants.
    """
    if not name:
        return None
    name = name.strip().lower()

    mapping = {
        "usa": "united states",
        "u.s.a.": "united states",
        "u.s.": "united states",
        "us": "united states",
        "united states of america": "united states",
        "uk": "united kingdom",
        "u.k.": "united kingdom",
        "england": "united kingdom",
        # Add more mappings here when encounter them in real data
    }

    return mapping.get(name, name)


def compute_confidence_score_and_tier(
    signals: Dict[str, Any],
    rules: Optional[Dict[str, Any]] = None,
) -> Tuple[int, str, List[str]]:
    """
    Compute confidence score and tier for a single accession row.

    Input `signals` dict is expected to contain:

        has_geo_loc_name: bool
        has_pubmed: bool
        accession_found_in_text: bool  # accession present in extracted external text
        predicted_country: str | None  # final model label / country prediction
        genbank_country: str | None    # from NCBI / GenBank metadata
        num_publications: int
        missing_key_fields: bool
        known_failure_pattern: bool

    Returns:
        score (0–100), tier ("high"/"medium"/"low"),
        explanations (list of short human-readable reasons)
    """
    if rules is None:
        rules = set_rules()

    score = 0
    explanations: List[str] = []

    # ---------- Signal 1: Direct evidence strength ----------
    has_geo = bool(signals.get("has_geo_loc_name"))
    has_pubmed = bool(signals.get("has_pubmed"))
    accession_in_text = bool(signals.get("accession_found_in_text"))

    direct_cfg = rules["direct_evidence"]

    # We pick the strongest applicable case.
    if has_geo and has_pubmed and accession_in_text:
        score += direct_cfg["explicit_geo_pubmed_text"]
        explanations.append(
            "Accession linked to a country in GenBank and associated publication text."
        )
    elif has_geo and has_pubmed:
        score += direct_cfg["geo_and_pubmed"]
        explanations.append(
            "GenBank geo_loc_name and linked publication found."
        )
    elif has_geo:
        score += direct_cfg["geo_only"]
        explanations.append("GenBank geo_loc_name present.")
    elif accession_in_text:
        score += direct_cfg["accession_in_text_only"]
        explanations.append("Accession keyword found in extracted external text.")

    # ---------- Signal 2: Cross-source consistency ----------
    print("standardize pre_country")
    pred_country = signals.get("predicted_country")
    if pred_country:
      pred_country = standardize_location.smart_country_lookup(signals.get("predicted_country").lower())
    gb_country = signals.get("genbank_country")
    if gb_country:  
      gb_country = standardize_location.smart_country_lookup(signals.get("genbank_country").lower()) 
    print("both pred_country and gb_country after standardizing: ", pred_country, gb_country)
    cons_cfg = rules["consistency"]
    print("start compare gb country and pre country")
    if gb_country is not None and pred_country is not None:
        print("inside comparison")
        if gb_country.lower() == pred_country.lower():
            score += cons_cfg["match"]
            explanations.append(
                "Predicted country matches GenBank country metadata."
            )
        else:
            score += cons_cfg["contradiction"]
            explanations.append(
                "Conflict between predicted country and GenBank country metadata."
            )
        print("done comparison")    
    else:
        # Only give "no contradiction" bonus if there is at least some evidence
        if has_geo or has_pubmed or accession_in_text:
            score += cons_cfg["no_contradiction"]
            explanations.append(
                "No contradiction detected across available sources."
            )
    print("start evidence density")
    # ---------- Signal 3: Evidence density ----------
    num_pubs = int(signals.get("num_publications", 0))
    dens_cfg = rules["evidence_density"]

    if num_pubs >= 2:
        score += dens_cfg["two_or_more_pubs"]
        explanations.append("Multiple linked publications available.")
    elif num_pubs == 1:
        score += dens_cfg["one_pub"]
        explanations.append("One linked publication available.")
    # else: 0 publications → no extra score

    # ---------- Signal 4: Risk flags ----------
    risk_cfg = rules["risk_penalties"]

    if signals.get("missing_key_fields"):
        score += risk_cfg["missing_key_fields"]
        explanations.append(
            "Missing key metadata fields (higher uncertainty)."
        )

    if signals.get("known_failure_pattern"):
        score += risk_cfg["known_failure_pattern"]
        explanations.append(
            "Accession matches a known risky/failure pattern."
        )

    # ---------- Clamp score and determine tier ----------
    score = max(0, min(100, score))

    tiers = rules["tiers"]
    if score >= tiers["high_min"]:
        tier = "high"
    elif score >= tiers["medium_min"]:
        tier = "medium"
    else:
        tier = "low"

    # Keep explanations short and readable
    if len(explanations) > 3:
        explanations = explanations[:3]
    print("done all")
    return score, tier, explanations


# if __name__ == "__main__":
#     # Quick local sanity-check examples (manual smoke tests)
#     rules = set_rules()

#     examples = [
#         {
#             "name": "Strong, clean case",
#             "signals": {
#                 "has_geo_loc_name": True,
#                 "has_pubmed": True,
#                 "accession_found_in_text": True,
#                 "predicted_country": "USA",
#                 "genbank_country": "United States of America",
#                 "num_publications": 3,
#                 "missing_key_fields": False,
#                 "known_failure_pattern": False,
#             },
#         },
#         {
#             "name": "Weak, conflicting case",
#             "signals": {
#                 "has_geo_loc_name": True,
#                 "has_pubmed": False,
#                 "accession_found_in_text": False,
#                 "predicted_country": "Japan",
#                 "genbank_country": "France",
#                 "num_publications": 0,
#                 "missing_key_fields": True,
#                 "known_failure_pattern": True,
#             },
#         },
#         {
#             "name": "Medium, sparse but okay",
#             "signals": {
#                 "has_geo_loc_name": False,
#                 "has_pubmed": True,
#                 "accession_found_in_text": False,
#                 "predicted_country": "United Kingdom",
#                 "genbank_country": None,
#                 "num_publications": 1,
#                 "missing_key_fields": False,
#                 "known_failure_pattern": False,
#             },
#         },
#     ]

#     for ex in examples:
#         score, tier, expl = compute_confidence_score_and_tier(
#             ex["signals"], rules
#         )
#         print("====", ex["name"], "====")
#         print("Score:", score, "| Tier:", tier)
#         print("Reasons:")
#         for e in expl:
#             print(" -", e)
#         print()