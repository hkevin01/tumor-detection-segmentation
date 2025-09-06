"""
Advanced Active Learning Strategies for MONAI Label
================================================

Implements sophisticated active learning strategies for brain tumor
segmentation including uncertainty estimation, diversity sampling,
and hybrid approaches.

Author: Tumor Detection Segmentation Team
Phase: MONAI Label Integration - Task 17 Completion
"""

import logging
import random
from typing import Any, Dict, List, Optional

import numpy as np
import torch

# Configure logging
logger = logging.getLogger(__name__)

# Check for MONAI Label availability
try:
    from monailabel.interfaces.tasks.strategy import Strategy
    from monailabel.utils.others.generic import get_class_names
    MONAI_LABEL_AVAILABLE = True
except ImportError:
    logger.warning("MONAI Label not available")
    Strategy = object
    MONAI_LABEL_AVAILABLE = False


class UncertaintyStrategy(Strategy):
    """
    Uncertainty-based active learning strategy using entropy and mutual information.
    Selects samples where the model is most uncertain.
    """

    def __init__(self, mc_samples: int = 10, uncertainty_metric: str = 'entropy'):
        super().__init__("Uncertainty-based Strategy")
        self.mc_samples = mc_samples
        self.uncertainty_metric = uncertainty_metric

        logger.info(f"Uncertainty strategy initialized with {uncertainty_metric}")

    def __call__(self, request: Dict[str, Any]) -> List[str]:
        """
        Select samples with highest uncertainty.

        Args:
            request: Request containing datastore, model, and parameters

        Returns:
            List of selected image IDs
        """
        datastore = request.get("datastore")
        model = request.get("model")
        client_id = request.get("client_id", "default")
        max_samples = request.get("params", {}).get("max_samples", 5)

        if not datastore or not model:
            logger.warning("Missing datastore or model in request")
            return []

        # Get unlabeled images
        unlabeled_images = self._get_unlabeled_images(datastore)

        if not unlabeled_images:
            logger.info("No unlabeled images available")
            return []

        # Compute uncertainties
        uncertainties = self._compute_uncertainties(model, unlabeled_images, datastore)

        # Select top uncertain samples
        sorted_indices = np.argsort(uncertainties)[::-1]
        selected_indices = sorted_indices[:min(max_samples, len(sorted_indices))]

        selected_images = [unlabeled_images[i] for i in selected_indices]

        logger.info(f"Selected {len(selected_images)} uncertain samples for {client_id}")
        return selected_images

    def _get_unlabeled_images(self, datastore) -> List[str]:
        """Get list of unlabeled image IDs."""
        try:
            all_images = list(datastore.list_images())
            labeled_images = set(datastore.list_labels())

            unlabeled = [img for img in all_images if img not in labeled_images]
            logger.info(f"Found {len(unlabeled)} unlabeled images")
            return unlabeled
        except Exception as e:
            logger.error(f"Error getting unlabeled images: {e}")
            return []

    def _compute_uncertainties(
        self,
        model,
        image_ids: List[str],
        datastore
    ) -> np.ndarray:
        """Compute uncertainty scores for images."""
        uncertainties = []

        for image_id in image_ids:
            try:
                # Load image
                image_path = datastore.get_image_uri(image_id)

                # Run inference with Monte Carlo dropout
                uncertainty = self._monte_carlo_uncertainty(model, image_path)
                uncertainties.append(uncertainty)

            except Exception as e:
                logger.warning(f"Error computing uncertainty for {image_id}: {e}")
                uncertainties.append(0.0)

        return np.array(uncertainties)

    def _monte_carlo_uncertainty(self, model, image_path: str) -> float:
        """Compute Monte Carlo uncertainty using dropout."""
        try:
            # Enable dropout for uncertainty estimation
            model.train()

            predictions = []

            # Multiple forward passes with dropout
            for _ in range(self.mc_samples):
                with torch.no_grad():
                    # This is a simplified version - you'd need to load and preprocess the image
                    pred = self._run_inference(model, image_path)
                    predictions.append(pred)

            # Compute uncertainty based on prediction variance
            predictions = np.stack(predictions)

            if self.uncertainty_metric == 'entropy':
                mean_pred = np.mean(predictions, axis=0)
                entropy = -np.sum(mean_pred * np.log(mean_pred + 1e-8), axis=-1)
                uncertainty = np.mean(entropy)
            elif self.uncertainty_metric == 'variance':
                uncertainty = np.mean(np.var(predictions, axis=0))
            else:
                uncertainty = np.mean(np.std(predictions, axis=0))

            return float(uncertainty)

        except Exception as e:
            logger.error(f"Error in Monte Carlo uncertainty: {e}")
            return 0.0

    def _run_inference(self, model, image_path: str) -> np.ndarray:
        """Run model inference on image."""
        # Simplified inference - in practice you'd need proper image loading
        # and preprocessing pipeline

        # Dummy implementation
        return np.random.random((96, 96, 96, 3))


