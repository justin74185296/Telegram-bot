"""
This bot is provided strictly for private programming study, data-structure research,
and offline fuzzy-matching experiments. Do NOT deploy publicly or use it to facilitate
any real-world transactions or services.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LocationRecord:
    """
    A single location record loaded from the static JSON database.

    Keep this schema stable so handlers can rely on it.
    """

    country: str
    city: str
    area: str
    sub_area: str
    nickname: str
    address_detail: str
    services: list[str]
    price_range: str
    tg_contacts: list[str]
    notes: str
    last_update: str

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "LocationRecord":
        """Validate and normalize a dict into a LocationRecord."""
        # Defensive parsing: accept missing fields but normalize to safe defaults.
        def _s(key: str) -> str:
            v = d.get(key, "")
            return str(v).strip()

        def _sl(key: str) -> list[str]:
            v = d.get(key, [])
            if not isinstance(v, list):
                return []
            return [str(x).strip() for x in v if str(x).strip()]

        return LocationRecord(
            country=_s("country"),
            city=_s("city"),
            area=_s("area"),
            sub_area=_s("sub_area"),
            nickname=_s("nickname"),
            address_detail=_s("address_detail"),
            services=_sl("services"),
            price_range=_s("price_range"),
            tg_contacts=_sl("tg_contacts"),
            notes=_s("notes"),
            last_update=_s("last_update"),
        )

    def to_search_blob(self) -> str:
        """
        A normalized text blob used for fuzzy matching.
        This intentionally includes multiple fields to support multilingual user input.
        """

        parts = [
            self.country,
            self.city,
            self.area,
            self.sub_area,
            self.nickname,
            self.address_detail,
            " ".join(self.services),
        ]
        return " | ".join(p for p in parts if p).lower()


def load_locations(json_path: Path) -> list[LocationRecord]:
    """
    Load static JSON database from disk.

    Requirements:
    - No network calls.
    - JSON schema: { "locations": [ {...}, ... ] }
    """

    raw = json.loads(json_path.read_text(encoding="utf-8"))
    locs = raw.get("locations", [])
    if not isinstance(locs, list):
        raise ValueError("Invalid JSON schema: 'locations' must be a list.")
    return [LocationRecord.from_dict(x) for x in locs if isinstance(x, dict)]

