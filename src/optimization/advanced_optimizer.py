#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Comprehensive Hyperparameter Optimization for Medical Image Segmentation

This module provides advanced hyperparameter optimization capabilities that
integrate with our enhanced augmentation framework, advanced loss functions,
and benchmarking suite to achieve optimal model performance.

Key Features:
- Multi-objective optimization (accuracy + efficiency)
- Integration with enhanced augmentation and loss functions
- Distributed optimization with Optuna
- Early stopping and pruning strategies
- Comprehensive parameter space exploration
- Performance analysis and visualization
"""

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import numpy as np

try:
    import optuna
    from optuna.pruners import HyperbandPruner, MedianPruner
    from optuna.samplers import CmaEsSampler, TPESampler
    from optuna.study import MaxTrialsCallback
    from optuna.trial import TrialState
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False
    logging.warning("Optuna not available. Hyperparameter optimization will be limited.")

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logging.warning("PyTorch not available. Training will be limited.")

# Import our frameworks
from ..augmentation import AugmentationConfig, create_augmentation_from_config
from ..benchmarking import ModelRegistry
from ..losses import CombinedLoss, LossFunctionFactory


@dataclass
class OptimizationConfig:
    """Configuration for hyperparameter optimization study."""

    # Study configuration
    study_name: str
    direction: str = "maximize"  # maximize or minimize
    storage_url: Optional[str] = None  # For distributed optimization

    # Optimization settings
    n_trials: int = 100
    timeout: Optional[float] = None  # Maximum study duration in seconds
    n_startup_trials: int = 10
    n_warmup_steps: int = 5

    # Sampling and pruning
    sampler: str = "tpe"  # tpe, cmaes, random
    pruner: str = "median"  # median, hyperband, none
    pruning_warmup_steps: int = 5

    # Multi-objective settings
    objectives: List[str] = field(default_factory=lambda: ["dice_score"])
    objective_weights: Dict[str, float] = field(default_factory=dict)

    # Early stopping
    early_stopping_rounds: Optional[int] = 20
    min_improvement: float = 0.001

    # Resource constraints
    max_epochs_per_trial: int = 50
    max_time_per_trial: int = 3600  # 1 hour

    # Output configuration
    output_dir: str = "optimization_results"
    save_intermediate_results: bool = True

    # Target performance
    target_dice: float = 0.85
    target_speedup: float = 1.3  # 30% faster than baseline


@dataclass
class TrialResult:
    """Results from a single optimization trial."""
    trial_number: int
    parameters: Dict[str, Any]
    objectives: Dict[str, float]
    trial_time: float
    trial_state: str
    intermediate_values: List[float] = field(default_factory=list)
    model_config: Optional[Dict[str, Any]] = None


@dataclass
class OptimizationResults:
    """Complete optimization study results."""
    config: OptimizationConfig
    best_trials: List[TrialResult]
    all_trials: List[TrialResult]
    study_time: float
    convergence_info: Dict[str, Any]
    parameter_importance: Dict[str, float] = field(default_factory=dict)

    def get_best_parameters(self, objective: str = "dice_score") -> Dict[str, Any]:
        """Get best parameters for a specific objective."""
        if not self.best_trials:
            return {}

        # Find best trial for the objective
        best_trial = max(self.best_trials,
                        key=lambda t: t.objectives.get(objective, 0))
        return best_trial.parameters

    def get_pareto_frontier(self) -> List[TrialResult]:
        """Get Pareto frontier for multi-objective optimization."""
        if len(self.config.objectives) <= 1:
            return self.best_trials[:1]

        # Simple Pareto frontier identification
        pareto_trials = []
        for trial1 in self.all_trials:
            is_pareto = True
            for trial2 in self.all_trials:
                if trial1 == trial2:
                    continue

                # Check if trial2 dominates trial1
                dominates = True
                for obj in self.config.objectives:
                    if trial2.objectives.get(obj, 0) <= trial1.objectives.get(obj, 0):
                        dominates = False
                        break

                if dominates:
                    is_pareto = False
                    break

            if is_pareto:
                pareto_trials.append(trial1)

        return pareto_trials


class AdvancedOptimizer:
    """Advanced hyperparameter optimizer integrating all framework components."""

    def __init__(self, config: OptimizationConfig):
        self.config = config
        self.logger = self._setup_logging()

        # Initialize Optuna study
        self.study: Optional[optuna.Study] = None
        self._setup_study()

        # Results tracking
        self.trial_results: List[TrialResult] = []
        self.start_time: Optional[float] = None

        # Framework integrations
        self.augmentation_factory = self._setup_augmentation_factory()
        self.loss_factory = LossFunctionFactory()

        # Create output directory
        Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for optimization."""
        logger = logging.getLogger(f"optimizer_{self.config.study_name}")
        logger.setLevel(logging.INFO)

        # File handler
        log_file = Path(self.config.output_dir) / "optimization.log"
        handler = logging.FileHandler(log_file)
        handler.setLevel(logging.INFO)

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def _setup_study(self) -> None:
        """Setup Optuna study with samplers and pruners."""
        if not OPTUNA_AVAILABLE:
            return

        # Configure sampler
        if self.config.sampler == "tpe":
            sampler = TPESampler(
                n_startup_trials=self.config.n_startup_trials,
                n_ei_candidates=24,
                seed=42
            )
        elif self.config.sampler == "cmaes":
            sampler = CmaEsSampler(seed=42)
        else:
            sampler = optuna.samplers.RandomSampler(seed=42)

        # Configure pruner
        if self.config.pruner == "median":
            pruner = MedianPruner(
                n_startup_trials=self.config.n_startup_trials,
                n_warmup_steps=self.config.pruning_warmup_steps
            )
        elif self.config.pruner == "hyperband":
            pruner = HyperbandPruner(
                min_resource=1,
                max_resource=self.config.max_epochs_per_trial
            )
        else:
            pruner = optuna.pruners.NopPruner()

        # Create study
        study_direction = "maximize" if self.config.direction == "maximize" else "minimize"

        self.study = optuna.create_study(
            study_name=self.config.study_name,
            direction=study_direction,
            sampler=sampler,
            pruner=pruner,
            storage=self.config.storage_url
        )

    def _setup_augmentation_factory(self) -> AugmentationConfig:
        """Setup augmentation configuration factory."""
        return AugmentationConfig()

    def define_parameter_space(self, trial: 'optuna.Trial') -> Dict[str, Any]:
        """Define comprehensive parameter space for optimization."""
        params = {}

        # Model architecture parameters
        params['model_name'] = trial.suggest_categorical(
            'model_name', ['unet', 'segresnet', 'unetr', 'swin_unetr']
        )

        # Training parameters
        params['learning_rate'] = trial.suggest_float('learning_rate', 1e-5, 1e-2, log=True)
        params['batch_size'] = trial.suggest_categorical('batch_size', [1, 2, 4, 8])
        params['optimizer'] = trial.suggest_categorical('optimizer', ['adam', 'adamw', 'sgd'])

        # Loss function parameters
        params['loss_type'] = trial.suggest_categorical(
            'loss_type', ['dice', 'focal', 'combined', 'adaptive_combined']
        )

        if params['loss_type'] == 'combined':
            params['dice_weight'] = trial.suggest_float('dice_weight', 0.3, 0.7)
            params['ce_weight'] = trial.suggest_float('ce_weight', 0.3, 0.7)

        if params['loss_type'] == 'focal':
            params['focal_alpha'] = trial.suggest_float('focal_alpha', 0.1, 1.0)
            params['focal_gamma'] = trial.suggest_float('focal_gamma', 1.0, 3.0)

        if params['loss_type'] == 'adaptive_combined':
            params['adaptation_method'] = trial.suggest_categorical(
                'adaptation_method', ['epoch_based', 'loss_based', 'performance_based']
            )

        # Augmentation parameters
        params['augmentation_domain'] = trial.suggest_categorical(
            'augmentation_domain', ['brain_tumor', 'cardiac_segmentation', 'liver_lesion']
        )

        # Spatial augmentation intensity
        params['spatial_intensity'] = trial.suggest_float('spatial_intensity', 0.1, 1.0)
        params['intensity_intensity'] = trial.suggest_float('intensity_intensity', 0.1, 1.0)
        params['noise_intensity'] = trial.suggest_float('noise_intensity', 0.0, 0.8)

        # Specific augmentation parameters
        params['elastic_alpha_range'] = trial.suggest_float('elastic_alpha_range', 5.0, 25.0)
        params['gamma_range'] = trial.suggest_float('gamma_range', 0.2, 0.4)
        params['rotation_range'] = trial.suggest_float('rotation_range', 5.0, 15.0)

        # Training schedule parameters
        params['scheduler'] = trial.suggest_categorical('scheduler', ['cosine', 'step', 'plateau'])

        if params['scheduler'] == 'step':
            params['step_size'] = trial.suggest_int('step_size', 20, 50)
            params['step_gamma'] = trial.suggest_float('step_gamma', 0.1, 0.5)

        # Regularization
        params['weight_decay'] = trial.suggest_float('weight_decay', 1e-6, 1e-3, log=True)
        params['dropout'] = trial.suggest_float('dropout', 0.0, 0.3)

        return params

    def create_training_components(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create training components from parameters."""
        components = {}

        # Model
        model_config = self._create_model_config(params)
        components['model'] = ModelRegistry.get_model(params['model_name'], model_config)

        # Loss function
        components['loss_fn'] = self._create_loss_function(params)

        # Augmentation pipeline
        components['augmentation'] = self._create_augmentation_pipeline(params)

        # Optimizer
        components['optimizer_fn'] = self._create_optimizer_factory(params)

        # Scheduler
        components['scheduler_fn'] = self._create_scheduler_factory(params)

        return components

    def _create_model_config(self, params: Dict[str, Any]) -> Any:
        """Create model configuration from parameters."""
        from ..benchmarking.model_registry import ModelConfig

        config = ModelConfig(
            name=f"{params['model_name']}_optimized",
            architecture=params['model_name'],
            model_params={
                'dropout_prob': params.get('dropout', 0.0)
            }
        )
        return config

    def _create_loss_function(self, params: Dict[str, Any]) -> Callable:
        """Create loss function from parameters."""
        loss_type = params['loss_type']

        if loss_type == 'dice':
            return self.loss_factory.create_loss('dice')
        elif loss_type == 'focal':
            return self.loss_factory.create_loss('focal',
                alpha=params.get('focal_alpha', 0.25),
                gamma=params.get('focal_gamma', 2.0)
            )
        elif loss_type == 'combined':
            return CombinedLoss(
                loss_types=['dice', 'crossentropy'],
                weights=[params.get('dice_weight', 0.5), params.get('ce_weight', 0.5)]
            )
        elif loss_type == 'adaptive_combined':
            from ..losses.adaptive_loss import AdaptiveCombinedLoss
            return AdaptiveCombinedLoss(
                adaptation_method=params.get('adaptation_method', 'epoch_based')
            )
        else:
            return self.loss_factory.create_loss('dice')

    def _create_augmentation_pipeline(self, params: Dict[str, Any]) -> Any:
        """Create augmentation pipeline from parameters."""
        domain = params.get('augmentation_domain', 'brain_tumor')
        base_config = self.augmentation_factory.get_domain_config(domain)

        # Modify augmentation intensities
        modifications = {
            'spatial': {
                0: {
                    'alpha_range': (5.0, params.get('elastic_alpha_range', 15.0)),
                    'prob': 0.3 * params.get('spatial_intensity', 1.0)
                }
            },
            'intensity': {
                0: {
                    'gamma_range': (
                        1.0 - params.get('gamma_range', 0.2),
                        1.0 + params.get('gamma_range', 0.2)
                    ),
                    'prob': 0.5 * params.get('intensity_intensity', 1.0)
                }
            }
        }

        custom_config = self.augmentation_factory.create_custom_config(
            domain, modifications
        )

        return create_augmentation_from_config(custom_config)

    def _create_optimizer_factory(self, params: Dict[str, Any]) -> Callable:
        """Create optimizer factory function."""
        def create_optimizer(model):
            if not TORCH_AVAILABLE:
                return None

            optimizer_type = params.get('optimizer', 'adam')
            lr = params.get('learning_rate', 1e-4)
            weight_decay = params.get('weight_decay', 1e-5)

            if optimizer_type == 'adam':
                return torch.optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)
            elif optimizer_type == 'adamw':
                return torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
            elif optimizer_type == 'sgd':
                return torch.optim.SGD(model.parameters(), lr=lr,
                                     momentum=0.9, weight_decay=weight_decay)
            else:
                return torch.optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)

        return create_optimizer

    def _create_scheduler_factory(self, params: Dict[str, Any]) -> Callable:
        """Create learning rate scheduler factory function."""
        def create_scheduler(optimizer):
            if not TORCH_AVAILABLE:
                return None

            scheduler_type = params.get('scheduler', 'cosine')

            if scheduler_type == 'cosine':
                return torch.optim.lr_scheduler.CosineAnnealingLR(
                    optimizer, T_max=self.config.max_epochs_per_trial
                )
            elif scheduler_type == 'step':
                step_size = params.get('step_size', 30)
                gamma = params.get('step_gamma', 0.1)
                return torch.optim.lr_scheduler.StepLR(
                    optimizer, step_size=step_size, gamma=gamma
                )
            elif scheduler_type == 'plateau':
                return torch.optim.lr_scheduler.ReduceLROnPlateau(
                    optimizer, patience=10, factor=0.5
                )
            else:
                return None

        return create_scheduler

    def objective_function(
        self,
        trial: 'optuna.Trial',
        train_loader: DataLoader,
        val_loader: DataLoader,
        device: str = "cpu"
    ) -> Union[float, List[float]]:
        """Objective function for optimization."""

        # Get trial parameters
        params = self.define_parameter_space(trial)

        # Create training components
        components = self.create_training_components(params)

        # Setup training
        model = components['model']
        loss_fn = components['loss_fn']
        optimizer = components['optimizer_fn'](model)
        scheduler = components['scheduler_fn'](optimizer) if components['scheduler_fn'] else None

        if TORCH_AVAILABLE:
            model = model.to(device)

        # Training loop with early stopping
        best_val_dice = 0.0
        training_start_time = time.time()

        for epoch in range(self.config.max_epochs_per_trial):
            if not TORCH_AVAILABLE:
                break

            # Training phase
            model.train()
            train_loss = 0.0

            for batch_idx, (data, target) in enumerate(train_loader):
                data, target = data.to(device), target.to(device)

                optimizer.zero_grad()
                output = model(data)
                loss = loss_fn(output, target)
                loss.backward()
                optimizer.step()

                train_loss += loss.item()

            # Validation phase
            model.eval()
            val_loss = 0.0
            val_dice = 0.0

            with torch.no_grad():
                for data, target in val_loader:
                    data, target = data.to(device), target.to(device)
                    output = model(data)
                    loss = loss_fn(output, target)
                    val_loss += loss.item()

                    # Calculate Dice score
                    pred = torch.argmax(output, dim=1)
                    dice = self._compute_dice_score(pred.cpu().numpy(), target.cpu().numpy())
                    val_dice += dice

            avg_val_dice = val_dice / len(val_loader)
            best_val_dice = max(best_val_dice, avg_val_dice)

            # Report intermediate value for pruning
            trial.report(avg_val_dice, epoch)

            # Check if trial should be pruned
            if trial.should_prune():
                raise optuna.exceptions.TrialPruned()

            # Update learning rate
            if scheduler:
                if isinstance(scheduler, torch.optim.lr_scheduler.ReduceLROnPlateau):
                    scheduler.step(val_loss / len(val_loader))
                else:
                    scheduler.step()

            # Early stopping based on validation performance
            if epoch > 10 and avg_val_dice < 0.3:  # Stop very poor trials early
                raise optuna.exceptions.TrialPruned()

        training_time = time.time() - training_start_time

        # Calculate objectives
        dice_score = best_val_dice
        training_efficiency = 1.0 / training_time  # Higher is better

        # Multi-objective optimization
        if len(self.config.objectives) == 1:
            if 'dice_score' in self.config.objectives:
                return dice_score
            elif 'training_efficiency' in self.config.objectives:
                return training_efficiency
            else:
                return dice_score
        else:
            # Return weighted combination for multi-objective
            objectives = []
            for obj in self.config.objectives:
                if obj == 'dice_score':
                    objectives.append(dice_score)
                elif obj == 'training_efficiency':
                    objectives.append(training_efficiency)
                else:
                    objectives.append(dice_score)

            # Weighted sum
            weights = [self.config.objective_weights.get(obj, 1.0) for obj in self.config.objectives]
            return sum(w * obj for w, obj in zip(weights, objectives))

    def _compute_dice_score(self, prediction: np.ndarray, ground_truth: np.ndarray) -> float:
        """Compute Dice score for evaluation."""
        pred_flat = (prediction > 0).astype(int).flatten()
        gt_flat = (ground_truth > 0).astype(int).flatten()

        intersection = np.sum(pred_flat * gt_flat)
        total = np.sum(pred_flat) + np.sum(gt_flat)

        if total == 0:
            return 1.0

        dice = (2.0 * intersection) / total
        return dice

    def run_optimization(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        device: str = "cpu"
    ) -> OptimizationResults:
        """Run the complete optimization study."""

        if not OPTUNA_AVAILABLE:
            raise RuntimeError("Optuna is required for optimization")

        self.logger.info(f"Starting optimization study: {self.config.study_name}")
        self.start_time = time.time()

        # Create objective function
        def objective(trial):
            return self.objective_function(trial, train_loader, val_loader, device)

        # Run optimization
        try:
            self.study.optimize(
                objective,
                n_trials=self.config.n_trials,
                timeout=self.config.timeout,
                callbacks=[MaxTrialsCallback(self.config.n_trials)]
            )
        except KeyboardInterrupt:
            self.logger.info("Optimization interrupted by user")

        study_time = time.time() - self.start_time

        # Process results
        results = self._process_results(study_time)

        # Save results
        self._save_results(results)

        self.logger.info(f"Optimization completed in {study_time:.2f} seconds")
        return results

    def _process_results(self, study_time: float) -> OptimizationResults:
        """Process optimization results."""

        # Convert trials to our format
        all_trials = []
        for trial in self.study.trials:
            trial_result = TrialResult(
                trial_number=trial.number,
                parameters=trial.params,
                objectives={'dice_score': trial.value} if trial.value else {},
                trial_time=0.0,  # Would need to track this separately
                trial_state=trial.state.name,
                intermediate_values=list(trial.intermediate_values.values())
            )
            all_trials.append(trial_result)

        # Get best trials
        completed_trials = [t for t in all_trials if t.trial_state == 'COMPLETE']
        best_trials = sorted(completed_trials,
                           key=lambda t: t.objectives.get('dice_score', 0),
                           reverse=True)[:10]

        # Calculate parameter importance
        parameter_importance = {}
        if OPTUNA_AVAILABLE and len(completed_trials) > 10:
            try:
                importance = optuna.importance.get_param_importances(self.study)
                parameter_importance = importance
            except Exception as e:
                self.logger.warning(f"Could not calculate parameter importance: {e}")

        # Convergence analysis
        convergence_info = {
            'total_trials': len(all_trials),
            'completed_trials': len(completed_trials),
            'pruned_trials': len([t for t in all_trials if t.trial_state == 'PRUNED']),
            'best_value': self.study.best_value if hasattr(self.study, 'best_value') else 0.0,
            'convergence_trial': self._find_convergence_trial(completed_trials)
        }

        return OptimizationResults(
            config=self.config,
            best_trials=best_trials,
            all_trials=all_trials,
            study_time=study_time,
            convergence_info=convergence_info,
            parameter_importance=parameter_importance
        )

    def _find_convergence_trial(self, trials: List[TrialResult]) -> int:
        """Find when the optimization converged."""
        if len(trials) < 10:
            return len(trials)

        best_values = []
        current_best = 0.0

        for trial in trials:
            value = trial.objectives.get('dice_score', 0)
            current_best = max(current_best, value)
            best_values.append(current_best)

        # Find when improvement becomes minimal
        for i in range(10, len(best_values)):
            recent_improvement = best_values[i] - best_values[i-10]
            if recent_improvement < self.config.min_improvement:
                return i

        return len(trials)

    def _save_results(self, results: OptimizationResults) -> None:
        """Save optimization results."""
        results_file = Path(self.config.output_dir) / "optimization_results.json"

        # Convert to serializable format
        results_dict = asdict(results)

        with open(results_file, 'w') as f:
            json.dump(results_dict, f, indent=2, default=str)

        self.logger.info(f"Results saved to {results_file}")


def run_optimization_study(
    config: OptimizationConfig,
    train_loader: DataLoader,
    val_loader: DataLoader,
    device: str = "cpu"
) -> OptimizationResults:
    """Convenience function to run optimization study."""
    optimizer = AdvancedOptimizer(config)
    return optimizer.run_optimization(train_loader, val_loader, device)


def create_optimization_study(
    study_name: str,
    n_trials: int = 100,
    objectives: List[str] = None,
    output_dir: str = "optimization_results"
) -> OptimizationConfig:
    """Create optimization study configuration."""
    if objectives is None:
        objectives = ["dice_score"]

    return OptimizationConfig(
        study_name=study_name,
        n_trials=n_trials,
        objectives=objectives,
        output_dir=output_dir
    )


# Example usage and testing
if __name__ == "__main__":
    print("Testing Advanced Hyperparameter Optimization...")

    if OPTUNA_AVAILABLE and TORCH_AVAILABLE:
        # Create test configuration
        config = OptimizationConfig(
            study_name="test_optimization",
            n_trials=5,
            max_epochs_per_trial=3,
            output_dir="/tmp/test_optimization"
        )

        print(f"Created optimization config: {config.study_name}")
        print(f"Objectives: {config.objectives}")
        print(f"Number of trials: {config.n_trials}")

        # Initialize optimizer
        optimizer = AdvancedOptimizer(config)
        print("Advanced optimizer initialized")

        # Test parameter space definition
        if OPTUNA_AVAILABLE:
            study = optuna.create_study()
            trial = study.ask()
            params = optimizer.define_parameter_space(trial)
            print(f"Generated {len(params)} parameters")
            print(f"Sample parameters: {list(params.keys())[:5]}")

        print("Advanced optimization tests completed successfully!")
    else:
        print("Optuna or PyTorch not available - skipping optimization tests")
        print("Optuna or PyTorch not available - skipping optimization tests")
