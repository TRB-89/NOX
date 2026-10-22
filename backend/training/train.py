"""
NØX - Neural Network Intrusion Detection System
Module 02: Neural Network Training Pipeline

Trains the PyTorch Multilayer Perceptron (NoxMLP) on preprocessed UNSW-NB15 flow data.
Features mini-batch training, BCEWithLogitsLoss, Adam optimizer, validation F1 monitoring,
early stopping with patience, and visual loss/F1 curve plotting adhering to Opium aesthetics.
"""

import sys
import copy
import json
import logging
import datetime
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

# Root directory resolution
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from sklearn.metrics import f1_score, accuracy_score, precision_score, recall_score
import matplotlib.pyplot as plt

from backend.models.mlp_model import NoxMLP, get_default_device

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("NOX.Train")

# Opium Dark Theme Palette
OPIUM_BG = "#080808"
OPIUM_CARD = "#141414"
OPIUM_TEXT_CHROME = "#D8D8D8"
OPIUM_TEXT_MUTED = "#888888"
OPIUM_THREAT_RED = "#A62735"
OPIUM_SILVER = "#B0B0B0"
OPIUM_GRID = "#222222"


def set_seed(seed: int = 42) -> None:
    """Sets random seeds for reproducibility across numpy and torch."""
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


class ModelTrainer:
    """
    Orchestrates the PyTorch training loop, validation tracking, early stopping,
    and checkpoint persistence for NoxMLP.
    """

    def __init__(
        self,
        processed_dir: Optional[Path | str] = None,
        models_save_dir: Optional[Path | str] = None,
        plots_dir: Optional[Path | str] = None,
        epochs: int = 30,
        batch_size: int = 256,
        learning_rate: float = 0.001,
        patience: int = 5,
        random_seed: int = 42,
        use_pos_weight: bool = False,
        device: Optional[torch.device] = None,
    ):
        base_dir = Path(__file__).resolve().parent.parent
        self.processed_dir = Path(processed_dir) if processed_dir else base_dir / "data" / "processed"
        self.models_save_dir = Path(models_save_dir) if models_save_dir else base_dir / "models" / "saved"
        self.plots_dir = Path(plots_dir) if plots_dir else base_dir / "outputs" / "plots"

        self.epochs = epochs
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.patience = patience
        self.random_seed = random_seed
        self.use_pos_weight = use_pos_weight
        self.device = device if device else get_default_device()

        # Create output directories
        self.models_save_dir.mkdir(parents=True, exist_ok=True)
        self.plots_dir.mkdir(parents=True, exist_ok=True)

        set_seed(self.random_seed)

    def load_data(self) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Loads preprocessed training and validation numpy arrays and converts them to tensors.
        Raises informative errors if arrays are missing.
        """
        x_train_path = self.processed_dir / "X_train.npy"
        y_train_path = self.processed_dir / "y_train.npy"
        x_val_path = self.processed_dir / "X_val.npy"
        y_val_path = self.processed_dir / "y_val.npy"

        for p in [x_train_path, y_train_path, x_val_path, y_val_path]:
            if not p.exists():
                raise FileNotFoundError(
                    f"Required preprocessed artifact not found at {p.resolve()}. "
                    "Run Module 01 pipeline first: python backend/preprocessing/pipeline.py"
                )

        logger.info("Loading preprocessed arrays from %s ...", self.processed_dir)
        X_train_np = np.load(x_train_path)
        y_train_np = np.load(y_train_path)
        X_val_np = np.load(x_val_path)
        y_val_np = np.load(y_val_path)

        # Convert to float32 tensors
        X_train = torch.tensor(X_train_np, dtype=torch.float32)
        y_train = torch.tensor(y_train_np, dtype=torch.float32).unsqueeze(1)
        X_val = torch.tensor(X_val_np, dtype=torch.float32)
        y_val = torch.tensor(y_val_np, dtype=torch.float32).unsqueeze(1)

        logger.info(
            "Tensors created: X_train=%s, y_train=%s | X_val=%s, y_val=%s (Device: %s)",
            tuple(X_train.shape),
            tuple(y_train.shape),
            tuple(X_val.shape),
            tuple(y_val.shape),
            self.device,
        )
        return X_train, y_train, X_val, y_val

    def train(self) -> Dict[str, Any]:
        """
        Executes the neural network training loop.
        """
        logger.info("=" * 65)
        logger.info("STARTING NØX NEURAL NETWORK TRAINING (MODULE 02)")
        logger.info("=" * 65)

        X_train, y_train, X_val, y_val = self.load_data()
        input_dim = X_train.shape[1]

        # DataLoaders
        train_dataset = TensorDataset(X_train, y_train)
        val_dataset = TensorDataset(X_val, y_val)
        train_loader = DataLoader(train_dataset, batch_size=self.batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=self.batch_size, shuffle=False)

        # Initialize Model
        model = NoxMLP(input_dim=input_dim).to(self.device)
        optimizer = torch.optim.Adam(model.parameters(), lr=self.learning_rate)

        # Loss Function: calculate pos_weight strictly on training data if requested
        pos_weight_tensor = None
        if self.use_pos_weight:
            num_pos = float((y_train == 1).sum())
            num_neg = float((y_train == 0).sum())
            weight_val = num_neg / max(num_pos, 1.0)
            pos_weight_tensor = torch.tensor([weight_val], device=self.device)
            logger.info("Using training-derived pos_weight: %.4f", weight_val)

        criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight_tensor)

        # Training history trackers
        history: Dict[str, list] = {
            "epoch": [],
            "train_loss": [],
            "val_loss": [],
            "val_f1": [],
            "val_accuracy": [],
            "val_precision": [],
            "val_recall": [],
        }

        best_val_f1 = -1.0
        best_epoch = 0
        best_model_weights = None
        patience_counter = 0

        logger.info("Training on device '%s' for up to %d epochs (batch_size=%d, lr=%s)...",
                    self.device, self.epochs, self.batch_size, self.learning_rate)
        print("-" * 75)
        print(f"{'Epoch':<8}{'Train Loss':<14}{'Val Loss':<14}{'Val F1':<12}{'Val Acc':<12}{'Patience':<10}")
        print("-" * 75)

        for epoch in range(1, self.epochs + 1):
            # 1. Training Phase
            model.train()
            running_loss = 0.0
            total_train_samples = 0

            for batch_x, batch_y in train_loader:
                batch_x = batch_x.to(self.device)
                batch_y = batch_y.to(self.device)

                optimizer.zero_grad()
                logits = model(batch_x)
                loss = criterion(logits, batch_y)
                loss.backward()
                optimizer.step()

                running_loss += loss.item() * batch_x.size(0)
                total_train_samples += batch_x.size(0)

            epoch_train_loss = running_loss / max(total_train_samples, 1)

            # 2. Validation Phase
            model.eval()
            running_val_loss = 0.0
            total_val_samples = 0
            val_logits_list = []
            val_targets_list = []

            with torch.no_grad():
                for batch_x, batch_y in val_loader:
                    batch_x = batch_x.to(self.device)
                    batch_y = batch_y.to(self.device)

                    logits = model(batch_x)
                    loss = criterion(logits, batch_y)

                    running_val_loss += loss.item() * batch_x.size(0)
                    total_val_samples += batch_x.size(0)

                    val_logits_list.append(logits.cpu())
                    val_targets_list.append(batch_y.cpu())

            epoch_val_loss = running_val_loss / max(total_val_samples, 1)

            # Compute validation metrics with default threshold 0.50
            val_logits = torch.cat(val_logits_list, dim=0)
            val_targets = torch.cat(val_targets_list, dim=0).numpy().flatten()
            val_probs = torch.sigmoid(val_logits).numpy().flatten()
            val_preds = (val_probs >= 0.50).astype(int)

            epoch_val_f1 = float(f1_score(val_targets, val_preds, zero_division=0))
            epoch_val_acc = float(accuracy_score(val_targets, val_preds))
            epoch_val_prec = float(precision_score(val_targets, val_preds, zero_division=0))
            epoch_val_rec = float(recall_score(val_targets, val_preds, zero_division=0))

            # Record history
            history["epoch"].append(epoch)
            history["train_loss"].append(epoch_train_loss)
            history["val_loss"].append(epoch_val_loss)
            history["val_f1"].append(epoch_val_f1)
            history["val_accuracy"].append(epoch_val_acc)
            history["val_precision"].append(epoch_val_prec)
            history["val_recall"].append(epoch_val_rec)

            # Check for best model based on validation F1
            is_best = False
            if epoch_val_f1 > best_val_f1:
                best_val_f1 = epoch_val_f1
                best_epoch = epoch
                best_model_weights = copy.deepcopy(model.state_dict())
                patience_counter = 0
                is_best = True
            else:
                patience_counter += 1

            patience_str = f"{patience_counter}/{self.patience}" + (" (BEST)" if is_best else "")
            print(f"{epoch:<8}{epoch_train_loss:<14.4f}{epoch_val_loss:<14.4f}{epoch_val_f1:<12.4f}{epoch_val_acc:<12.4f}{patience_str:<10}")

            # Early Stopping Check
            if patience_counter >= self.patience:
                logger.info(
                    "Early stopping triggered at epoch %d. Validation F1 did not improve for %d epochs.",
                    epoch,
                    self.patience,
                )
                break

        print("-" * 75)
        logger.info("Training complete. Best Validation F1: %.4f at Epoch %d", best_val_f1, best_epoch)

        # Restore best model weights
        if best_model_weights is not None:
            model.load_state_dict(best_model_weights)

        # Save model checkpoint and metadata (TASK 7)
        saved_paths = self.save_model_artifacts(
            model=model,
            best_epoch=best_epoch,
            best_val_f1=best_val_f1,
            history=history,
            input_dim=input_dim,
        )

        # Plot training curves (TASK 4)
        plot_paths = self.generate_training_plots(history)

        results = {
            "best_epoch": best_epoch,
            "best_val_f1": best_val_f1,
            "total_epochs_trained": len(history["epoch"]),
            "final_train_loss": history["train_loss"][-1],
            "final_val_loss": history["val_loss"][-1],
            "saved_model_path": str(saved_paths["model_weights"]),
            "saved_metadata_path": str(saved_paths["metadata"]),
            "plot_paths": [str(p) for p in plot_paths],
            "history": history,
        }
        return results

    def save_model_artifacts(
        self,
        model: NoxMLP,
        best_epoch: int,
        best_val_f1: float,
        history: Dict[str, list],
        input_dim: int,
    ) -> Dict[str, Path]:
        """
        Saves the PyTorch model state_dict and comprehensive training metadata.
        """
        model_weights_path = self.models_save_dir / "nox_mlp.pth"
        metadata_path = self.models_save_dir / "model_metadata.json"

        # 1. Save PyTorch state dict
        torch.save(model.state_dict(), model_weights_path)
        logger.info("Model weights saved successfully to: %s", model_weights_path)

        # Best epoch validation metrics
        idx = best_epoch - 1
        best_metrics = {
            "validation_f1": float(history["val_f1"][idx]),
            "validation_accuracy": float(history["val_accuracy"][idx]),
            "validation_precision": float(history["val_precision"][idx]),
            "validation_recall": float(history["val_recall"][idx]),
            "validation_loss": float(history["val_loss"][idx]),
            "train_loss": float(history["train_loss"][idx]),
        }

        # 2. Save Metadata
        metadata = {
            "model_name": "NØX-MLP-v1",
            "model_version": "1.0.0",
            "date_trained": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "framework": f"PyTorch {torch.__version__}",
            "device_used": str(self.device),
            "random_seed": self.random_seed,
            "architecture": model.get_architecture_summary(),
            "input_feature_count": input_dim,
            "hyperparameters": {
                "max_epochs": self.epochs,
                "batch_size": self.batch_size,
                "learning_rate": self.learning_rate,
                "optimizer": "Adam",
                "loss_function": "BCEWithLogitsLoss",
                "patience": self.patience,
                "use_pos_weight": self.use_pos_weight,
            },
            "best_epoch": best_epoch,
            "total_epochs_run": len(history["epoch"]),
            "selected_threshold": 0.50,
            "best_validation_metrics": best_metrics,
            "note": "UNSW-NB15 historical network benchmark model. Offline intrusion classification.",
        }

        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        logger.info("Model metadata saved successfully to: %s", metadata_path)

        return {"model_weights": model_weights_path, "metadata": metadata_path}

    def generate_training_plots(self, history: Dict[str, list]) -> list[Path]:
        """
        Generates individual and unified training charts adhering to Opium aesthetics:
        - training_loss.png
        - validation_loss.png
        - validation_f1.png
        """
        epochs = history["epoch"]
        train_loss = history["train_loss"]
        val_loss = history["val_loss"]
        val_f1 = history["val_f1"]

        # Apply Opium Dark Theme
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

        generated_plots = []

        # 1. Training Loss versus Epoch
        fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
        ax.plot(epochs, train_loss, color=OPIUM_SILVER, marker="o", markersize=4, linewidth=2, label="Train Loss (BCE)")
        ax.set_title("NØX — TRAINING LOSS VS EPOCH", fontsize=12, fontweight="bold", pad=15)
        ax.set_xlabel("Epoch", fontsize=10)
        ax.set_ylabel("Loss", fontsize=10)
        ax.grid(True)
        ax.legend(facecolor=OPIUM_CARD, edgecolor=OPIUM_GRID)
        plt.tight_layout()
        p1 = self.plots_dir / "training_loss.png"
        fig.savefig(p1, facecolor=OPIUM_BG)
        plt.close(fig)
        generated_plots.append(p1)

        # 2. Validation Loss versus Epoch
        fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
        ax.plot(epochs, val_loss, color=OPIUM_THREAT_RED, marker="s", markersize=4, linewidth=2, label="Validation Loss")
        ax.set_title("NØX — VALIDATION LOSS VS EPOCH", fontsize=12, fontweight="bold", pad=15)
        ax.set_xlabel("Epoch", fontsize=10)
        ax.set_ylabel("Loss", fontsize=10)
        ax.grid(True)
        ax.legend(facecolor=OPIUM_CARD, edgecolor=OPIUM_GRID)
        plt.tight_layout()
        p2 = self.plots_dir / "validation_loss.png"
        fig.savefig(p2, facecolor=OPIUM_BG)
        plt.close(fig)
        generated_plots.append(p2)

        # 3. Validation F1-score versus Epoch
        fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
        ax.plot(epochs, val_f1, color=OPIUM_SILVER, marker="^", markersize=5, linewidth=2, label="Validation F1-Score")
        ax.set_title("NØX — VALIDATION F1-SCORE VS EPOCH", fontsize=12, fontweight="bold", pad=15)
        ax.set_xlabel("Epoch", fontsize=10)
        ax.set_ylabel("F1-Score", fontsize=10)
        ax.set_ylim(0.0, 1.05)
        ax.grid(True)
        ax.legend(facecolor=OPIUM_CARD, edgecolor=OPIUM_GRID)
        plt.tight_layout()
        p3 = self.plots_dir / "validation_f1.png"
        fig.savefig(p3, facecolor=OPIUM_BG)
        plt.close(fig)
        generated_plots.append(p3)

        # Also mirror to root outputs/plots/ for convenience
        root_plots_dir = self.plots_dir.parent.parent.parent / "outputs" / "plots"
        if root_plots_dir.exists():
            for p in [p1, p2, p3]:
                import shutil
                shutil.copy(p, root_plots_dir / p.name)

        logger.info("Training visualization charts saved to: %s", self.plots_dir)
        return generated_plots


if __name__ == "__main__":
    trainer = ModelTrainer(epochs=30, batch_size=256, learning_rate=0.001, patience=5)
    train_results = trainer.train()
    print("\n[+] Training execution completed successfully.")
    print(f"    Best Epoch: {train_results['best_epoch']}")
    print(f"    Best Validation F1: {train_results['best_val_f1']:.4f}")
    print(f"    Model saved to: {train_results['saved_model_path']}")
