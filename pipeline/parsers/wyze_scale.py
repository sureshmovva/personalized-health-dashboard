"""Parser for Wyze Body Scale Ultra exports (CSV format)."""

from typing import BinaryIO, TextIO, Union
import pandas as pd
from pipeline.models import ScaleRecord, SourceType
from pipeline.normalizer import parse_to_utc, lbs_to_kg, kg_to_lbs
from pipeline.parsers.base import BaseHealthParser


class WyzeScaleParser(BaseHealthParser):
    """Parses Wyze Scale CSV/tabular exports with automated unit detection."""

    def parse(self, file_or_buffer: Union[str, BinaryIO, TextIO]) -> list[ScaleRecord]:
        df = pd.read_csv(file_or_buffer)
        df.columns = [str(c).strip().lower() for c in df.columns]

        # Identify timestamp column
        timestamp_col = None
        for cand in ["time", "date", "weigh time", "timestamp", "measured_at"]:
            if cand in df.columns:
                timestamp_col = cand
                break

        # Identify weight column and unit
        weight_col = None
        is_lbs = True
        for cand in ["weight(lb)", "weight (lbs)", "weight(lbs)", "weight_lbs", "weight (lb)", "weight"]:
            if cand in df.columns:
                weight_col = cand
                is_lbs = True
                break

        if not weight_col:
            for cand in ["weight(kg)", "weight (kg)", "weight_kg"]:
                if cand in df.columns:
                    weight_col = cand
                    is_lbs = False
                    break

        # Body fat % column
        fat_col = None
        for cand in ["body fat(%)", "body fat (%)", "body_fat_pct", "fat percentage", "body fat"]:
            if cand in df.columns:
                fat_col = cand
                break

        # Muscle mass column
        muscle_col = None
        for cand in ["muscle mass(lb)", "muscle mass(kg)", "muscle mass", "muscle"]:
            if cand in df.columns:
                muscle_col = cand
                break

        # Metabolic age column
        age_col = None
        for cand in ["metabolic age", "body age"]:
            if cand in df.columns:
                age_col = cand
                break

        if not timestamp_col or not weight_col:
            raise ValueError(f"Wyze CSV missing timestamp or weight. Columns: {list(df.columns)}")

        records: list[ScaleRecord] = []
        for _, row in df.iterrows():
            raw_w = row[weight_col]
            if pd.isna(raw_w) or str(raw_w).strip() == "":
                continue

            try:
                numeric_w = float(raw_w)
                if is_lbs:
                    w_lbs = round(numeric_w, 2)
                    w_kg = lbs_to_kg(w_lbs)
                else:
                    w_kg = round(numeric_w, 2)
                    w_lbs = kg_to_lbs(w_kg)

                ts = parse_to_utc(row[timestamp_col])
                fat = float(row[fat_col]) if fat_col and not pd.isna(row[fat_col]) else None
                muscle = float(row[muscle_col]) if muscle_col and not pd.isna(row[muscle_col]) else None
                age = int(float(row[age_col])) if age_col and not pd.isna(row[age_col]) else None

                records.append(
                    ScaleRecord(
                        timestamp_utc=ts,
                        weight_kg=w_kg,
                        weight_lbs=w_lbs,
                        body_fat_pct=fat,
                        muscle_mass_kg=muscle,
                        metabolic_age=age,
                        source=SourceType.WYZE_SCALE,
                    )
                )
            except Exception:
                continue

        return records