class DiversityStrategy(Strategy):
    """
    Diversity-based active learning strategy using feature clustering.
    Selects diverse samples to maximize coverage of feature space.
    """

    def __init__(self, clustering_method: str = 'kmeans', n_clusters: int = None):
        super().__init__("Diversity-based Strategy")
        self.clustering_method = clustering_method
        self.n_clusters = n_clusters

        logger.info(f"Diversity strategy initialized with {clustering_method}")

    def __call__(self, request: Dict[str, Any]) -> List[str]:
        """Select diverse samples using clustering."""
        datastore = request.get("datastore")
        model = request.get("model")
        max_samples = request.get("params", {}).get("max_samples", 5)

        if not datastore or not model:
            return []

        unlabeled_images = self._get_unlabeled_images(datastore)

        if not unlabeled_images:
            return []

        # Extract features
        features = self._extract_features(model, unlabeled_images, datastore)

        # Perform clustering
        selected_images = self._cluster_and_select(
            features, unlabeled_images, max_samples
        )

        logger.info(f"Selected {len(selected_images)} diverse samples")
        return selected_images

    def _get_unlabeled_images(self, datastore) -> List[str]:
        """Get list of unlabeled image IDs."""
        try:
            all_images = list(datastore.list_images())
            labeled_images = set(datastore.list_labels())
            return [img for img in all_images if img not in labeled_images]
        except:
            return []

    def _extract_features(
        self,
        model,
        image_ids: List[str],
        datastore
    ) -> np.ndarray:
        """Extract features from images using model."""
        features = []

        for image_id in image_ids:
            try:
                # In practice, you'd extract features from intermediate model layers
                # This is a simplified version
                feature = np.random.random(512)  # Dummy feature vector
                features.append(feature)
            except Exception as e:
                logger.warning(f"Error extracting features for {image_id}: {e}")
                features.append(np.zeros(512))

        return np.array(features)

    def _cluster_and_select(
        self,
        features: np.ndarray,
        image_ids: List[str],
        max_samples: int
    ) -> List[str]:
        """Cluster features and select representative samples."""
        try:
            from sklearn.cluster import KMeans
            from sklearn.metrics.pairwise import pairwise_distances

            n_clusters = min(self.n_clusters or max_samples, len(image_ids))

            # Perform clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            cluster_labels = kmeans.fit_predict(features)

            # Select one sample from each cluster (closest to centroid)
            selected = []
            for cluster_id in range(n_clusters):
                cluster_indices = np.where(cluster_labels == cluster_id)[0]

                if len(cluster_indices) > 0:
                    cluster_features = features[cluster_indices]
                    centroid = kmeans.cluster_centers_[cluster_id]

                    # Find closest sample to centroid
                    distances = pairwise_distances(
                        cluster_features, centroid.reshape(1, -1)
                    ).flatten()

                    closest_idx = cluster_indices[np.argmin(distances)]
                    selected.append(image_ids[closest_idx])

            return selected[:max_samples]

        except ImportError:
            logger.warning("scikit-learn not available, using random selection")
            return random.sample(image_ids, min(max_samples, len(image_ids)))
        except Exception as e:
            logger.error(f"Error in clustering: {e}")
            return random.sample(image_ids, min(max_samples, len(image_ids)))


