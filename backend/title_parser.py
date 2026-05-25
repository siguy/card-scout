"""Convert an eBay listing title into a CardModel.

Honest disclosure (Cooper): this is regex-and-keywords, not magic. It will be
wrong sometimes — esp. on weird/unusual cards. We log when we can't parse so
we can improve the rules over time.
"""
from __future__ import annotations

import re
from typing import Optional

from .models import CardModel

BRANDS = [
    ("topps chrome", "Topps Chrome"),
    ("topps", "Topps"),
    ("panini prizm", "Panini Prizm"),
    ("prizm", "Panini Prizm"),
    ("panini select", "Panini Select"),
    ("select", "Panini Select"),
    ("panini donruss optic", "Panini Donruss Optic"),
    ("optic", "Panini Donruss Optic"),
    ("donruss", "Panini Donruss"),
    ("upper deck", "Upper Deck"),
    ("fleer", "Fleer"),
    ("stadium club", "Topps Stadium Club"),
    ("bowman", "Bowman"),
]


def _detect_brand(title_lower: str) -> str:
    for needle, label in BRANDS:
        if needle in title_lower:
            return label
    return "Unknown"


def _detect_card_type(title_lower: str) -> str:
    is_rookie = bool(re.search(r"\brookie\b|\brc\b", title_lower))
    if "silver" in title_lower and ("prizm" in title_lower):
        return "Silver Prizm Rookie" if is_rookie else "Silver Prizm"
    if "refractor" in title_lower:
        return "Refractor Rookie" if is_rookie else "Refractor"
    if "auto" in title_lower or "autograph" in title_lower or "signed" in title_lower:
        return "Rookie Autograph" if is_rookie else "Autograph"
    if "patch" in title_lower:
        return "Patch"
    return "Rookie" if is_rookie else "Base"


def _detect_grade(title_lower: str) -> tuple[bool, Optional[str], Optional[float]]:
    grader = None
    for needle, label in [("psa", "PSA"), ("bgs", "BGS"), ("beckett", "BGS"), ("sgc", "SGC")]:
        if re.search(rf"\b{needle}\b", title_lower):
            grader = label
            break
    if not grader:
        return False, None, None
    m = re.search(rf"\b{grader.lower()}\s*(10|9\.5|9|8\.5|8|7\.5|7|6)\b", title_lower)
    if not m:
        m = re.search(r"\b(10|9\.5|9|8\.5|8|7\.5|7|6)\b(?=[^0-9]*(?:gem|mint)?)", title_lower)
    grade = float(m.group(1)) if m else None
    return True, grader, grade


def parse_title(title: str, hint_player: str) -> CardModel:
    t = title.lower()
    year_match = re.search(r"\b(19\d{2}|20\d{2})\b", title)
    year = int(year_match.group(1)) if year_match else 0
    graded, grader, grade = _detect_grade(t)
    return CardModel(
        player_name=hint_player,
        year=year,
        brand=_detect_brand(t),
        card_type=_detect_card_type(t),
        graded=graded,
        grader=grader,
        grade=grade,
    )
