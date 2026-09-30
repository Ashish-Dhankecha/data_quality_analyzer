"""Module 6: Cleaning & Report
Applies a configurable cleaning pipeline and renders a Markdown report tying
together profiling, quality issues, statistics and visualizations.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ._dtypes import text_columns


@dataclass
class CleaningConfig:
    drop_duplicate_rows: bool = True
    missing_strategy: str = "median"   # "median" | "mean" | "mode" | "drop_rows" | "none"
    strip_whitespace: bool = True
    standardize_case: bool = False      # lowercases object columns if True
    drop_constant_columns: bool = False
    cap_outliers: bool = False
    outlier_z: float = 3.0


@dataclass
class CleaningLog:
    actions: list[str] = field(default_factory=list)

    def add(self, msg: str):
        self.actions.append(msg)


class DataCleaner:
    def clean(self, df: pd.DataFrame, cfg: CleaningConfig) -> tuple[pd.DataFrame, CleaningLog]:
        log = CleaningLog()
        out = df.copy()

        if cfg.strip_whitespace:
            obj_cols = text_columns(out)
            for c in obj_cols:
                out[c] = out[c].str.strip()
            if len(obj_cols):
                log.add(f"Stripped whitespace on {len(obj_cols)} text columns")

        if cfg.standardize_case:
            obj_cols = text_columns(out)
            for c in obj_cols:
                out[c] = out[c].str.lower()
            log.add("Lowercased text columns")

        if cfg.drop_duplicate_rows:
            before = len(out)
            out = out.drop_duplicates()
            log.add(f"Dropped {before - len(out)} duplicate rows")

        if cfg.drop_constant_columns:
            const_cols = [c for c in out.columns if out[c].nunique(dropna=True) <= 1]
            out = out.drop(columns=const_cols)
            if const_cols:
                log.add(f"Dropped constant columns: {const_cols}")

        if cfg.missing_strategy == "drop_rows":
            before = len(out)
            out = out.dropna()
            log.add(f"Dropped {before - len(out)} rows with any missing value")
        elif cfg.missing_strategy in ("mean", "median"):
            num_cols = out.select_dtypes(include=[np.number]).columns
            for c in num_cols:
                if out[c].isna().any():
                    fill = out[c].mean() if cfg.missing_strategy == "mean" else out[c].median()
                    out[c] = out[c].fillna(fill)
            cat_cols = text_columns(out)
            for c in cat_cols:
                if out[c].isna().any():
                    mode = out[c].mode(dropna=True)
                    out[c] = out[c].fillna(mode.iloc[0] if not mode.empty else "UNKNOWN")
            log.add(f"Imputed numeric NaNs with {cfg.missing_strategy}, categorical with mode")
        elif cfg.missing_strategy == "mode":
            for c in out.columns:
                if out[c].isna().any():
                    mode = out[c].mode(dropna=True)
                    if not mode.empty:
                        out[c] = out[c].fillna(mode.iloc[0])
            log.add("Imputed all NaNs with column mode")

        if cfg.cap_outliers:
            num_cols = out.select_dtypes(include=[np.number]).columns
            capped = 0
            for c in num_cols:
                mean, std = out[c].mean(), out[c].std()
                if std == 0 or pd.isna(std):
                    continue
                lower, upper = mean - cfg.outlier_z * std, mean + cfg.outlier_z * std
                mask = (out[c] < lower) | (out[c] > upper)
                capped += int(mask.sum())
                out[c] = out[c].clip(lower, upper)
            log.add(f"Capped {capped} outlier values at +/-{cfg.outlier_z} sigma")

        return out, log


class ReportBuilder:
    def build_markdown(self, *, source: str, load_result, profiles, issues_df: pd.DataFrame,
                        numeric_desc: pd.DataFrame, corr: pd.DataFrame, strong_corr: list,
                        cleaning_log: CleaningLog, before_shape: tuple, after_shape: tuple,
                        plot_paths: list[str]) -> str:
        lines = []
        lines.append(f"# Data Quality Report — {os.path.basename(source)}\n")
        lines.append(f"- Rows x Columns (raw): **{before_shape[0]} x {before_shape[1]}**")
        lines.append(f"- Rows x Columns (cleaned): **{after_shape[0]} x {after_shape[1]}**")
        lines.append(f"- Load time: {load_result.load_time_s:.3f}s, "
                      f"memory: {load_result.memory_mb:.2f} MB, encoding: {load_result.encoding_used}\n")

        lines.append("## Column Profile\n")
        prof_df = pd.DataFrame([p.__dict__ for p in profiles])
        lines.append(prof_df[["name", "dtype", "semantic_type", "null_pct", "unique", "unique_pct"]]
                      .to_markdown(index=False))
        lines.append("")

        lines.append("## Quality Issues\n")
        if issues_df.empty:
            lines.append("No issues detected.\n")
        else:
            sev_order = {"high": 0, "medium": 1, "low": 2}
            issues_df = issues_df.sort_values(by="severity", key=lambda s: s.map(sev_order))
            lines.append(issues_df.to_markdown(index=False))
            lines.append("")
            counts = issues_df["severity"].value_counts().to_dict()
            lines.append(f"Summary: {counts}\n")

        if not numeric_desc.empty:
            lines.append("## Numeric Statistics\n")
            lines.append(numeric_desc.to_markdown())
            lines.append("")

        if strong_corr:
            lines.append("## Strong Correlations (|r| >= 0.7)\n")
            for a, b, v in strong_corr:
                lines.append(f"- {a} <-> {b}: r={v}")
            lines.append("")

        lines.append("## Cleaning Actions\n")
        for a in cleaning_log.actions:
            lines.append(f"- {a}")
        lines.append("")

        if plot_paths:
            lines.append("## Visualizations\n")
            for p in plot_paths:
                lines.append(f"![{os.path.basename(p)}]({os.path.basename(p)})")
            lines.append("")

        return "\n".join(lines)
