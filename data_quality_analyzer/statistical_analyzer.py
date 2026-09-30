"""Module 4: Statistical Analyzer
Descriptive statistics, distribution shape, and correlation structure.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ._dtypes import text_columns


class StatisticalAnalyzer:
    def describe_numeric(self, df: pd.DataFrame) -> pd.DataFrame:
        num = df.select_dtypes(include=[np.number])
        if num.empty:
            return pd.DataFrame()
        desc = num.describe().T
        desc["skew"] = num.skew()
        desc["kurtosis"] = num.kurtosis()
        desc["missing_pct"] = 100 * num.isna().mean()
        return desc.round(3)

    def describe_categorical(self, df: pd.DataFrame, top_n: int = 5) -> dict[str, pd.Series]:
        out = {}
        cols = set(text_columns(df)) | set(df.select_dtypes(include="category").columns)
        for col in cols:
            out[col] = df[col].value_counts(dropna=True).head(top_n)
        return out

    def correlation(self, df: pd.DataFrame, method: str = "pearson") -> pd.DataFrame:
        num = df.select_dtypes(include=[np.number])
        if num.shape[1] < 2:
            return pd.DataFrame()
        return num.corr(method=method).round(3)

    def strong_correlations(self, corr: pd.DataFrame, threshold: float = 0.7) -> list[tuple]:
        pairs = []
        cols = corr.columns
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                v = corr.iloc[i, j]
                if pd.notna(v) and abs(v) >= threshold:
                    pairs.append((cols[i], cols[j], round(float(v), 3)))
        return sorted(pairs, key=lambda x: -abs(x[2]))
