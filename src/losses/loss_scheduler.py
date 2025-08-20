#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Loss Schedulers and Adaptive Loss Weighting for Medical Image Segmentation

This module provides schedulers for dynamically adjusting loss function
parameters and weights during training. This is particularly useful for
medical segmentation where different loss components may need different
emphasis at different stages of training.

References:
- Curriculum learning approaches
- Adaptive loss weighting strategies
- Multi-task learning weight balancing
"""

import math
from typing import Dict, List, Optional, Union

import torch


class LossScheduler:
    """
    Base class for loss parameter scheduling.

    Provides infrastructure for dynamically adjusting loss function
    parameters during training based on epoch, iteration, or performance.
    """

    def __init__(
        self,
        initial_values: Dict[str, float],
        schedule_type: str = "cosine",
        total_steps: int = 1000,
        warmup_steps: int = 100
    ):
        """
        Initialize loss scheduler.

        Args:
            initial_values: Initial parameter values
            schedule_type: Type of schedule ('cosine', 'linear', 'exponential')
            total_steps: Total training steps
            warmup_steps: Warmup steps
        """
        self.initial_values = initial_values.copy()
        self.current_values = initial_values.copy()
        self.schedule_type = schedule_type
        self.total_steps = total_steps
        self.warmup_steps = warmup_steps
        self.step_count = 0

    def step(self) -> Dict[str, float]:
        """
        Update scheduler and return current parameter values.

        Returns:
            Current parameter values
        """
        self.step_count += 1

        # Calculate progress
        if self.step_count <= self.warmup_steps:
            progress = self.step_count / self.warmup_steps
            multiplier = progress  # Linear warmup
        else:
            remaining_steps = self.total_steps - self.warmup_steps
            current_step = self.step_count - self.warmup_steps
            progress = min(1.0, current_step / remaining_steps)
            multiplier = self._get_multiplier(progress)

        # Update current values
        for param_name, initial_value in self.initial_values.items():
            self.current_values[param_name] = initial_value * multiplier

        return self.current_values.copy()

    def _get_multiplier(self, progress: float) -> float:
        """Get multiplier based on schedule type and progress."""
        if self.schedule_type == "cosine":
            return 0.5 * (1 + math.cos(math.pi * progress))
        elif self.schedule_type == "linear":
            return 1.0 - progress
        elif self.schedule_type == "exponential":
            return math.exp(-5 * progress)
        else:
            return 1.0

    def get_current_values(self) -> Dict[str, float]:
        """Get current parameter values without stepping."""
        return self.current_values.copy()


class AdaptiveLossWeighting:
    """
    Adaptive loss weighting based on task performance.

    Automatically adjusts weights of different loss components based on
    their relative performance and convergence rates.
    """

    def __init__(
        self,
        loss_names: List[str],
        initial_weights: Optional[Dict[str, float]] = None,
        adaptation_rate: float = 0.1,
        temperature: float = 2.0,
        window_size: int = 10
    ):
        """
        Initialize adaptive loss weighting.

        Args:
            loss_names: Names of loss components
            initial_weights: Initial weights (uniform if None)
            adaptation_rate: Rate of weight adaptation
            temperature: Temperature for softmax weighting
            window_size: Window size for loss averaging
        """
        self.loss_names = loss_names
        self.adaptation_rate = adaptation_rate
        self.temperature = temperature
        self.window_size = window_size

        # Initialize weights
        if initial_weights is None:
            self.weights = {name: 1.0 / len(loss_names) for name in loss_names}
        else:
            self.weights = initial_weights.copy()

        # Loss history for adaptation
        self.loss_history = {name: [] for name in loss_names}
        self.weight_history = {name: [] for name in loss_names}

    def update_weights(self, loss_values: Dict[str, float]) -> Dict[str, float]:
        """
        Update weights based on current loss values.

        Args:
            loss_values: Current loss values for each component

        Returns:
            Updated weights
        """
        # Store loss values
        for name, value in loss_values.items():
            if name in self.loss_history:
                self.loss_history[name].append(value)
                if len(self.loss_history[name]) > self.window_size:
                    self.loss_history[name].pop(0)

        # Calculate relative loss rates
        if all(len(history) >= 2 for history in self.loss_history.values()):
            loss_rates = {}
            for name, history in self.loss_history.items():
                if len(history) >= self.window_size:
                    # Calculate improvement rate
                    recent_avg = sum(history[-self.window_size//2:]) / (self.window_size//2)
                    older_avg = sum(history[:self.window_size//2]) / (self.window_size//2)

                    if older_avg > 0:
                        improvement_rate = (older_avg - recent_avg) / older_avg
                        # Inverse relationship: slower improvement = higher weight
                        loss_rates[name] = 1.0 / (1.0 + improvement_rate)
                    else:
                        loss_rates[name] = 1.0
                else:
                    loss_rates[name] = 1.0

            # Convert to softmax weights
            raw_weights = [loss_rates[name] for name in self.loss_names]
            temperatures = [w / self.temperature for w in raw_weights]

            # Numerical stability
            max_temp = max(temperatures)
            exp_temps = [math.exp(t - max_temp) for t in temperatures]
            sum_exp = sum(exp_temps)

            new_weights = [exp_t / sum_exp for exp_t in exp_temps]

            # Update weights with momentum
            for i, name in enumerate(self.loss_names):
                self.weights[name] = (
                    (1 - self.adaptation_rate) * self.weights[name] +
                    self.adaptation_rate * new_weights[i]
                )

        # Store weight history
        for name in self.loss_names:
            self.weight_history[name].append(self.weights[name])

        return self.weights.copy()

    def get_weights(self) -> Dict[str, float]:
        """Get current weights."""
        return self.weights.copy()


class CurriculumLossScheduler:
    """
    Curriculum learning scheduler for gradually increasing task difficulty.

    Starts with easier examples/objectives and gradually introduces
    more challenging aspects as training progresses.
    """

    def __init__(
        self,
        curriculum_stages: List[Dict],
        stage_durations: List[int],
        transition_type: str = "smooth"
    ):
        """
        Initialize curriculum scheduler.

        Args:
            curriculum_stages: List of parameter sets for each stage
            stage_durations: Duration of each stage in steps
            transition_type: Type of transition ('smooth', 'hard')
        """
        self.curriculum_stages = curriculum_stages
        self.stage_durations = stage_durations
        self.transition_type = transition_type
        self.total_stages = len(curriculum_stages)

        self.current_stage = 0
        self.stage_progress = 0
        self.step_count = 0

        # Validate stages
        assert len(curriculum_stages) == len(stage_durations)

    def step(self) -> Dict[str, float]:
        """
        Update curriculum and return current parameters.

        Returns:
            Current parameter values
        """
        self.step_count += 1
        self.stage_progress += 1

        # Check if we should move to next stage
        if (self.stage_progress >= self.stage_durations[self.current_stage] and
            self.current_stage < self.total_stages - 1):
            self.current_stage += 1
            self.stage_progress = 0

        # Get current parameters
        if self.transition_type == "hard":
            return self.curriculum_stages[self.current_stage].copy()
        else:
            # Smooth transition
            return self._smooth_transition()

    def _smooth_transition(self) -> Dict[str, float]:
        """Smooth transition between curriculum stages."""
        current_params = self.curriculum_stages[self.current_stage]

        # If not in last stage and close to transition
        if (self.current_stage < self.total_stages - 1 and
            self.stage_progress >= self.stage_durations[self.current_stage] * 0.8):

            next_params = self.curriculum_stages[self.current_stage + 1]

            # Calculate interpolation factor
            transition_start = int(self.stage_durations[self.current_stage] * 0.8)
            transition_length = self.stage_durations[self.current_stage] - transition_start
            alpha = (self.stage_progress - transition_start) / transition_length
            alpha = max(0, min(1, alpha))

            # Interpolate parameters
            interpolated = {}
            for key in current_params:
                if key in next_params:
                    interpolated[key] = (
                        (1 - alpha) * current_params[key] +
                        alpha * next_params[key]
                    )
                else:
                    interpolated[key] = current_params[key]

            return interpolated

        return current_params.copy()


class MultiTaskLossBalancer:
    """
    Balancer for multi-task learning scenarios.

    Automatically balances loss weights across multiple tasks to ensure
    balanced learning and prevent task dominance.
    """

    def __init__(
        self,
        task_names: List[str],
        balancing_method: str = "uncertainty",
        initial_log_vars: Optional[Dict[str, float]] = None,
        lr_log_vars: float = 0.01
    ):
        """
        Initialize multi-task loss balancer.

        Args:
            task_names: Names of tasks
            balancing_method: Balancing method ('uncertainty', 'gradnorm', 'equal')
            initial_log_vars: Initial log variance values for uncertainty weighting
            lr_log_vars: Learning rate for log variance parameters
        """
        self.task_names = task_names
        self.balancing_method = balancing_method
        self.lr_log_vars = lr_log_vars

        # Initialize parameters based on method
        if balancing_method == "uncertainty":
            if initial_log_vars is None:
                self.log_vars = {name: 0.0 for name in task_names}
            else:
                self.log_vars = initial_log_vars.copy()
        else:
            self.weights = {name: 1.0 / len(task_names) for name in task_names}

        self.task_losses = {name: [] for name in task_names}
        self.gradients = {name: [] for name in task_names}

    def compute_weights(
        self,
        task_losses: Dict[str, torch.Tensor],
        gradients: Optional[Dict[str, torch.Tensor]] = None
    ) -> Dict[str, float]:
        """
        Compute task weights based on losses and optionally gradients.

        Args:
            task_losses: Current task losses
            gradients: Task gradients (for gradnorm method)

        Returns:
            Task weights
        """
        if self.balancing_method == "uncertainty":
            return self._uncertainty_weighting(task_losses)
        elif self.balancing_method == "gradnorm" and gradients is not None:
            return self._gradnorm_weighting(task_losses, gradients)
        else:
            # Equal weighting
            return {name: 1.0 / len(self.task_names) for name in self.task_names}

    def _uncertainty_weighting(
        self,
        task_losses: Dict[str, torch.Tensor]
    ) -> Dict[str, float]:
        """
        Uncertainty-based weighting using learned log variances.

        Args:
            task_losses: Task losses

        Returns:
            Uncertainty-based weights
        """
        weights = {}
        total_weighted_loss = 0

        for name in self.task_names:
            if name in task_losses:
                precision = torch.exp(-self.log_vars[name])
                weighted_loss = precision * task_losses[name] + self.log_vars[name]
                total_weighted_loss += weighted_loss.item()

                # Update log variance (simple gradient step)
                grad_log_var = 1 - precision * task_losses[name]
                self.log_vars[name] -= self.lr_log_vars * grad_log_var.item()

                weights[name] = precision.item()

        # Normalize weights
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {name: w / total_weight for name, w in weights.items()}

        return weights

    def _gradnorm_weighting(
        self,
        task_losses: Dict[str, torch.Tensor],
        gradients: Dict[str, torch.Tensor]
    ) -> Dict[str, float]:
        """
        GradNorm-based weighting for balanced gradient magnitudes.

        Args:
            task_losses: Task losses
            gradients: Task gradients

        Returns:
            GradNorm-based weights
        """
        # Calculate gradient norms
        grad_norms = {}
        for name, grad in gradients.items():
            grad_norms[name] = torch.norm(grad).item()

        # Calculate relative training rates
        loss_ratios = {}
        if len(self.task_losses[list(self.task_names)[0]]) > 1:
            for name in self.task_names:
                if len(self.task_losses[name]) >= 2:
                    current_loss = task_losses[name].item()
                    initial_loss = self.task_losses[name][0]
                    loss_ratios[name] = current_loss / (initial_loss + 1e-8)

        # Store current losses
        for name, loss in task_losses.items():
            self.task_losses[name].append(loss.item())

        # Compute target gradient norms
        if loss_ratios:
            avg_ratio = sum(loss_ratios.values()) / len(loss_ratios)
            target_grad_norms = {}
            avg_grad_norm = sum(grad_norms.values()) / len(grad_norms)

            for name in self.task_names:
                relative_rate = loss_ratios.get(name, 1.0) / avg_ratio
                target_grad_norms[name] = avg_grad_norm * (relative_rate ** 0.12)

            # Update weights based on gradient norm differences
            for name in self.task_names:
                if name in grad_norms and name in target_grad_norms:
                    ratio = target_grad_norms[name] / (grad_norms[name] + 1e-8)
                    self.weights[name] = max(0.1, min(10.0, ratio))

        # Normalize weights
        total_weight = sum(self.weights.values())
        return {name: w / total_weight for name, w in self.weights.items()}


def create_loss_scheduler(
    scheduler_type: str = "adaptive",
    **kwargs
) -> Union[LossScheduler, AdaptiveLossWeighting, CurriculumLossScheduler, MultiTaskLossBalancer]:
    """
    Factory function to create loss scheduler.

    Args:
        scheduler_type: Type of scheduler
        **kwargs: Additional arguments

    Returns:
        Configured scheduler instance
    """
    if scheduler_type == "parameter":
        return LossScheduler(**kwargs)
    elif scheduler_type == "adaptive":
        return AdaptiveLossWeighting(**kwargs)
    elif scheduler_type == "curriculum":
        return CurriculumLossScheduler(**kwargs)
    elif scheduler_type == "multitask":
        return MultiTaskLossBalancer(**kwargs)
    else:
        raise ValueError(f"Unknown scheduler type: {scheduler_type}")


# Example usage and testing
if __name__ == "__main__":
    import torch

    print("Testing Loss Schedulers...")

    # Test Parameter Scheduler
    print("\nTesting Parameter Scheduler...")
    param_scheduler = LossScheduler(
        initial_values={"alpha": 0.25, "gamma": 2.0},
        schedule_type="cosine",
        total_steps=100,
        warmup_steps=10
    )

    for i in range(5):
        values = param_scheduler.step()
        print(f"Step {i+1}: {values}")

    # Test Adaptive Loss Weighting
    print("\nTesting Adaptive Loss Weighting...")
    adaptive_weighter = AdaptiveLossWeighting(
        loss_names=["dice", "focal", "boundary"],
        adaptation_rate=0.1
    )

    for i in range(5):
        # Simulate different loss convergence rates
        loss_values = {
            "dice": 0.8 - i * 0.1,
            "focal": 0.6 - i * 0.05,
            "boundary": 0.4 - i * 0.02
        }
        weights = adaptive_weighter.update_weights(loss_values)
        print(f"Iteration {i+1}: {weights}")

    # Test Curriculum Scheduler
    print("\nTesting Curriculum Scheduler...")
    curriculum = CurriculumLossScheduler(
        curriculum_stages=[
            {"alpha": 0.5, "gamma": 1.0},  # Easy stage
            {"alpha": 0.25, "gamma": 2.0}, # Medium stage
            {"alpha": 0.1, "gamma": 3.0}   # Hard stage
        ],
        stage_durations=[10, 10, 10],
        transition_type="smooth"
    )

    for i in range(25):
        params = curriculum.step()
        if i % 5 == 0:
            print(f"Step {i+1}: {params}")

    # Test Multi-task Balancer
    print("\nTesting Multi-task Loss Balancer...")
    balancer = MultiTaskLossBalancer(
        task_names=["segmentation", "classification"],
        balancing_method="uncertainty"
    )

    for i in range(3):
        # Simulate task losses
        seg_loss = torch.tensor(0.8 - i * 0.2)
        cls_loss = torch.tensor(0.6 - i * 0.1)

        weights = balancer.compute_weights({
            "segmentation": seg_loss,
            "classification": cls_loss
        })
        print(f"Iteration {i+1}: {weights}")

    print("\nAll scheduler tests completed successfully!")
    print("\nAll scheduler tests completed successfully!")
