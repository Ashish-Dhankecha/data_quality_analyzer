"""Module 3: Quality Checker
Detects concrete data quality issues: duplicates, missingness, outliers,
constant/redundant columns, and inconsistent categorical text.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from ._dtypes import text_columns

@dataclass
class Issue:
    module: str
    column: Optional[str]
    severity: str  # "high" | "medium" | "low"
    description: str
    count: Optional[int] = None


class QualityChecker:
    def __init__(self, missing_threshold: float = 30.0, outlier_z: float = 3.0):
        self.missing_threshold = missing_threshold
        self.outlier_z = outlier_z

    def check(self, df: pd.DataFrame) -> list[Issue]:
        issues: list[Issue] = []
        issues += self._duplicate_rows(df)
        issues += self._duplicate_columns(df)
        issues += self._missing_values(df)
        issues += self._constant_columns(df)
        issues += self._outliers(df)
        issues += self._categorical_inconsistency(df)
        return issues

    def _duplicate_rows(self, df):
        n = int(df.duplicated().sum())
        if n:
            return [Issue("duplicates", None, "high", f"{n} fully duplicated rows", n)]
        return []

    def _duplicate_columns(self, df):
        dup_cols = []
        seen = {}
        for col in df.columns:
            key = tuple(df[col].fillna("__NA__").astype(str))
            if key in seen:
                dup_cols.append((col, seen[key]))
            else:
                seen[key] = col
        return [Issue("duplicates", c, "medium", f"Column duplicates '{ref}'")
                for c, ref in dup_cols]

    def _missing_values(self, df):
        issues = []
        n = len(df)
        for col in df.columns:
            null_count = int(df[col].isna().sum())
            pct = 100 * null_count / n if n else 0
            if pct == 0:
                continue
            sev = "high" if pct >= self.missing_threshold else "low"
            issues.append(Issue("missingness", col, sev, f"{pct:.1f}% missing", null_count))
        return issues

    def _constant_columns(self, df):
        issues = []
        for col in df.columns:
            nun = df[col].nunique(dropna=True)
            if nun <= 1:
                issues.append(Issue("redundancy", col, "medium",
                                     "Constant column (0 or 1 unique values)"))
        return issues

    def _outliers(self, df):
        issues = []
        for col in df.select_dtypes(include=[np.number]).columns:
            s = df[col].dropna()
            if len(s) < 8 or s.std() == 0:
                continue
            z = (s - s.mean()) / s.std()
            n_out = int((z.abs() > self.outlier_z).sum())
            if n_out:
                issues.append(Issue("outliers", col, "medium",
                                     f"{n_out} values beyond |z|>{self.outlier_z}", n_out))
        return issues

    def _categorical_inconsistency(self, df):
        issues = []
        for col in text_columns(df):
            s = df[col].dropna().astype(str)
            if s.empty:
                continue
            has_ws = int((s != s.str.strip()).sum())
            case_collapsed = s.str.lower().str.strip().nunique()
            raw_unique = s.nunique()
            if has_ws:
                issues.append(Issue("consistency", col, "low",
                                     f"{has_ws} values have leading/trailing whitespace", has_ws))
            if case_collapsed < raw_unique:
                issues.append(Issue("consistency", col, "low",
                                     f"Case inconsistency collapses {raw_unique}->{case_collapsed} categories"))
        return issues

    def to_frame(self, issues: list[Issue]) -> pd.DataFrame:
        return pd.DataFrame([i.__dict__ for i in issues])
