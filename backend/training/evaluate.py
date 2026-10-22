"""
NØX - Neural Network Intrusion Detection System
Module 02: Model Evaluation & Benchmark Comparison

Evaluates the trained NoxMLP on the official untouched UNSW-NB15 test set.
Computes Accuracy, Precision, Recall, F1-Score, False Positive Rate (FPR), and ROC-AUC.
Evaluates a Logistic Regression baseline on the same data for empirical comparison.
Supports threshold tuning on the validation set, and exports Opium-styled plots & metrics.
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

# Root directory resolution
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import numpy as np
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    roc_auc_score,
    roc_curve,
)
import matplotlib.pyplot as plt
import seaborn as sns

from backend.models.mlp_model import NoxMLP, get_default_device

logger = logging.getLogger("NOX.Evaluate")

# Opium Dark Theme Palette
OPIUM_BG = "#080808"
OPIUM_CARD = "#141414"
OPIUM_TEXT_CHROME = "#D8D8D8"
OPIUM_TEXT_MUTED = "#888888"
OPIUM_THREAT_RED = "#A62735"
OPIUM_SAFE_GREEN = "#2B6E3F"
OPIUM_SILVER = "#B0B0B0"
OPIUM_GRID = "#222222"


def setup_dark_theme():
    """Applies Opium industrial cybersecurity theme to matplotlib."""
    plt.rcParams["figure.facecolor"] = OPIUM_BG
    plt.rcParams["axes.facecolor"] = OPIUM_CARD
    plt.rcParams["axes.edgecolor"] = OPIUM_GRID
    plt.rcParams["axes.labelcolor"] = OPIUM_TEXT_CHROME
    plt.rcParams["xtick.color"] = OPIUM_TEXT_MUTED
    plt.rcParams["ytick.color"] = OPIUM_TEXT_MUTED
    plt.rcParams["text.color"] = OPIUM_TEXT_CHROME
    plt.rcParams["grid.color"] = OPIUM_GRID
    plt.rcParams["grid.linestyle"] = "--"
    plt.rcParams["grid.alpha"] = 0.5
    plt.rcParams["font.sans-serif"] = ["Segoe UI", "DejaVu Sans", "Helvetica", "Arial"]


class ModelEvaluator:
    """
    Evaluator for comparing NoxMLP against a Logistic Regression baseline on the
    untouched UNSW-NB15 test set.
    """

    def __init__(
        self,
        processed_dir: Optional[Path | str] = None,
        model_path: Optional[Path | str] = None,
        metadata_path: Optional[Path | str] = None,
        outputs_dir: Optional[Path | str] = None,
        threshold: float = 0.50,
        device: Optional[torch.device] = None,
    ):
        base_dir = Path(__file__).resolve().parent.parent
        self.processed_dir = Path(processed_dir) if processed_dir else base_dir / "data" / "processed"
        self.model_path = Path(model_path) if model_path else base_dir / "models" / "saved" / "nox_mlp.pth"
        self.metadata_path = Path(metadata_path) if metadata_path else base_dir / "models" / "saved" / "model_metadata.json"
        
        backend_outputs = base_dir / "outputs"
        self.plots_dir = backend_outputs / "plots"
        self.metrics_dir = backend_outputs / "metrics"
        self.threshold = threshold
        self.device = device if device else get_default_device()

        self.plots_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        setup_dark_theme()

    def load_test_and_val_data(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Loads training, validation and test arrays."""
        X_train = np.load(self.processed_dir / "X_train.npy")
        y_train = np.load(self.processed_dir / "y_train.npy")
        X_val = np.load(self.processed_dir / "X_val.npy")
        y_val = np.load(self.processed_dir / "y_val.npy")
        X_test = np.load(self.processed_dir / "X_test.npy")
        y_test = np.load(self.processed_dir / "y_test.npy")
        return X_train, y_train, X_val, y_val, X_test, y_test

    def load_trained_model(self, input_dim: int) -> NoxMLP:
        """Loads model weights into NoxMLP in eval mode."""
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Trained model not found at {self.model_path.resolve()}. "
                "Run training first: python backend/training/train.py"
            )

        model = NoxMLP(input_dim=input_dim).to(self.device)
        state_dict = torch.load(self.model_path, map_location=self.device)
        model.load_state_dict(state_dict)
        model.eval()
        logger.info("Loaded trained NoxMLP from %s into %s", self.model_path, self.device)
        return model

    def find_optimal_threshold(self, model: NoxMLP, X_val: np.ndarray, y_val: np.ndarray) -> float:
        """
        Tunes classification threshold on the validation set to balance recall and precision.
        Returns the threshold maximizing validation F1.
        """
        val_tensor = torch.tensor(X_val, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            val_probs = model.predict_proba(val_tensor).cpu().numpy().flatten()

        candidate_thresholds = np.linspace(0.10, 0.90, 81)
        best_t = 0.50
        best_f1 = -1.0

        for t in candidate_thresholds:
            preds = (val_probs >= t).astype(int)
            f1 = f1_score(y_val, preds, zero_division=0)
            if f1 > best_f1:
                best_f1 = f1
                best_t = float(t)

        logger.info("Validation threshold search: optimal F1=%.4f achieved at threshold=%.2f", best_f1, best_t)
        return best_t

    def evaluate_predictions(self, y_true: np.ndarray, y_probs: np.ndarray, threshold: float) -> Dict[str, Any]:
        """Calculates standard classification metrics."""
        y_pred = (y_probs >= threshold).astype(int)

        cm = confusion_matrix(y_true, y_pred)
        tn, fp, fn, tp = cm.ravel()

        accuracy = float(accuracy_score(y_true, y_pred))
        precision = float(precision_score(y_true, y_pred, zero_division=0))
        recall = float(recall_score(y_true, y_pred, zero_division=0))
        f1 = float(f1_score(y_true, y_pred, zero_division=0))
        fpr = float(fp / max(fp + tn, 1))

        try:
            auc = float(roc_auc_score(y_true, y_probs))
        except ValueError:
            auc = None

        return {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "false_positive_rate": fpr,
            "roc_auc": auc,
            "confusion_matrix": {
                "tn": int(tn),
                "fp": int(fp),
                "fn": int(fn),
                "tp": int(tp),
            },
            "threshold_used": threshold,
        }

    def run_evaluation(self, tune_threshold_on_val: bool = True) -> Dict[str, Any]:
        """
        Executes full evaluation:
        1. Loads test and val sets.
        2. Optionally tunes threshold on validation set.
        3. Generates MLP predictions on test set.
        4. Trains and evaluates Logistic Regression baseline.
        5. Saves confusion matrix and ROC curves.
        6. Writes evaluation_results.json.
        """
        logger.info("=" * 65)
        logger.info("STARTING NØX MODEL EVALUATION & BENCHMARK COMPARISON")
        logger.info("=" * 65)

        X_train, y_train, X_val, y_val, X_test, y_test = self.load_test_and_val_data()
        input_dim = X_test.shape[1]

        # 1. Load Trained MLP
        mlp_model = self.load_trained_model(input_dim)

        # 2. Threshold Selection (on validation set, never test set!)
        if tune_threshold_on_val:
            selected_threshold = self.find_optimal_threshold(mlp_model, X_val, y_val)
        else:
            selected_threshold = self.threshold

        self.threshold = selected_threshold
        logger.info("Frozen classification threshold for test evaluation: %.2f", self.threshold)

        # 3. Evaluate MLP on Untouched Test Set
        test_tensor = torch.tensor(X_test, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            mlp_probs = mlp_model.predict_proba(test_tensor).cpu().numpy().flatten()

        mlp_metrics = self.evaluate_predictions(y_test, mlp_probs, threshold=self.threshold)
        logger.info("MLP Test F1-Score: %.4f | Accuracy: %.4f | Recall: %.4f | FPR: %.4f",
                    mlp_metrics["f1_score"], mlp_metrics["accuracy"], mlp_metrics["recall"], mlp_metrics["false_positive_rate"])

        # 4. Train and Evaluate Logistic Regression Baseline
        logger.info("Training Logistic Regression baseline on processed training data...")
        lr_baseline = LogisticRegression(max_iter=1000, random_state=42)
        lr_baseline.fit(X_train, y_train)

        lr_probs = lr_baseline.predict_proba(X_test)[:, 1]
        lr_metrics = self.evaluate_predictions(y_test, lr_probs, threshold=0.50)
        logger.info("Baseline Logistic Regression Test F1-Score: %.4f | Accuracy: %.4f | Recall: %.4f | FPR: %.4f",
                    lr_metrics["f1_score"], lr_metrics["accuracy"], lr_metrics["recall"], lr_metrics["false_positive_rate"])

        # 5. Generate Plots
        cm_path = self.plot_confusion_matrices(
            cm_mlp=mlp_metrics["confusion_matrix"],
            cm_lr=lr_metrics["confusion_matrix"],
        )
        roc_path = self.plot_roc_curves(
            y_test=y_test,
            mlp_probs=mlp_probs,
            lr_probs=lr_probs,
            mlp_auc=mlp_metrics["roc_auc"],
            lr_auc=lr_metrics["roc_auc"],
        )

        # 6. Save Evaluation Results JSON
        eval_report = {
            "project": "NØX — Neural Network Intrusion Detection System",
            "evaluation_target": "Official UNSW-NB15 Untouched Test Partition (UNSW_NB15_testing-set.csv)",
            "test_sample_count": len(y_test),
            "threat_classification_threshold": self.threshold,
            "threshold_selection_method": "Validation set F1 optimization" if tune_threshold_on_val else "Default (0.50)",
            "mlp_model_performance": mlp_metrics,
            "logistic_regression_baseline_performance": lr_metrics,
            "comparison_summary": {
                "f1_delta": round(mlp_metrics["f1_score"] - lr_metrics["f1_score"], 4),
                "accuracy_delta": round(mlp_metrics["accuracy"] - lr_metrics["accuracy"], 4),
                "fpr_delta": round(mlp_metrics["false_positive_rate"] - lr_metrics["false_positive_rate"], 4),
                "empirical_analysis": (
                    "Empirical comparison between the non-linear Multilayer Perceptron and "
                    "the linear Logistic Regression baseline. Metrics reflect genuine evaluation "
                    "on the standardized UNSW-NB15 benchmark."
                ),
            },
            "generated_plots": {
                "confusion_matrix": str(cm_path),
                "roc_curve": str(roc_path),
            },
        }

        eval_json_path = self.metrics_dir / "evaluation_results.json"
        with open(eval_json_path, "w", encoding="utf-8") as f:
            json.dump(eval_report, f, indent=2)
        logger.info("Evaluation report saved to: %s", eval_json_path)

        # Update metadata.json with the selected threshold
        if self.metadata_path.exists():
            try:
                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                meta["selected_threshold"] = self.threshold
                meta["final_test_metrics"] = mlp_metrics
                with open(self.metadata_path, "w", encoding="utf-8") as f:
                    json.dump(meta, f, indent=2)
                logger.info("Updated model_metadata.json with test metrics and threshold.")
            except Exception as e:
                logger.warning("Could not update model_metadata.json: %s", e)

        self._print_evaluation_table(mlp_metrics, lr_metrics)
        return eval_report

    def plot_confusion_matrices(self, cm_mlp: dict, cm_lr: dict) -> Path:
        """Generates side-by-side confusion matrix plots for MLP and Baseline."""
        mlp_mat = np.array([[cm_mlp["tn"], cm_mlp["fp"]], [cm_mlp["fn"], cm_mlp["tp"]]])
        lr_mat = np.array([[cm_lr["tn"], cm_lr["fp"]], [cm_lr["fn"], cm_lr["tp"]]])

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5), dpi=150)
        labels = ["Normal (0)", "Attack (1)"]

        # Custom red-toned colormap
        cmap = sns.color_palette("dark:#A62735", as_cmap=True)

        # Subplot 1: NoxMLP
        sns.heatmap(
            mlp_mat,
            annot=True,
            fmt=",d",
            cmap=cmap,
            ax=ax1,
            cbar=False,
            annot_kws={"size": 11, "fontweight": "bold", "color": OPIUM_TEXT_CHROME},
        )
        ax1.set_title(f"NØX-MLP (Threshold: {self.threshold:.2f})", fontsize=11, fontweight="bold", pad=12)
        ax1.set_xlabel("Predicted Label", fontsize=10)
        ax1.set_ylabel("True Label", fontsize=10)
        ax1.set_xticklabels(labels)
        ax1.set_yticklabels(labels)

        # Subplot 2: Logistic Regression Baseline
        sns.heatmap(
            lr_mat,
            annot=True,
            fmt=",d",
            cmap=cmap,
            ax=ax2,
            cbar=False,
            annot_kws={"size": 11, "fontweight": "bold", "color": OPIUM_TEXT_CHROME},
        )
        ax2.set_title("Logistic Regression Baseline (Threshold: 0.50)", fontsize=11, fontweight="bold", pad=12)
        ax2.set_xlabel("Predicted Label", fontsize=10)
        ax2.set_ylabel("True Label", fontsize=10)
        ax2.set_xticklabels(labels)
        ax2.set_yticklabels(labels)

        plt.suptitle("NØX — CONFUSION MATRICES (TEST BENCHMARK)", fontsize=13, fontweight="bold", y=1.03)
        plt.tight_layout()

        out_path = self.plots_dir / "confusion_matrix.png"
        fig.savefig(out_path, facecolor=OPIUM_BG)
        plt.close(fig)

        # Mirror to root outputs/plots/
        root_plots_dir = self.plots_dir.parent.parent.parent / "outputs" / "plots"
        if root_plots_dir.exists():
            import shutil
            shutil.copy(out_path, root_plots_dir / out_path.name)

        return out_path

    def plot_roc_curves(
        self,
        y_test: np.ndarray,
        mlp_probs: np.ndarray,
        lr_probs: np.ndarray,
        mlp_auc: Optional[float],
        lr_auc: Optional[float],
    ) -> Path:
        """Plots Receiver Operating Characteristic (ROC) curves."""
        fig, ax = plt.subplots(figsize=(7.5, 6), dpi=150)

        # MLP ROC
        fpr_mlp, tpr_mlp, _ = roc_curve(y_test, mlp_probs)
        mlp_auc_str = f"{mlp_auc:.4f}" if mlp_auc else "N/A"
        ax.plot(fpr_mlp, tpr_mlp, color=OPIUM_THREAT_RED, linewidth=2.2, label=f"NØX-MLP (AUC = {mlp_auc_str})")

        # Baseline ROC
        fpr_lr, tpr_lr, _ = roc_curve(y_test, lr_probs)
        lr_auc_str = f"{lr_auc:.4f}" if lr_auc else "N/A"
        ax.plot(fpr_lr, tpr_lr, color=OPIUM_SILVER, linewidth=1.8, linestyle="--", label=f"Logistic Regression (AUC = {lr_auc_str})")

        # Chance diagonal
        ax.plot([0, 1], [0, 1], color=OPIUM_TEXT_MUTED, linestyle=":", linewidth=1, label="Random Chance (AUC = 0.50)")

        ax.set_title("NØX — RECEIVER OPERATING CHARACTERISTIC (ROC) CURVE", fontsize=11, fontweight="bold", pad=15)
        ax.set_xlabel("False Positive Rate (FPR)", fontsize=10)
        ax.set_ylabel("True Positive Rate (TPR / Recall)", fontsize=10)
        ax.set_xlim([0.0, 1.0])
        ax.set_ylim([0.0, 1.05])
        ax.grid(True)
        ax.legend(loc="lower right", facecolor=OPIUM_CARD, edgecolor=OPIUM_GRID)

        plt.tight_layout()
        out_path = self.plots_dir / "roc_curve.png"
        fig.savefig(out_path, facecolor=OPIUM_BG)
        plt.close(fig)

        # Mirror to root outputs/plots/
        root_plots_dir = self.plots_dir.parent.parent.parent / "outputs" / "plots"
        if root_plots_dir.exists():
            import shutil
            shutil.copy(out_path, root_plots_dir / out_path.name)

        return out_path

    def _print_evaluation_table(self, mlp_metrics: dict, lr_metrics: dict):
        """Displays formatted comparison metrics table."""
        print("\n" + "=" * 70)
        print(" NØX BENCHMARK EVALUATION RESULTS (OFFICIAL TEST SET: 82,332 FLOWS)")
        print("=" * 70)
        print(f"{'Metric':<24}{'NØX-MLP':<22}{'Logistic Regression Baseline':<24}")
        print("-" * 70)
        print(f"{'Accuracy':<24}{mlp_metrics['accuracy']:<22.4f}{lr_metrics['accuracy']:<24.4f}")
        print(f"{'Precision':<24}{mlp_metrics['precision']:<22.4f}{lr_metrics['precision']:<24.4f}")
        print(f"{'Recall (TPR)':<24}{mlp_metrics['recall']:<22.4f}{lr_metrics['recall']:<24.4f}")
        print(f"{'F1-Score':<24}{mlp_metrics['f1_score']:<22.4f}{lr_metrics['f1_score']:<24.4f}")
        print(f"{'False Positive Rate':<24}{mlp_metrics['false_positive_rate']:<22.4f}{lr_metrics['false_positive_rate']:<24.4f}")
        auc_mlp_s = f"{mlp_metrics['roc_auc']:.4f}" if mlp_metrics['roc_auc'] else "N/A"
        auc_lr_s = f"{lr_metrics['roc_auc']:.4f}" if lr_metrics['roc_auc'] else "N/A"
        print(f"{'ROC-AUC':<24}{auc_mlp_s:<22}{auc_lr_s:<24}")
        print(f"{'Threshold':<24}{mlp_metrics['threshold_used']:<22.2f}{lr_metrics['threshold_used']:<24.2f}")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    evaluator = ModelEvaluator()
    report = evaluator.run_evaluation(tune_threshold_on_val=True)