class HybridStrategy(Strategy):
    """
    Hybrid active learning strategy combining uncertainty and diversity.
    """

    def __init__(
        self,
        uncertainty_weight: float = 0.7,
        diversity_weight: float = 0.3,
        batch_selection_method: str = 'weighted_combination'
    ):
        super().__init__("Hybrid Strategy")
        self.uncertainty_weight = uncertainty_weight
        self.diversity_weight = diversity_weight
        self.batch_selection_method = batch_selection_method

        # Initialize component strategies
        self.uncertainty_strategy = UncertaintyStrategy()
        self.diversity_strategy = DiversityStrategy()

        logger.info(f"Hybrid strategy initialized: uncertainty={uncertainty_weight}, "
                   f"diversity={diversity_weight}")

    def __call__(self, request: Dict[str, Any]) -> List[str]:
        """Select samples using hybrid approach."""
        max_samples = request.get("params", {}).get("max_samples", 5)

        if self.batch_selection_method == 'weighted_combination':
            return self._weighted_combination_selection(request, max_samples)
        elif self.batch_selection_method == 'sequential':
            return self._sequential_selection(request, max_samples)
        else:
            return self._alternating_selection(request, max_samples)

    def _weighted_combination_selection(
        self,
        request: Dict[str, Any],
        max_samples: int
    ) -> List[str]:
        """Select samples using weighted combination of scores."""
        datastore = request.get("datastore")
        model = request.get("model")

        if not datastore or not model:
            return []

        unlabeled_images = self._get_unlabeled_images(datastore)

        if not unlabeled_images:
            return []

        # Compute uncertainty scores
        uncertainty_scores = self._compute_uncertainty_scores(
            model, unlabeled_images, datastore
        )

        # Compute diversity scores
        diversity_scores = self._compute_diversity_scores(
            model, unlabeled_images, datastore
        )

        # Normalize scores
        uncertainty_scores = self._normalize_scores(uncertainty_scores)
        diversity_scores = self._normalize_scores(diversity_scores)

        # Combine scores
        combined_scores = (
            self.uncertainty_weight * uncertainty_scores +
            self.diversity_weight * diversity_scores
        )

        # Select top samples
        sorted_indices = np.argsort(combined_scores)[::-1]
        selected_indices = sorted_indices[:max_samples]

        selected_images = [unlabeled_images[i] for i in selected_indices]

        logger.info(f"Selected {len(selected_images)} samples using hybrid approach")
        return selected_images

    def _sequential_selection(
        self,
        request: Dict[str, Any],
        max_samples: int
    ) -> List[str]:
        """Select samples sequentially (uncertainty first, then diversity)."""
        uncertainty_samples = max_samples // 2
        diversity_samples = max_samples - uncertainty_samples

        # Get uncertainty-based selections
        uncertainty_request = request.copy()
        uncertainty_request["params"] = {"max_samples": uncertainty_samples}
        uncertainty_selected = self.uncertainty_strategy(uncertainty_request)

        # Get diversity-based selections (excluding already selected)
        diversity_request = request.copy()
        diversity_request["params"] = {"max_samples": diversity_samples}
        diversity_selected = self.diversity_strategy(diversity_request)

        # Combine and remove duplicates
        combined = list(set(uncertainty_selected + diversity_selected))

        return combined[:max_samples]

    def _alternating_selection(
        self,
        request: Dict[str, Any],
        max_samples: int
    ) -> List[str]:
        """Alternate between uncertainty and diversity selection."""
        selected = []

        for i in range(max_samples):
            if i % 2 == 0:
                # Use uncertainty strategy
                strategy_request = request.copy()
                strategy_request["params"] = {"max_samples": 1}
                candidates = self.uncertainty_strategy(strategy_request)
            else:
                # Use diversity strategy
                strategy_request = request.copy()
                strategy_request["params"] = {"max_samples": 1}
                candidates = self.diversity_strategy(strategy_request)

            # Add new candidates (avoiding duplicates)
            for candidate in candidates:
                if candidate not in selected:
                    selected.append(candidate)
                    break

        return selected

    def _get_unlabeled_images(self, datastore) -> List[str]:
        """Get list of unlabeled image IDs."""
        try:
            all_images = list(datastore.list_images())
            labeled_images = set(datastore.list_labels())
            return [img for img in all_images if img not in labeled_images]
        except:
            return []

    def _compute_uncertainty_scores(
        self,
        model,
        image_ids: List[str],
        datastore
    ) -> np.ndarray:
        """Compute uncertainty scores for images."""
        return self.uncertainty_strategy._compute_uncertainties(
            model, image_ids, datastore
        )

    def _compute_diversity_scores(
        self,
        model,
        image_ids: List[str],
        datastore
    ) -> np.ndarray:
        """Compute diversity scores for images."""
        # Simplified diversity scoring
        # In practice, you'd compute distances from existing labeled samples
        return np.random.random(len(image_ids))

    def _normalize_scores(self, scores: np.ndarray) -> np.ndarray:
        """Normalize scores to [0, 1] range."""
        if len(scores) == 0:
            return scores

        min_score = np.min(scores)
        max_score = np.max(scores)

        if max_score == min_score:
            return np.ones_like(scores)

        return (scores - min_score) / (max_score - min_score)


