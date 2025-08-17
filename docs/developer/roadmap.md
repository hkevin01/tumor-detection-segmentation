# Roadmap and Next Steps (Planning)

This document outlines prioritized, actionable improvements. Items are planned unless explicitly marked implemented in code and tests.

## 1) Reproducible baselines and data readiness

- Minimal, reproducible runs for each recipe in `config/recipes/` on small public subsets (BTCV/MSD/BraTS samples).
- Dataset adapters in `src/data/` with download/verify scripts and checksums.
- Pin versions, deterministic seeds, and cuDNN settings.

## 2) Training quality and reliability

- Early stopping, LR schedulers, AMP autocast + GradScaler, gradient clipping, EMA.
- Cross-validation (fold configs) to avoid single split overfitting.
- Sliding-window inference with TTA in `src/inference/`.
- Class imbalance handling (DiceFocal/TopK) and per-modality normalization.

## 3) Metrics, evaluation, and reporting

- Standard metrics: Dice, IoU, HD95, ASSD, sensitivity/specificity, calibration (ECE/Brier).
- MLflow: confusion maps, qualitative overlays, per-case CSVs, cohort summaries.
- Post-processing: connected components, hole filling, size filters; ablations.

## 4) Multi-modal fusion and cascade improvements

- Modality dropout and gating for missing modalities.
- Learnable modality attention (channel + spatial); ablate early vs late fusion.
- Cascade thresholds and NMS handoff tuning; memory/latency profiling.

## 5) Architecture exploration and NAS

- DiNTS: budget-aware constraints (latency/VRAM) and search-space docs; re-train best architecture.
- Lightweight backbones (SwinUNETR/UNETR tiny) with perf vs cost curves.

## 6) Active learning and MONAI Label

- Acquisition: BALD, predictive entropy, TTA disagreement, region-wise uncertainty.
- Triage scripts; auto-update serving model on new labels.

## 7) Robustness, generalization, harmonization

- Intensity harmonization (z-score/site-aware, Nyul, histogram matching).
- Domain adaptation: test-time normalization, style augmentation, self-ensembling.
- Corruption robustness (noise, motion, bias field).

## 8) Inference, deployment, monitoring

- Half-precision/quantization; ONNX/TensorRT where available.
- Per-case runtime/memory telemetry; drift tracking in MLflow.
- Health-check thresholds for metric drops.

## 9) Testing, CI, documentation

- Expand unit/integration/GUI/API smoke tests.
- CPU-only CI with linting; fast tiny-volume tests.
- Dataset setup, recipes how-to, troubleshooting, expected scores; model cards.

Status: planning (not all items implemented). Update as tasks land.
