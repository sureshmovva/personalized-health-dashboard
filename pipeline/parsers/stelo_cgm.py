"""Parser for Dexcom Stelo Continuous Glucose Monitor (CGM) export files."""

from typing import BinaryIO, TextIO, Union
import pandas as pd
from pipeline.models import GlucoseReading, SourceType
from pipeline.normalizer import parse_to_utc
from pipeline.parsers.base import BaseHealthParser


class SteloCGMParser(BaseHealthParser):
    """Parses Stelo / Dexcom CSV exports into normalized GlucoseReading instances."""

    def parse(self, file_or_buffer: Union[str, BinaryIO, TextIO]) -> list[GlucoseReading]:
        # Handle Dexcom CSV preamble/metadata rows by scanning for header
        df = pd.read_csv(file_or_buffer)
        
        # Standardize column headers (lowercased, stripped)
        df.columns = [str(c).strip().lower() for c in df.columns]

        timestamp_col = None
        for candidate in ["display time", "timestamp", "date", "system time", "local time"]:
            if candidate in df.columns:
                timestamp_col = candidate
                break

        glucose_col = None
        for candidate in ["glucose value (mg/dl)", "glucose", "historic glucose mg/dl", "value", "glucose (mg/dl)"]:
            if candidate in df.columns:
                glucose_col = candidate
                break

        trend_col = None
        for candidate in ["trend arrow", "trend", "direction"]:
            if candidate in df.columns:
                trend_col = candidate
                break

        if not timestamp_col or not glucose_col:
            raise ValueError(
                f"Stelo CSV missing required columns. Found: {list(df.columns)}. "
                "Expected a timestamp and glucose column."
            )

        readings: list[GlucoseReading] = []
        for _, row in df.iterrows():
            raw_val = row[glucose_col]
            if pd.isna(raw_val) or str(raw_val).strip() == "":
                continue

            try:
                numeric_val = float(raw_val)
                # Ignore out-of-range sensor calibration errors (< 20 or > 600)
                if numeric_val < 20.0 or numeric_val > 600.0:
                    continue

                ts = parse_to_utc(row[timestamp_col])
                trend = str(row[trend_col]).strip() if trend_col and not pd.isna(row.get(trend_col)) else None

                readings.append(
                    GlucoseReading(
                        timestamp_utc=ts,
                        glucose_mg_dl=numeric_val,
                        trend_arrow=trend,
                        source=SourceType.STELO_CGM,
                    )
                )
            except Exception:
                continue

        return readings
