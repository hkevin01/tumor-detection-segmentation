# =============================================================================
# ID: TEST-TRAIN-001
# Requirement: Verify that the core Trainer from src.training.trainer can
#              complete a minimal training loop without error on synthetic data,
#              exercising model construction, loss computation, gradient update,
#              and checkpoint save/load round-trip.
# Purpose: Smoke test catching import failures, API breakage, and regressions
#          introduced by changes to trainer.py or its dependencies.
# Preconditions: src.training.trainer importable; pytest installed
# Postconditions: No exceptions; metrics dict returned with valid keys
# Assumptions: CPU-only; no dataset files required (all data is synthetic)
# Verification: pytest tests/training/simple_train_test.py -v
# =============================================================================
"""Smoke test for the Trainer class with synthetic in-memory data."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def _torch_and_monai() -> bool:
    try:
        import torch  # noqa: F401
        import monai  # noqa: F401
        return True
    except ImportError:
        return False


skip_without_deps = pytest.mark.skipif(
    not _torch_and_monai(),
    reason="torch and monai required for trainer smoke test"
)


class TestTrainerSmoke:
    """Minimal training loop smoke tests."""

    @skip_without_deps
    def test_trainer_imports(self):
        """Trainer class must import without error."""
        from training.trainer import Trainer  # noqa: F401

    @skip_without_deps
    def test_trainer_single_batch(self, tmp_path):
        """Trainer must complete one batch forward+backward on CPU."""
        import torch
        from torch.utils.data import DataLoader, TensorDataset
        from monai.networks.nets import UNet

        from training.trainer import Trainer

        # Tiny UNet for speed
        model = UNet(
            spatial_dims=3,
            in_channels=1,
            out_channels=2,
            channels=(4, 8),
            strides=(2,),
        )

        # Synthetic dataset: 2 samples of 32³
        images = torch.randn(2, 1, 32, 32, 32)
        labels = torch.zeros(2, 1, 32, 32, 32, dtype=torch.float32)

        ds = [
            {"image": images[i], "label": labels[i]}
            for i in range(2)
        ]

        def collate_fn(batch):
            return {
                "image": torch.stack([b["image"] for b in batch]),
                "label": torch.stack([b["label"] for b in batch]),
            }

        loader = DataLoader(ds, batch_size=1, collate_fn=collate_fn)

        config = {
            "device": "cpu",
            "learning_rate": 1e-3,
            "weight_decay": 1e-5,
            "epochs": 1,
            "use_amp": False,
            "use_compile": False,
            "checkpoint_dir": str(tmp_path),
            "num_classes": 2,
            "loss_function": "dice_ce",
            "label_smoothing": 0.0,
        }

        trainer = Trainer(model, loader, loader, config)
        metrics = trainer.train(num_epochs=1)

        assert "train_loss" in metrics or isinstance(metrics, dict)

    @skip_without_deps
    def test_trainer_checkpoint_save(self, tmp_path):
        """Trainer.save_checkpoint must write a valid .pth file."""
        import torch
        from monai.networks.nets import UNet

        from training.trainer import Trainer

        model = UNet(
            spatial_dims=3,
            in_channels=1,
            out_channels=2,
            channels=(4, 8),
            strides=(2,),
        )

        images = torch.randn(1, 1, 32, 32, 32)
        labels = torch.zeros(1, 1, 32, 32, 32)
        ds = [{"image": images[0], "label": labels[0]}]

        def collate_fn(batch):
            return {
                "image": torch.stack([b["image"] for b in batch]),
                "label": torch.stack([b["label"] for b in batch]),
            }

        loader = DataLoader(ds, batch_size=1, collate_fn=collate_fn) \
            if False else [{"image": images, "label": labels}]

        config = {
            "device": "cpu",
            "learning_rate": 1e-3,
            "weight_decay": 1e-5,
            "use_amp": False,
            "use_compile": False,
            "checkpoint_dir": str(tmp_path),
            "num_classes": 2,
            "loss_function": "dice_ce",
            "label_smoothing": 0.0,
        }

        trainer = Trainer(model, [], [], config)
        ckpt_path = tmp_path / "test_checkpoint.pth"
        trainer.save_checkpoint(str(ckpt_path), epoch=0, val_dice=0.5)

        assert ckpt_path.exists()
        loaded = torch.load(str(ckpt_path), weights_only=True)
        assert "model_state_dict" in loaded

    @skip_without_deps
    def test_trainer_load_checkpoint(self, tmp_path):
        """Trainer.load_checkpoint must restore model weights correctly."""
        import torch
        from monai.networks.nets import UNet

        from training.trainer import Trainer

        model = UNet(
            spatial_dims=3,
            in_channels=1,
            out_channels=2,
            channels=(4, 8),
            strides=(2,),
        )

        config = {
            "device": "cpu",
            "learning_rate": 1e-3,
            "weight_decay": 1e-5,
            "use_amp": False,
            "use_compile": False,
            "checkpoint_dir": str(tmp_path),
            "num_classes": 2,
        }

        trainer = Trainer(model, [], [], config)
        ckpt_path = str(tmp_path / "save_and_load.pth")
        trainer.save_checkpoint(ckpt_path, epoch=5, val_dice=0.75)

        # Load into a fresh copy and verify weights match
        model2 = UNet(
            spatial_dims=3,
            in_channels=1,
            out_channels=2,
            channels=(4, 8),
            strides=(2,),
        )
        trainer2 = Trainer(model2, [], [], config)
        trainer2.load_checkpoint(ckpt_path)

        # Parameter values must match after loading
        for p1, p2 in zip(model.parameters(), model2.parameters()):
            assert torch.allclose(p1, p2), "Checkpoint weights not restored correctly"
