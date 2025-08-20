#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Advanced Loss Functions Integration Example

This example demonstrates how to integrate the advanced loss functions
with the hyperparameter optimization framework for medical image segmentation.
It shows practical usage patterns and optimization strategies.

Example workflows:
1. Single loss optimization
2. Multi-objective loss optimization
3. Curriculum learning with adaptive losses
4. Domain-specific optimization
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from typing import Any, Dict, List

import numpy as np
import torch.nn as nn

# Import loss functions and configuration
from losses import (AdaptiveLossWeighting, BoundaryLoss, CombinedLoss,
                    FocalLoss, TopKLoss, TverskyLoss)
from losses.loss_config import (LossConfig, create_loss_from_config,
                                get_recommended_config)
# Import optimization framework
from optimization import OptunaTuner


class AdvancedLossOptimization:
    """
    Advanced loss function optimization for medical segmentation.

    Integrates state-of-the-art loss functions with hyperparameter
    optimization for systematic performance improvement.
    """

    def __init__(
        self,
        study_name: str = "advanced_loss_optimization",
        storage_url: str = "sqlite:///advanced_loss_study.db"
    ):
        """
        Initialize advanced loss optimization.

        Args:
            study_name: Name of the optimization study
            storage_url: Storage URL for optimization results
        """
        self.study_name = study_name
        self.storage_url = storage_url
        self.tuner = None

        # Loss function registry
        self.loss_registry = {
            "focal": self._create_focal_objective,
            "tversky": self._create_tversky_objective,
            "combined": self._create_combined_objective,
            "boundary": self._create_boundary_objective,
            "topk": self._create_topk_objective,
            "adaptive": self._create_adaptive_objective
        }

    def optimize_single_loss(
        self,
        loss_type: str,
        n_trials: int = 100,
        direction: str = "maximize"
    ) -> Dict[str, Any]:
        """
        Optimize a single loss function type.

        Args:
            loss_type: Type of loss to optimize
            n_trials: Number of optimization trials
            direction: Optimization direction

        Returns:
            Optimization results
        """
        print(f"Optimizing {loss_type} loss function...")

        # Get loss-specific search space
        search_space = self._get_loss_search_space(loss_type)

        # Create tuner
        self.tuner = OptunaTuner(
            study_name=f"{self.study_name}_{loss_type}",
            direction=direction,
            storage_url=self.storage_url
        )

        # Create objective function
        objective_func = self.loss_registry[loss_type](search_space)

        # Run optimization
        best_params = self.tuner.optimize(
            objective=objective_func,
            n_trials=n_trials,
            timeout=None
        )

        return {
            "loss_type": loss_type,
            "best_params": best_params,
            "study_results": self.tuner.get_study_results()
        }

    def optimize_multi_objective_loss(
        self,
        loss_components: List[str],
        objectives: List[str] = ["dice_score", "hausdorff_distance"],
        n_trials: int = 200
    ) -> Dict[str, Any]:
        """
        Optimize multi-objective loss combination.

        Args:
            loss_components: List of loss components to combine
            objectives: List of objectives to optimize
            n_trials: Number of optimization trials

        Returns:
            Multi-objective optimization results
        """
        print(f"Multi-objective optimization with {loss_components}...")

        # Create multi-objective search space
        search_space = self._create_multi_objective_space(loss_components)

        # Create multi-objective tuner
        self.tuner = OptunaTuner(
            study_name=f"{self.study_name}_multi_objective",
            direction=["maximize", "minimize"],  # dice_score, hausdorff_distance
            storage_url=self.storage_url,
            multi_objective=True
        )

        # Create multi-objective function
        def multi_objective_func(trial):
            # Sample loss configuration
            loss_config = self._sample_multi_loss_config(trial, loss_components, search_space)

            # Create combined loss
            combined_loss = self._create_combined_loss_from_config(loss_config)

            # Simulate training and evaluation
            results = self._simulate_training_evaluation(combined_loss)

            return results["dice_score"], results["hausdorff_distance"]

        # Run optimization
        best_params = self.tuner.optimize(
            objective=multi_objective_func,
            n_trials=n_trials
        )

        return {
            "loss_components": loss_components,
            "objectives": objectives,
            "pareto_front": self.tuner.get_pareto_front(),
            "best_solutions": best_params
        }

    def curriculum_loss_optimization(
        self,
        curriculum_stages: List[Dict[str, Any]],
        n_trials: int = 150
    ) -> Dict[str, Any]:
        """
        Optimize curriculum learning with adaptive loss scheduling.

        Args:
            curriculum_stages: Curriculum learning stages
            n_trials: Number of optimization trials

        Returns:
            Curriculum optimization results
        """
        print("Optimizing curriculum learning strategy...")

        # Create curriculum-specific search space
        search_space = self._create_curriculum_search_space(curriculum_stages)

        # Create tuner
        self.tuner = OptunaTuner(
            study_name=f"{self.study_name}_curriculum",
            direction="maximize",
            storage_url=self.storage_url
        )

        def curriculum_objective(trial):
            # Sample curriculum parameters
            curriculum_config = self._sample_curriculum_config(trial, search_space)

            # Create curriculum scheduler
            scheduler = self._create_curriculum_scheduler(curriculum_config)

            # Simulate curriculum training
            results = self._simulate_curriculum_training(scheduler)

            return results["final_score"]

        # Run optimization
        best_params = self.tuner.optimize(
            objective=curriculum_objective,
            n_trials=n_trials
        )

        return {
            "curriculum_stages": curriculum_stages,
            "best_curriculum": best_params,
            "learning_curves": self.tuner.get_optimization_history()
        }

    def domain_specific_optimization(
        self,
        domain: str,
        data_characteristics: Dict[str, Any],
        n_trials: int = 100
    ) -> Dict[str, Any]:
        """
        Domain-specific loss optimization.

        Args:
            domain: Medical domain (brain, cardiac, liver, etc.)
            data_characteristics: Characteristics of the dataset
            n_trials: Number of optimization trials

        Returns:
            Domain-specific optimization results
        """
        print(f"Domain-specific optimization for {domain}...")

        # Get recommended configuration
        recommended_config = get_recommended_config(domain, data_characteristics)
        base_config = LossConfig.get_config(recommended_config)

        print(f"Using base configuration: {recommended_config}")

        # Create domain-specific search space
        search_space = self._create_domain_search_space(domain, base_config)

        # Create tuner
        self.tuner = OptunaTuner(
            study_name=f"{self.study_name}_{domain}",
            direction="maximize",
            storage_url=self.storage_url
        )

        def domain_objective(trial):
            # Sample parameters around recommended configuration
            sampled_config = self._sample_domain_config(trial, base_config, search_space)

            # Create loss function
            loss_func = create_loss_from_config(sampled_config)

            # Simulate domain-specific evaluation
            results = self._simulate_domain_evaluation(loss_func, domain, data_characteristics)

            return results["domain_score"]

        # Run optimization
        best_params = self.tuner.optimize(
            objective=domain_objective,
            n_trials=n_trials
        )

        return {
            "domain": domain,
            "base_config": recommended_config,
            "best_params": best_params,
            "improvement": self._calculate_improvement(base_config, best_params)
        }

    def _get_loss_search_space(self, loss_type: str) -> Dict[str, Any]:
        """Get search space for specific loss type."""
        spaces = {
            "focal": LossConfig.get_search_space("focal_search"),
            "tversky": LossConfig.get_search_space("tversky_search"),
            "combined": LossConfig.get_search_space("combined_search"),
            "topk": LossConfig.get_search_space("topk_search")
        }

        return spaces.get(loss_type, {})

    def _create_focal_objective(self, search_space: Dict[str, Any]) -> callable:
        """Create objective function for focal loss optimization."""
        def objective(trial):
            # Sample focal loss parameters
            alpha = trial.suggest_float("alpha", 0.1, 0.9, step=0.05)
            gamma = trial.suggest_float("gamma", 1.0, 5.0, step=0.5)

            # Create focal loss
            focal_loss = FocalLoss(alpha=alpha, gamma=gamma)

            # Simulate training
            results = self._simulate_training_evaluation(focal_loss)

            return results["dice_score"]

        return objective

    def _create_tversky_objective(self, search_space: Dict[str, Any]) -> callable:
        """Create objective function for Tversky loss optimization."""
        def objective(trial):
            # Sample Tversky parameters
            alpha = trial.suggest_float("alpha", 0.1, 0.9, step=0.1)
            beta = trial.suggest_float("beta", 0.1, 0.9, step=0.1)

            # Create Tversky loss
            tversky_loss = TverskyLoss(alpha=alpha, beta=beta)

            # Simulate training
            results = self._simulate_training_evaluation(tversky_loss)

            return results["dice_score"]

        return objective

    def _create_combined_objective(self, search_space: Dict[str, Any]) -> callable:
        """Create objective function for combined loss optimization."""
        def objective(trial):
            # Sample combination weights
            dice_weight = trial.suggest_float("dice_weight", 0.1, 0.9, step=0.1)
            focal_weight = 1.0 - dice_weight

            # Sample focal parameters
            focal_alpha = trial.suggest_float("focal_alpha", 0.1, 0.9, step=0.05)
            focal_gamma = trial.suggest_float("focal_gamma", 1.0, 4.0, step=0.5)

            # Create combined loss
            combined_loss = CombinedLoss(
                losses=[
                    ("dice", nn.CrossEntropyLoss(), dice_weight),
                    ("focal", FocalLoss(alpha=focal_alpha, gamma=focal_gamma), focal_weight)
                ]
            )

            # Simulate training
            results = self._simulate_training_evaluation(combined_loss)

            return results["dice_score"]

        return objective

    def _create_boundary_objective(self, search_space: Dict[str, Any]) -> callable:
        """Create objective function for boundary loss optimization."""
        def objective(trial):
            # Sample boundary loss parameters
            boundary_weight = trial.suggest_float("boundary_weight", 0.1, 2.0, step=0.1)
            distance_threshold = trial.suggest_float("distance_threshold", 1.0, 10.0, step=1.0)

            # Create boundary loss
            boundary_loss = BoundaryLoss(
                boundary_weight=boundary_weight,
                distance_threshold=distance_threshold
            )

            # Simulate training
            results = self._simulate_training_evaluation(boundary_loss)

            return results["dice_score"]

        return objective

    def _create_topk_objective(self, search_space: Dict[str, Any]) -> callable:
        """Create objective function for Top-K loss optimization."""
        def objective(trial):
            # Sample Top-K parameters
            k_ratio = trial.suggest_float("k_ratio", 0.3, 0.9, step=0.1)
            adaptive = trial.suggest_categorical("adaptive", [True, False])

            # Create Top-K loss
            base_loss = nn.CrossEntropyLoss()
            topk_loss = TopKLoss(base_loss=base_loss, k=k_ratio, adaptive_k=adaptive)

            # Simulate training
            results = self._simulate_training_evaluation(topk_loss)

            return results["dice_score"]

        return objective

    def _create_adaptive_objective(self, search_space: Dict[str, Any]) -> callable:
        """Create objective function for adaptive loss weighting."""
        def objective(trial):
            # Sample adaptive weighting parameters
            adaptation_rate = trial.suggest_float("adaptation_rate", 0.01, 0.5, step=0.01)
            temperature = trial.suggest_float("temperature", 1.0, 5.0, step=0.5)

            # Create adaptive weighting
            loss_names = ["dice", "focal", "boundary"]
            adaptive_weighter = AdaptiveLossWeighting(
                loss_names=loss_names,
                adaptation_rate=adaptation_rate,
                temperature=temperature
            )

            # Simulate adaptive training
            results = self._simulate_adaptive_training(adaptive_weighter)

            return results["final_score"]

        return objective

    def _simulate_training_evaluation(self, loss_func: nn.Module) -> Dict[str, float]:
        """
        Simulate training and evaluation for a loss function.

        Args:
            loss_func: Loss function to evaluate

        Returns:
            Simulated performance metrics
        """
        # This would normally involve actual training and evaluation
        # For demonstration, we return simulated scores

        # Simulate based on loss function characteristics
        if hasattr(loss_func, 'alpha') and hasattr(loss_func, 'gamma'):
            # Focal loss - performance depends on alpha/gamma balance
            base_score = 0.85
            alpha_factor = 1.0 - abs(loss_func.alpha - 0.25) * 0.5
            gamma_factor = 1.0 - abs(loss_func.gamma - 2.0) * 0.1
            dice_score = base_score * alpha_factor * gamma_factor
        elif hasattr(loss_func, 'alpha') and hasattr(loss_func, 'beta'):
            # Tversky loss - performance depends on alpha/beta balance
            base_score = 0.83
            balance_factor = 1.0 - abs((loss_func.alpha + loss_func.beta) - 1.0) * 0.3
            dice_score = base_score * balance_factor
        else:
            # Default simulation
            dice_score = np.random.uniform(0.75, 0.90)

        # Add some noise
        dice_score += np.random.normal(0, 0.02)
        dice_score = np.clip(dice_score, 0.0, 1.0)

        return {
            "dice_score": dice_score,
            "hausdorff_distance": 95 - dice_score * 100,  # Inverse relationship
            "sensitivity": dice_score + np.random.normal(0, 0.01),
            "specificity": dice_score + np.random.normal(0, 0.01)
        }

    def _simulate_curriculum_training(self, scheduler) -> Dict[str, float]:
        """Simulate curriculum learning training."""
        # Simulate progressive improvement through curriculum stages
        final_score = np.random.uniform(0.87, 0.93)
        return {"final_score": final_score}

    def _simulate_domain_evaluation(
        self,
        loss_func: nn.Module,
        domain: str,
        data_characteristics: Dict[str, Any]
    ) -> Dict[str, float]:
        """Simulate domain-specific evaluation."""
        # Domain-specific baseline scores
        domain_baselines = {
            "brain": 0.85,
            "cardiac": 0.82,
            "liver": 0.78
        }

        base_score = domain_baselines.get(domain.split("_")[0], 0.80)
        domain_score = base_score + np.random.uniform(-0.05, 0.10)

        return {"domain_score": domain_score}

    def _simulate_adaptive_training(self, adaptive_weighter) -> Dict[str, float]:
        """Simulate adaptive loss weighting training."""
        final_score = np.random.uniform(0.86, 0.92)
        return {"final_score": final_score}


