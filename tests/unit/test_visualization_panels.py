#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for visualization panels to prevent regressions.
"""

import tempfile
from pathlib import Path

import pytest
import torch

from src.training.callbacks.visualization import (save_overlay_panel,
                                                  save_prob_panel)


class TestVisualizationPanels:
    """Test visualization panel generation functions."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Create synthetic medical image data
        self.H, self.W, self.D = 64, 64, 32
        self.C_in, self.C_out = 4, 3  # 4 input channels, 3 output classes

        # Synthetic multi-modal image (e.g., T1, T1c, T2, FLAIR)
        self.image = torch.randn(self.C_in, self.H, self.W, self.D)

        # Synthetic ground truth (one-hot encoded)
        self.gt_onehot = torch.zeros(self.C_out, self.H, self.W, self.D)
        self.gt_onehot[0] = 1.0  # background everywhere
        # Add small tumor region
        self.gt_onehot[0, 20:30, 20:30, 10:15] = 0.0
        self.gt_onehot[1, 20:30, 20:30, 10:15] = 1.0  # tumor class

        # Synthetic prediction (similar but slightly different)
        self.pred_onehot = self.gt_onehot.clone()
        self.pred_onehot[1, 22:28, 22:28, 11:14] = 0.8  # smaller prediction
        self.pred_onehot[0] = 1.0 - self.pred_onehot[1] - self.pred_onehot[2]

        # Synthetic probability logits
        self.prob_logits = torch.randn(self.C_out, self.H, self.W, self.D)
        self.prob_logits[1, 20:30, 20:30, 10:15] = 2.0  # higher logits for tumor

    def test_save_overlay_panel_basic(self):
        """Test basic overlay panel generation."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "test_overlay.png"

            save_overlay_panel(
                image_ch_first=self.image,
                label_onehot=self.gt_onehot,
                pred_onehot=self.pred_onehot,
                out_path=output_path,
                slices="auto",
                class_index=1
            )

            # Verify file was created and has reasonable size
            assert output_path.exists(), "Overlay PNG not created"
            assert output_path.stat().st_size > 1000, "PNG file too small"

    def test_save_overlay_panel_custom_slices(self):
        """Test overlay panel with custom slice indices."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "test_custom_slices.png"

            save_overlay_panel(
                image_ch_first=self.image,
                label_onehot=self.gt_onehot,
                pred_onehot=self.pred_onehot,
                out_path=output_path,
                slices=[8, 16, 24],  # Custom slice indices
                class_index=1
            )

            assert output_path.exists(), "Custom slice overlay PNG not created"
            assert output_path.stat().st_size > 1000, "PNG file too small"

    def test_save_overlay_panel_prediction_only(self):
        """Test overlay panel with prediction only (no ground truth)."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "test_pred_only.png"

            save_overlay_panel(
                image_ch_first=self.image,
                label_onehot=None,  # No ground truth
                pred_onehot=self.pred_onehot,
                out_path=output_path,
                slices="auto",
                class_index=1
            )

            assert output_path.exists(), "Prediction-only overlay PNG not created"
            assert output_path.stat().st_size > 1000, "PNG file too small"

    def test_save_overlay_panel_string_slices(self):
        """Test overlay panel with comma-separated string slices."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "test_string_slices.png"

            save_overlay_panel(
                image_ch_first=self.image,
                label_onehot=self.gt_onehot,
                pred_onehot=self.pred_onehot,
                out_path=output_path,
                slices="5,15,25",  # String format
                class_index=1
            )

            assert output_path.exists(), "String slices overlay PNG not created"
            assert output_path.stat().st_size > 1000, "PNG file too small"

    def test_save_prob_panel_with_logits(self):
        """Test probability panel generation from logits."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "test_prob_logits.png"

            save_prob_panel(
                image_ch_first=self.image,
                prob_logits_or_probs=self.prob_logits,
                out_path=output_path,
                slices="auto",
                class_index=1,
                apply_softmax=True  # Apply softmax to logits
            )

            assert output_path.exists(), "Probability panel PNG not created"
            assert output_path.stat().st_size > 1000, "PNG file too small"

    def test_save_prob_panel_with_probs(self):
        """Test probability panel generation from probabilities."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "test_prob_probs.png"

            # Convert logits to probabilities
            probs = torch.softmax(self.prob_logits, dim=0)

            save_prob_panel(
                image_ch_first=self.image,
                prob_logits_or_probs=probs,
                out_path=output_path,
                slices="auto",
                class_index=1,
                apply_softmax=False  # Already probabilities
            )

            assert output_path.exists(), "Probability panel PNG not created"
            assert output_path.stat().st_size > 1000, "PNG file too small"

    def test_save_prob_panel_custom_slices(self):
        """Test probability panel with custom slice selection."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "test_prob_custom.png"

            save_prob_panel(
                image_ch_first=self.image,
                prob_logits_or_probs=self.prob_logits,
                out_path=output_path,
                slices=[4, 12, 20],
                class_index=1,
                apply_softmax=True
            )

            assert output_path.exists(), "Custom slice probability PNG not created"
            assert output_path.stat().st_size > 1000, "PNG file too small"

    def test_auto_directory_creation(self):
        """Test that output directories are created automatically."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Use nested directory that doesn't exist
            output_path = Path(tmp_dir) / "nested" / "dir" / "test_auto_dir.png"

            save_overlay_panel(
                image_ch_first=self.image,
                label_onehot=self.gt_onehot,
                pred_onehot=self.pred_onehot,
                out_path=output_path,
                slices="auto",
                class_index=1
            )

            assert output_path.exists(), "PNG not created in auto-created directory"
            assert output_path.parent.exists(), "Directory not auto-created"

    def test_class_index_bounds_checking(self):
        """Test handling of out-of-bounds class indices."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "test_bounds.png"

            # Test with class index beyond available classes
            save_overlay_panel(
                image_ch_first=self.image,
                label_onehot=self.gt_onehot,
                pred_onehot=self.pred_onehot,
                out_path=output_path,
                slices="auto",
                class_index=99  # Out of bounds
            )

            # Should still create output (will use fallback)
            assert output_path.exists(), "PNG not created with out-of-bounds class index"

    def test_edge_case_single_slice(self):
        """Test with very small depth dimension."""
        # Create image with single slice
        small_image = torch.randn(self.C_in, self.H, self.W, 1)
        small_gt = torch.zeros(self.C_out, self.H, self.W, 1)
        small_gt[0] = 1.0
        small_pred = small_gt.clone()

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "test_single_slice.png"

            save_overlay_panel(
                image_ch_first=small_image,
                label_onehot=small_gt,
                pred_onehot=small_pred,
                out_path=output_path,
                slices="auto",
                class_index=0
            )

            assert output_path.exists(), "Single slice PNG not created"
            assert output_path.stat().st_size > 500, "Single slice PNG too small"


if __name__ == "__main__":
    pytest.main([__file__])
