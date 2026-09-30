"""Module 5: Visualization Engine
Generates diagnostic plots (missingness, distributions, outliers, correlation,
top categories) and saves them as PNG files.
"""
from __future__ import annotations

import os
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

sns.set_theme(style="whitegrid")


class VisualizationEngine:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.generated: list[str] = []

    def _save(self, fig, name: str) -> str:
        path = os.path.join(self.output_dir, name)
        fig.savefig(path, dpi=140, bbox_inches="tight")
        plt.close(fig)
        self.generated.append(path)
        return path

    def missingness_heatmap(self, df: pd.DataFrame) -> Optional[str]:
        if df.isna().sum().sum() == 0:
            return None
        fig, ax = plt.subplots(figsize=(min(1 + 0.4 * df.shape[1], 14), 5))
        sns.heatmap(df.isna(), cbar=False, cmap="mako", ax=ax)
        ax.set_title("Missing Value Map")
        return self._save(fig, "missingness_heatmap.png")

    def distributions(self, df: pd.DataFrame, max_cols: int = 12) -> Optional[str]:
        num_cols = df.select_dtypes(include=[np.number]).columns[:max_cols]
        if len(num_cols) == 0:
            return None
        n = len(num_cols)
        ncols = min(3, n)
        nrows = int(np.ceil(n / ncols))
        fig, axes = plt.subplots(nrows, ncols, figsize=(5 * ncols, 3.5 * nrows))
        axes = np.atleast_1d(axes).flatten()
        for ax, col in zip(axes, num_cols):
            sns.histplot(df[col].dropna(), kde=True, ax=ax, color="#3E7CB1")
            ax.set_title(col)
        for ax in axes[len(num_cols):]:
            ax.axis("off")
        fig.suptitle("Numeric Distributions")
        fig.tight_layout()
        return self._save(fig, "distributions.png")

    def boxplots(self, df: pd.DataFrame, max_cols: int = 12) -> Optional[str]:
        num_cols = df.select_dtypes(include=[np.number]).columns[:max_cols]
        if len(num_cols) == 0:
            return None
        fig, ax = plt.subplots(figsize=(max(6, 1.2 * len(num_cols)), 5))
        sns.boxplot(data=df[num_cols], ax=ax, palette="Set2")
        ax.set_title("Outlier Overview (Boxplots)")
        ax.tick_params(axis="x", rotation=45)
        return self._save(fig, "boxplots.png")

    def correlation_heatmap(self, corr: pd.DataFrame) -> Optional[str]:
        if corr.empty:
            return None
        fig, ax = plt.subplots(figsize=(max(5, corr.shape[1]), max(4, corr.shape[0] * 0.8)))
        sns.heatmap(corr, annot=corr.shape[1] <= 12, fmt=".2f", cmap="coolwarm",
                    center=0, ax=ax, square=True)
        ax.set_title("Correlation Matrix")
        return self._save(fig, "correlation_heatmap.png")

    def categorical_bars(self, df: pd.DataFrame, cat_cols: list[str], top_n: int = 8) -> Optional[str]:
        cat_cols = cat_cols[:6]
        if not cat_cols:
            return None
        ncols = min(3, len(cat_cols))
        nrows = int(np.ceil(len(cat_cols) / ncols))
        fig, axes = plt.subplots(nrows, ncols, figsize=(5 * ncols, 3.5 * nrows))
        axes = np.atleast_1d(axes).flatten()
        for ax, col in zip(axes, cat_cols):
            vc = df[col].value_counts(dropna=True).head(top_n)
            sns.barplot(x=vc.values, y=vc.index.astype(str), ax=ax, color="#C1666B")
            ax.set_title(col)
        for ax in axes[len(cat_cols):]:
            ax.axis("off")
        fig.suptitle("Top Categories")
        fig.tight_layout()
        return self._save(fig, "categorical_bars.png")