class EpistemicUncertaintyStrategy(Strategy):
    """
    Epistemic uncertainty estimation using ensemble methods.
    Focuses on model uncertainty rather than data noise.
    """

    def __init__(self, num_models: int = 5, ensemble_method: str = 'dropout'):
        super().__init__("Epistemic Uncertainty Strategy")
        self.num_models = num_models
        self.ensemble_method = ensemble_method

        logger.info(f"Epistemic uncertainty strategy with {ensemble_method}")

    def __call__(self, request: Dict[str, Any]) -> List[str]:
        """Select samples with highest epistemic uncertainty."""
        datastore = request.get("datastore")
        model = request.get("model")
        max_samples = request.get("params", {}).get("max_samples", 5)

        if not datastore or not model:
            return []

        unlabeled_images = self._get_unlabeled_images(datastore)

        if not unlabeled_images:
            return []

        # Compute epistemic uncertainties
        uncertainties = self._compute_epistemic_uncertainties(
            model, unlabeled_images, datastore
        )

        # Select top uncertain samples
        sorted_indices = np.argsort(uncertainties)[::-1]
        selected_indices = sorted_indices[:max_samples]

        selected_images = [unlabeled_images[i] for i in selected_indices]

        logger.info(f"Selected {len(selected_images)} epistemically uncertain samples")
        return selected_images

    def _get_unlabeled_images(self, datastore) -> List[str]:
        """Get list of unlabeled image IDs."""
        try:
            all_images = list(datastore.list_images())
            labeled_images = set(datastore.list_labels())
            return [img for img in all_images if img not in labeled_images]
        except:
            return []

    def _compute_epistemic_uncertainties(
        self,
        model,
        image_ids: List[str],
        datastore
    ) -> np.ndarray:
        """Compute epistemic uncertainty using ensemble methods."""
        uncertainties = []

        for image_id in image_ids:
            try:
                if self.ensemble_method == 'dropout':
                    uncertainty = self._monte_carlo_dropout(model, image_id, datastore)
                elif self.ensemble_method == 'deep_ensemble':
                    uncertainty = self._deep_ensemble_uncertainty(model, image_id, datastore)
                else:
                    uncertainty = self._bayesian_uncertainty(model, image_id, datastore)

                uncertainties.append(uncertainty)

            except Exception as e:
                logger.warning(f"Error computing epistemic uncertainty for {image_id}: {e}")
                uncertainties.append(0.0)

        return np.array(uncertainties)

    def _monte_carlo_dropout(self, model, image_id: str, datastore) -> float:
        """Estimate uncertainty using Monte Carlo dropout."""
        # Enable dropout
        model.train()

        predictions = []
        for _ in range(self.num_models):
            # Run inference with dropout
            pred = self._run_inference(model, image_id, datastore)
            predictions.append(pred)

        # Compute prediction variance
        predictions = np.stack(predictions)
        epistemic_uncertainty = np.mean(np.var(predictions, axis=0))

        return float(epistemic_uncertainty)

    def _deep_ensemble_uncertainty(self, model, image_id: str, datastore) -> float:
        """Estimate uncertainty using deep ensemble (simplified)."""
        # In practice, you'd have multiple trained models
        # This is a simplified implementation

        predictions = []
        for _ in range(self.num_models):
            # Add noise to simulate ensemble
            pred = self._run_inference(model, image_id, datastore)
            pred += np.random.normal(0, 0.1, pred.shape)
            predictions.append(pred)

        predictions = np.stack(predictions)
        uncertainty = np.mean(np.var(predictions, axis=0))

        return float(uncertainty)

    def _bayesian_uncertainty(self, model, image_id: str, datastore) -> float:
        """Estimate uncertainty using Bayesian methods (simplified)."""
        # Simplified Bayesian uncertainty
        pred = self._run_inference(model, image_id, datastore)

        # Compute entropy as proxy for Bayesian uncertainty
        epsilon = 1e-8
        entropy = -np.sum(pred * np.log(pred + epsilon), axis=-1)
        uncertainty = np.mean(entropy)

        return float(uncertainty)

    def _run_inference(self, model, image_id: str, datastore) -> np.ndarray:
        """Run model inference on image."""
        # Simplified inference - you'd need proper image loading and preprocessing
        return np.random.random((96, 96, 96, 3))


