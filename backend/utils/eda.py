"""
NØX - Exploratory Data Analysis (EDA) Generator
Generates publication-quality charts for UNSW-NB15 dataset using the
NØX Opium-inspired cybersecurity visual aesthetic.
Outputs saved to: outputs/plots/
"""

import sys
from pathlib import Path

# Add project root to sys.path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

logger = logging.getLogger("NOX.EDA")

# Opium Aesthetic Palette
OPIUM_BG = "#080808"
OPIUM_CARD = "#141414"
OPIUM_TEXT_CHROME = "#D8D8D8"
OPIUM_TEXT_MUTED = "#888888"
OPIUM_THREAT_RED = "#A62735"
OPIUM_SAFE_GREEN = "#2B6E3F"
OPIUM_GRID = "#222222"
OPIUM_ACCENT_SILVER = "#B0B0B0"


def setup_dark_theme():
    """Applies the Opium industrial dark theme to matplotlib."""
    plt.rcParams["figure.facecolor"] = OPIUM_BG
    plt.rcParams["axes.facecolor"] = OPIUM_CARD
    plt.rcParams["axes.edgecolor"] = OPIUM_GRID
    plt.rcParams["axes.labelcolor"] = OPIUM_TEXT_CHROME
    plt.rcParams["xtick.color"] = OPIUM_TEXT_MUTED
    plt.rcParams["ytick.color"] = OPIUM_TEXT_MUTED
    plt.rcParams["text.color"] = OPIUM_TEXT_CHROME
    plt.rcParams["grid.color"] = OPIUM_GRID
    plt.rcParams["grid.linestyle"] = "--"
    plt.rcParams["grid.alpha"] = 0.6
    plt.rcParams["font.sans-serif"] = ["Segoe UI", "DejaVu Sans", "Helvetica", "Arial"]


