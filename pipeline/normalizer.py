"""Normalization engine for health data inputs.

Converts arbitrary string timestamps into UTC ISO 8601 objects and
standardizes biometric units (e.g. lbs <-> kg, mmol/L <-> mg/dL).
"""

from datetime import datetime, timezone
from typing import Optional, Union
from dateutil import parser as date_parser


def parse_to_utc(
    raw_date: Union[str, int, float, datetime],
    default_tz: timezone = timezone.utc,
) -> datetime:
    """Parse any datetime representation into a timezone-aware UTC datetime.
    
    Handles UNIX epochs, ISO strings, US date formats (MM/DD/YYYY HH:MM:SS), etc.
    """
    if isinstance(raw_date, datetime):
        if raw_date.tzinfo is None:
            return raw_date.replace(tzinfo=default_tz).astimezone(timezone.utc)
        return raw_date.astimezone(timezone.utc)

    if isinstance(raw_date, (int, float)):
        # Check if timestamp is in milliseconds vs seconds
        if raw_date > 1e11:
            raw_date = raw_date / 1000.0
        return datetime.fromtimestamp(raw_date, tz=timezone.utc)

    if not isinstance(raw_date, str) or not raw_date.strip():
        raise ValueError(f"Cannot parse empty or non-string date: {raw_date}")

    cleaned = raw_date.strip()
    dt = date_parser.parse(cleaned)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=default_tz)
    return dt.astimezone(timezone.utc)


def lbs_to_kg(lbs: float) -> float:
    """Convert pounds to kilograms rounded to 2 decimal places."""
    return round(lbs * 0.45359237, 2)


def kg_to_lbs(kg: float) -> float:
    """Convert kilograms to pounds rounded to 2 decimal places."""
    return round(kg / 0.45359237, 2)


def mmol_to_mgdl(mmol: float) -> float:
    """Convert blood glucose from mmol/L to mg/dL."""
    return round(mmol * 18.0182, 1)


def mgdl_to_mmol(mgdl: float) -> float:
    """Convert blood glucose from mg/dL to mmol/L."""
    return round(mgdl / 18.0182, 2)
