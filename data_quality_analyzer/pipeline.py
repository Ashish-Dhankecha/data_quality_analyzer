"""Pipeline orchestrator — wires modules 1-6 into one run."""
from __future__ import annotations

import os
from typing import Optional

from .data_loader import DataLoader
from .data_profiler import DataProfiler
from .quality_checker import QualityChecker
from .statistical_analyzer import StatisticalAnalyzer
from .visualization_engine import VisualizationEngine
from .cleaning_report import CleaningConfig, DataCleaner, ReportBuilder
from ._dtypes import text_columns


class Pipeline:
    def __init__(self, output_dir: str, cleaning_cfg: Optional[CleaningConfig] = None):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.cleaning_cfg = cleaning_cfg or CleaningConfig()

    def run(self, input_path: str) -> dict:
        # Module 1
        load_result = DataLoader().load(input_path)
        df = load_result.dataframe

        # Module 2
        profiles = DataProfiler().profile(df)

        # Module 3
        checker = QualityChecker()
        issues = checker.check(df)
        issues_df = checker.to_frame(issues)

        # Module 4
        stats = StatisticalAnalyzer()
        numeric_desc = stats.describe_numeric(df)
        corr = stats.correlation(df)
        strong_corr = stats.strong_correlations(corr) if not corr.empty else []

        # Module 5
        viz = VisualizationEngine(self.output_dir)
        plot_paths = []
        for p in (
            viz.missingness_heatmap(df),
            viz.distributions(df),
            viz.boxplots(df),
            viz.correlation_heatmap(corr),
            viz.categorical_bars(df, text_columns(df)),
        ):
            if p:
                plot_paths.append(p)

        # Module 6
        cleaned_df, cleaning_log = DataCleaner().clean(df, self.cleaning_cfg)
        cleaned_path = os.path.join(self.output_dir, "cleaned.csv")
        cleaned_df.to_csv(cleaned_path, index=False)

        report = ReportBuilder().build_markdown(
            source=input_path,
            load_result=load_result,
            profiles=profiles,
            issues_df=issues_df,
            numeric_desc=numeric_desc,
            corr=corr,
            strong_corr=strong_corr,
            cleaning_log=cleaning_log,
            before_shape=df.shape,
            after_shape=cleaned_df.shape,
            plot_paths=plot_paths,
        )
        report_path = os.path.join(self.output_dir, "report.md")
        with open(report_path, "w") as f:
            f.write(report)

        return {
            "load_result": load_result,
            "profiles": profiles,
            "issues_df": issues_df,
            "numeric_desc": numeric_desc,
            "corr": corr,
            "cleaned_path": cleaned_path,
            "report_path": report_path,
            "plot_paths": plot_paths,
        }