def run_comprehensive_loss_optimization():
    """Run comprehensive loss function optimization example."""

    print("=== Advanced Loss Function Optimization ===\n")

    optimizer = AdvancedLossOptimization()

    # 1. Single loss optimization
    print("1. Single Loss Optimization")
    print("-" * 40)

    focal_results = optimizer.optimize_single_loss("focal", n_trials=50)
    print(f"Best Focal Loss parameters: {focal_results['best_params']}")

    tversky_results = optimizer.optimize_single_loss("tversky", n_trials=50)
    print(f"Best Tversky Loss parameters: {tversky_results['best_params']}")

    # 2. Multi-objective optimization
    print("\n2. Multi-Objective Optimization")
    print("-" * 40)

    multi_results = optimizer.optimize_multi_objective_loss(
        loss_components=["dice", "focal", "boundary"],
        n_trials=100
    )
    print(f"Pareto front size: {len(multi_results['pareto_front'])}")

    # 3. Domain-specific optimization
    print("\n3. Domain-Specific Optimization")
    print("-" * 40)

    brain_results = optimizer.domain_specific_optimization(
        domain="brain_tumor",
        data_characteristics={
            "class_imbalance": "severe",
            "boundary_complexity": "high",
            "num_classes": 4
        },
        n_trials=75
    )
    print(f"Brain tumor optimization completed: {brain_results['domain']}")
    print(f"Performance improvement: {brain_results['improvement']:.2%}")

    # 4. Configuration examples
    print("\n4. Configuration Examples")
    print("-" * 40)

    # Show available configurations
    configs = LossConfig.list_available_configs()
    print("Available configurations:")
    for category, names in configs.items():
        print(f"  {category}: {names}")

    # Example configuration usage
    dice_focal_config = LossConfig.get_config("dice_focal")
    print(f"\nDice-Focal configuration: {dice_focal_config}")

    print("\n=== Optimization Complete ===")


if __name__ == "__main__":
    # Run the comprehensive optimization example
    run_comprehensive_loss_optimization()

    print("\nAdvanced loss function optimization example completed!")
    print("This demonstrates integration of:")
    print("- Advanced loss functions (Focal, Tversky, Boundary, etc.)")
    print("- Hyperparameter optimization with Optuna")
    print("- Multi-objective optimization")
    print("- Domain-specific configurations")
    print("- Curriculum learning strategies")
    print("- Adaptive loss weighting")

    print("\nAdvanced loss function optimization example completed!")
    print("This demonstrates integration of:")
    print("- Advanced loss functions (Focal, Tversky, Boundary, etc.)")
    print("- Hyperparameter optimization with Optuna")
    print("- Multi-objective optimization")
    print("- Domain-specific configurations")
    print("- Curriculum learning strategies")
    print("- Adaptive loss weighting")
