#!/usr/bin/env python3
"""Data Quality Analyzer — CLI entry point.

Usage:
    python main.py --input data.csv --output-dir out/ \
        --missing-strategy median --cap-outliers
"""
from __future__ import annotations

import argparse
import sys

from data_quality_analyzer.pipeline import Pipeline
from data_quality_analyzer.cleaning_report import CleaningConfig


def parse_args():
    p = argparse.ArgumentParser(description="Data Quality Analyzer")
    p.add_argument("--input", required=True, help="Path to input CSV")
    p.add_argument("--output-dir", default="output", help="Directory for outputs")
    p.add_argument("--missing-strategy", default="median",
                    choices=["median", "mean", "mode", "drop_rows", "none"])
    p.add_argument("--no-drop-duplicates", action="store_true", default=False)
    p.add_argument("--standardize-case", action="store_true", default=False)
    p.add_argument("--drop-constant-columns", action="store_true", default=False)
    p.add_argument("--cap-outliers", action="store_true", default=False)
    return p.parse_args()


def main():
    args = parse_args()
    cfg = CleaningConfig(
        drop_duplicate_rows=not args.no_drop_duplicates,
        missing_strategy=args.missing_strategy,
        standardize_case=args.standardize_case,
        drop_constant_columns=args.drop_constant_columns,
        cap_outliers=args.cap_outliers,
    )
    pipeline = Pipeline(args.output_dir, cfg)
    try:
        result = pipeline.run(args.input)
    except Exception as e:
        print(f"FATAL: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Rows: {result['load_result'].rows}, Cols: {result['load_result'].columns}")
    print(f"Issues found: {len(result['issues_df'])}")
    print(f"Cleaned CSV: {result['cleaned_path']}")
    print(f"Report: {result['report_path']}")
    print(f"Plots: {len(result['plot_paths'])} generated")


if __name__ == "__main__":
    main()