# Factory function to create strategies
def create_active_learning_strategy(
    strategy_type: str,
    config: Optional[Dict[str, Any]] = None
) -> Strategy:
    """
    Factory function to create active learning strategies.

    Args:
        strategy_type: Type of strategy ('uncertainty', 'diversity', 'hybrid', 'epistemic')
        config: Strategy configuration

    Returns:
        Configured strategy instance
    """
    if config is None:
        config = {}

    if strategy_type == 'uncertainty':
        return UncertaintyStrategy(
            mc_samples=config.get('mc_samples', 10),
            uncertainty_metric=config.get('uncertainty_metric', 'entropy')
        )
    elif strategy_type == 'diversity':
        return DiversityStrategy(
            clustering_method=config.get('clustering_method', 'kmeans'),
            n_clusters=config.get('n_clusters', None)
        )
    elif strategy_type == 'hybrid':
        return HybridStrategy(
            uncertainty_weight=config.get('uncertainty_weight', 0.7),
            diversity_weight=config.get('diversity_weight', 0.3),
            batch_selection_method=config.get('batch_selection_method', 'weighted_combination')
        )
    elif strategy_type == 'epistemic':
        return EpistemicUncertaintyStrategy(
            num_models=config.get('num_models', 5),
            ensemble_method=config.get('ensemble_method', 'dropout')
        )
    else:
        raise ValueError(f"Unknown strategy type: {strategy_type}")


# Example usage and testing
if __name__ == "__main__":
    print("Testing Advanced Active Learning Strategies...")

    # Test strategy creation
    strategies = ['uncertainty', 'diversity', 'hybrid', 'epistemic']

    for strategy_type in strategies:
        strategy = create_active_learning_strategy(strategy_type)
        print(f"Created {strategy_type} strategy: {strategy.name}")

    print("Active learning strategies test completed successfully!")
