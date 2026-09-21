"""Generic flexible parser for manual CSV uploads and external tracker exports."""

from typing import BinaryIO, TextIO, Union
import pandas as pd
from pipeline.models import GlucoseReading, ScaleRecord, SourceType
from pipeline.normalizer import parse_to_utc, lbs_to_kg
from pipeline.parsers.base import BaseHealthParser


class CustomCSVParser(BaseHealthParser):
    """Parses custom multi-metric health logs."""

    def parse(self, file_or_buffer: Union[str, BinaryIO, TextIO]) -> dict[str, list]:
        df = pd.read_csv(file_or_buffer)
        df.columns = [str(c).strip().lower() for c in df.columns]

        timestamp_col = None
        for cand in ["timestamp", "date", "time", "datetime", "logged_at"]:
            if cand in df.columns:
                timestamp_col = cand
                break

        if not timestamp_col:
            raise ValueError(f"Custom CSV requires a date/time column. Found: {list(df.columns)}")

        glucose_list: list[GlucoseReading] = []
        scale_list: list[ScaleRecord] = []

        glucose_col = next((c for c in df.columns if "glucose" in c or "blood_sugar" in c), None)
        weight_col = next((c for c in df.columns if "weight" in c), None)

        for _, row in df.iterrows():
            try:
                ts = parse_to_utc(row[timestamp_col])

                if glucose_col and not pd.isna(row[glucose_col]):
                    val = float(row[glucose_col])
                    glucose_list.append(
                        GlucoseReading(
                            timestamp_utc=ts,
                            glucose_mg_dl=val,
                            source=SourceType.MANUAL_CSV,
                        )
                    )

                if weight_col and not pd.isna(row[weight_col]):
                    w_lbs = float(row[weight_col])
                    scale_list.append(
                        ScaleRecord(
                            timestamp_utc=ts,
                            weight_lbs=round(w_lbs, 2),
                            weight_kg=lbs_to_kg(w_lbs),
                            source=SourceType.MANUAL_CSV,
                        )
                    )
            except Exception:
                continue

        return {"glucose": glucose_list, "scale": scale_list}
