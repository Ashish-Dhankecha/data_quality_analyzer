"""Shared dtype helpers.

pandas 3.x introduced a dedicated string dtype ("str"/StringDtype) as the
default for text columns, distinct from the legacy "object" dtype pandas
2.x used. Every module that needs "give me the text columns" has to check
both, or it silently drops columns depending on which pandas version ran
the pipeline. Centralized here so the fix lives in one place.
"""
from __future__ import annotations

import pandas as pd


def is_text_dtype(s: pd.Series) -> bool:
    return s.dtype == object or pd.api.types.is_string_dtype(s)


def text_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if is_text_dtype(df[c])]
