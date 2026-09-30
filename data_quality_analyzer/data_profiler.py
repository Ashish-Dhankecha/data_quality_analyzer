"""Module 2: Data Profiler
Per-column structural profiling: dtype, nulls, cardinality, semantic type inference.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from ._dtypes import is_text_dtype


@dataclass
class ColumnProfile:
    name: str
    dtype: str
    semantic_type: str
    non_null: int
    nulls: int
    null_pct: float
    unique: int
    unique_pct: float
    memory_kb: float
    sample_values: list[Any]


class DataProfiler:
    def profile(self, df: pd.DataFrame) -> list[ColumnProfile]:
        n = len(df)
        profiles = []
        for col in df.columns:
            s = df[col]
            nulls = int(s.isna().sum())
            non_null = n - nulls
            unique = int(s.nunique(dropna=True))
            profiles.append(ColumnProfile(
                name=col,
                dtype=str(s.dtype),
                semantic_type=self._infer_semantic_type(s),
                non_null=non_null,
                nulls=nulls,
                null_pct=round(100 * nulls / n, 2) if n else 0.0,
                unique=unique,
                unique_pct=round(100 * unique / n, 2) if n else 0.0,
                memory_kb=round(s.memory_usage(deep=True) / 1024, 2),
                sample_values=s.dropna().unique()[:5].tolist(),
            ))
        return profiles

    def _infer_semantic_type(self, s: pd.Series) -> str:
        if pd.api.types.is_bool_dtype(s):
            return "boolean"
        if pd.api.types.is_numeric_dtype(s):
            return "numeric"
        if pd.api.types.is_datetime64_any_dtype(s):
            return "datetime"
        if is_text_dtype(s):
            sample = s.dropna().head(20)
            if len(sample) > 0:
                parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
                if parsed.notna().mean() > 0.8:
                    return "datetime"
            denom = max(len(s.dropna()), 1)
            nunique_ratio = s.nunique(dropna=True) / denom
            return "categorical" if nunique_ratio < 0.5 else "text/high-cardinality"
        return "unknown"

    def summary_frame(self, profiles: list[ColumnProfile]) -> pd.DataFrame:
        return pd.DataFrame([p.__dict__ for p in profiles])