class DatasetAnalyzer:
    """
    Produces publication-grade EDA visualizations for NØX intrusion detection dataset.
    """

    def __init__(self, raw_train_path: Path | str, output_dir: Path | str):
        self.raw_train_path = Path(raw_train_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        setup_dark_theme()

    def generate_all_plots(self, df: pd.DataFrame | None = None) -> list[Path]:
        """Runs all plot generation routines."""
        if df is None:
            logger.info("Reading raw training dataset from %s for EDA...", self.raw_train_path)
            df = pd.read_csv(self.raw_train_path, encoding="utf-8-sig", low_memory=False)

        generated_files = []
        logger.info("Generating EDA charts in %s ...", self.output_dir)

        p1 = self.plot_traffic_distribution(df)
        p2 = self.plot_attack_categories(df)
        p3 = self.plot_missing_values(df)
        p4 = self.plot_numerical_distributions(df)
        p5 = self.plot_correlation_heatmap(df)

        generated_files.extend([p1, p2, p3, p4, p5])
        logger.info("EDA completed successfully. Generated %d plots.", len(generated_files))
        return generated_files

    def plot_traffic_distribution(self, df: pd.DataFrame) -> Path:
        """Chart 1: Normal versus Malicious Traffic Distribution."""
        fig, ax = plt.subplots(figsize=(8, 6), dpi=150)
        counts = df["label"].value_counts().sort_index()
        total = len(df)
        labels = ["Normal Traffic (0)", "Malicious Traffic (1)"]
        colors = [OPIUM_SAFE_GREEN, OPIUM_THREAT_RED]

        bars = ax.bar(labels, counts.values, color=colors, width=0.45, edgecolor=OPIUM_TEXT_MUTED, linewidth=1.2)

        for bar in bars:
            height = bar.get_height()
            pct = (height / total) * 100
            ax.annotate(
                f"{height:,}\n({pct:.1f}%)",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 6),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=11,
                fontweight="bold",
                color=OPIUM_TEXT_CHROME,
            )

        ax.set_title("NØX — BINARY TRAFFIC DISTRIBUTION (NORMAL vs MALICIOUS)", fontsize=13, fontweight="bold", pad=20)
        ax.set_ylabel("Packet Flow Count", fontsize=11, labelpad=10)
        ax.set_ylim(0, max(counts.values) * 1.15)
        ax.grid(axis="y", linestyle="--", alpha=0.4)

        plt.tight_layout()
        out_path = self.output_dir / "traffic_distribution.png"
        fig.savefig(out_path, facecolor=OPIUM_BG)
        plt.close(fig)
        return out_path

    def plot_attack_categories(self, df: pd.DataFrame) -> Path:
        """Chart 2: Distribution of Attack Categories."""
        fig, ax = plt.subplots(figsize=(10, 6.5), dpi=150)
        cat_counts = df["attack_cat"].fillna("Normal").astype(str).str.strip().value_counts()
        total = len(df)

        # Highlight Normal differently from attacks
        bar_colors = [OPIUM_SAFE_GREEN if cat == "Normal" else OPIUM_THREAT_RED for cat in cat_counts.index]

        y_pos = np.arange(len(cat_counts))
        bars = ax.barh(y_pos, cat_counts.values, color=bar_colors, edgecolor=OPIUM_GRID, height=0.65)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(cat_counts.index, fontsize=10, fontweight="bold")
        ax.invert_yaxis()  # Top-down

        for i, bar in enumerate(bars):
            width = bar.get_width()
            pct = (width / total) * 100
            ax.text(
                width + (max(cat_counts.values) * 0.01),
                bar.get_y() + bar.get_height() / 2,
                f"{width:,} ({pct:.1f}%)",
                va="center",
                ha="left",
                fontsize=9.5,
                color=OPIUM_TEXT_CHROME,
            )

        ax.set_title("NØX — ATTACK CATEGORY FREQUENCY BREAKDOWN", fontsize=13, fontweight="bold", pad=20)
        ax.set_xlabel("Record Count", fontsize=11, labelpad=10)
        ax.set_xlim(0, max(cat_counts.values) * 1.25)
        ax.grid(axis="x", linestyle="--", alpha=0.4)

        plt.tight_layout()
        out_path = self.output_dir / "attack_categories.png"
        fig.savefig(out_path, facecolor=OPIUM_BG)
        plt.close(fig)
        return out_path

    def plot_missing_values(self, df: pd.DataFrame) -> Path:
        """Chart 3: Missing Values Summary & Hygiene Audit."""
        fig, ax = plt.subplots(figsize=(10, 5), dpi=150)

        missing = df.isnull().sum()
        total_missing = missing.sum()

        if total_missing == 0:
            # Display clean verification banner
            ax.text(
                0.5,
                0.5,
                "DATASET HYGIENE AUDIT: ZERO MISSING CELLS\n"
                f"Evaluated {len(df):,} records across {len(df.columns)} features.\n"
                "100.0% data completeness verified.",
                ha="center",
                va="center",
                fontsize=13,
                fontweight="bold",
                color=OPIUM_SAFE_GREEN,
                bbox=dict(boxstyle="round,pad=1.2", facecolor=OPIUM_CARD, edgecolor=OPIUM_SAFE_GREEN, linewidth=1.5),
            )
            ax.set_xticks([])
            ax.set_yticks([])
        else:
            cols_missing = missing[missing > 0].sort_values(ascending=False)
            bars = ax.bar(cols_missing.index, cols_missing.values, color=OPIUM_THREAT_RED, edgecolor=OPIUM_GRID)
            for bar in bars:
                ax.annotate(
                    f"{bar.get_height():,}",
                    xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    xytext=(0, 4),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    fontsize=9,
                    color=OPIUM_TEXT_CHROME,
                )
            ax.set_ylabel("Missing Count", fontsize=11)
            plt.xticks(rotation=45, ha="right")

        ax.set_title("NØX — DATASET COMPLETENESS & MISSING VALUE AUDIT", fontsize=13, fontweight="bold", pad=20)
        plt.tight_layout()
        out_path = self.output_dir / "missing_values_summary.png"
        fig.savefig(out_path, facecolor=OPIUM_BG)
        plt.close(fig)
        return out_path

    def plot_numerical_distributions(self, df: pd.DataFrame) -> Path:
        """Chart 4: Selected Numerical Feature Distributions (Log-scaled flow stats)."""
        selected_features = ["dur", "sbytes", "dbytes", "rate", "sttl", "sload"]
        available_features = [f for f in selected_features if f in df.columns]

        fig, axes = plt.subplots(2, 3, figsize=(14, 8), dpi=150)
        axes = axes.flatten()

        for idx, col in enumerate(available_features):
            ax = axes[idx]
            normal_data = df[df["label"] == 0][col].dropna()
            attack_data = df[df["label"] == 1][col].dropna()

            # Handle skewed flow numbers using log1p if positive values
            if (normal_data >= 0).all() and (attack_data >= 0).all() and col != "sttl":
                sns.kdeplot(np.log1p(normal_data), ax=ax, color=OPIUM_SAFE_GREEN, label="Normal", fill=True, alpha=0.3)
                sns.kdeplot(np.log1p(attack_data), ax=ax, color=OPIUM_THREAT_RED, label="Malicious", fill=True, alpha=0.3)
                ax.set_xlabel(f"log1p({col})", fontsize=10)
            else:
                sns.kdeplot(normal_data, ax=ax, color=OPIUM_SAFE_GREEN, label="Normal", fill=True, alpha=0.3)
                sns.kdeplot(attack_data, ax=ax, color=OPIUM_THREAT_RED, label="Malicious", fill=True, alpha=0.3)
                ax.set_xlabel(col, fontsize=10)

            ax.set_title(f"Distribution: {col}", fontsize=11, fontweight="bold")
            ax.set_ylabel("Density", fontsize=9)
            ax.grid(True, linestyle="--", alpha=0.3)
            if idx == 0:
                ax.legend(facecolor=OPIUM_CARD, edgecolor=OPIUM_GRID)

        plt.suptitle("NØX — SELECTED NUMERICAL FEATURE DISTRIBUTIONS", fontsize=14, fontweight="bold", y=1.02)
        plt.tight_layout()
        out_path = self.output_dir / "numerical_feature_distributions.png"
        fig.savefig(out_path, facecolor=OPIUM_BG)
        plt.close(fig)
        return out_path

    def plot_correlation_heatmap(self, df: pd.DataFrame) -> Path:
        """Chart 5: Correlation Heatmap for Core Numerical Flow Features."""
        core_numeric = [
            "dur",
            "spkts",
            "dpkts",
            "sbytes",
            "dbytes",
            "rate",
            "sttl",
            "dttl",
            "sload",
            "dload",
            "swin",
            "dwin",
            "tcprtt",
            "synack",
            "ackdat",
            "smean",
            "dmean",
            "label",
        ]
        cols = [c for c in core_numeric if c in df.columns]
        corr_matrix = df[cols].corr()

        fig, ax = plt.subplots(figsize=(11, 9), dpi=150)
        # Custom dark red/silver diverging palette
        cmap = sns.diverging_palette(240, 10, as_cmap=True)

        sns.heatmap(
            corr_matrix,
            ax=ax,
            cmap=cmap,
            annot=True,
            fmt=".2f",
            annot_kws={"size": 7.5, "color": OPIUM_TEXT_CHROME},
            linewidths=0.5,
            linecolor=OPIUM_CARD,
            cbar_kws={"shrink": 0.8, "label": "Pearson Correlation"},
        )

        ax.set_title("NØX — FLOW FEATURE CORRELATION MATRIX", fontsize=13, fontweight="bold", pad=15)
        plt.xticks(rotation=45, ha="right", fontsize=9)
        plt.yticks(rotation=0, fontsize=9)

        plt.tight_layout()
        out_path = self.output_dir / "correlation_heatmap.png"
        fig.savefig(out_path, facecolor=OPIUM_BG)
        plt.close(fig)
        return out_path


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent
    train_path = base_dir / "data" / "raw" / "UNSW_NB15_training-set.csv"
    plots_dir = base_dir.parent / "outputs" / "plots"

    analyzer = DatasetAnalyzer(train_path, plots_dir)
    analyzer.generate_all_plots()
    print(f"[+] All EDA charts successfully saved to {plots_dir}")
