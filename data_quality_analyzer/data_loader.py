"""Module 1: Data Loader
Robust CSV ingestion — encoding/delimiter fallback, validation, load metadata.
"""
from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class LoadResult:
    dataframe: pd.DataFrame
    source_path: str
    rows: int
    columns: int
    memory_mb: float
    load_time_s: float
    encoding_used: str
    warnings: list[str] = field(default_factory=list)


class DataLoader:
    """Loads a CSV into a DataFrame with encoding/delimiter fallbacks."""

    ENCODINGS = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]

    def load(self, path: str, delimiter: Optional[str] = None) -> LoadResult:
        if not os.path.isfile(path):
            raise FileNotFoundError(f"No such file: {path}")
        if os.path.getsize(path) == 0:
            raise ValueError(f"File is empty: {path}")

        start = time.perf_counter()
        warnings: list[str] = []
        df: Optional[pd.DataFrame] = None
        used_encoding = self.ENCODINGS[0]

        for enc in self.ENCODINGS:
            try:
                if delimiter:
                    df = pd.read_csv(path, encoding=enc, sep=delimiter)
                else:
                    df = pd.read_csv(path, encoding=enc, sep=None, engine="python")
                used_encoding = enc
                if enc != self.ENCODINGS[0]:
                    warnings.append(f"Fell back to encoding={enc}")
                break
            except UnicodeDecodeError:
                continue
            except pd.errors.EmptyDataError:
                raise ValueError(f"File has no parsable columns: {path}")

        if df is None:
            raise ValueError(f"Could not decode {path} with encodings {self.ENCODINGS}")

        if df.shape[0] == 0:
            warnings.append("Loaded 0 data rows (header only).")
        if df.shape[1] == 1:
            warnings.append("Only 1 column detected — check delimiter.")

        load_time = time.perf_counter() - start
        memory_mb = df.memory_usage(deep=True).sum() / (1024 ** 2)

        logger.info(
            "Loaded %s: %d rows x %d cols (%.2f MB, %.3fs)",
            path, df.shape[0], df.shape[1], memory_mb, load_time,
        )

        return LoadResult(
            dataframe=df,
            source_path=path,
            rows=df.shape[0],
            columns=df.shape[1],
            memory_mb=memory_mb,
            load_time_s=load_time,
            encoding_used=used_encoding,
            warnings=warnings,
        )
