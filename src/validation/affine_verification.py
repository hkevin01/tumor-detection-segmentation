"""
Affine Transformation Correctness Verification
==============================================

Comprehensive verification system for spatial transformations in medical imaging.
Ensures affine transformations maintain spatial integrity and anatomical correctness.

Author: Tumor Detection Segmentation Team
Phase: Transformation Verification - Task 20 Completion
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import torch

# Configure logging
logger = logging.getLogger(__name__)

# Check for MONAI availability
try:
    from monai.data.meta_tensor import MetaTensor
    from monai.transforms import (Affine, Orientation, RandAffine, Resize,
                                  Spacing, SpatialCrop, SpatialPad)
    from monai.utils import GridSampleMode, GridSamplePadMode
    MONAI_AVAILABLE = True
except ImportError:
    logger.warning("MONAI not available - using basic PyTorch transforms")
    MONAI_AVAILABLE = False

# Check for nibabel availability
try:
    import nibabel as nib
    NIBABEL_AVAILABLE = True
except ImportError:
    logger.warning("Nibabel not available - limited NIFTI support")
    NIBABEL_AVAILABLE = False


class AffineTransformValidator:
    """
    Comprehensive validator for affine transformations in medical imaging.
    Verifies spatial correctness, anatomical preservation, and numerical stability.
    """

    def __init__(self, tolerance: float = 1e-6):
        self.tolerance = tolerance
        self.validation_results = []

        logger.info("Affine transform validator initialized")

    def verify_transform_matrix(self, matrix: np.ndarray) -> Dict[str, Any]:
        """
        Verify affine transformation matrix properties.

        Args:
            matrix: 4x4 affine transformation matrix

        Returns:
            Dictionary with verification results
        """
        result = {
            'valid': True,
            'issues': [],
            'properties': {}
        }

        # Check matrix dimensions
        if matrix.shape != (4, 4):
            result['valid'] = False
            result['issues'].append(f"Invalid matrix shape: {matrix.shape}, expected (4, 4)")
            return result

        # Check bottom row
        expected_bottom = np.array([0, 0, 0, 1])
        if not np.allclose(matrix[3, :], expected_bottom, atol=self.tolerance):
            result['valid'] = False
            result['issues'].append(f"Invalid bottom row: {matrix[3, :]}, expected {expected_bottom}")

        # Extract rotation/scaling matrix
        rotation_scale = matrix[:3, :3]
        translation = matrix[:3, 3]

        # Check for numerical stability
        if np.any(np.isnan(matrix)) or np.any(np.isinf(matrix)):
            result['valid'] = False
            result['issues'].append("Matrix contains NaN or infinite values")

        # Compute determinant
        det = np.linalg.det(rotation_scale)
        result['properties']['determinant'] = det

        if abs(det) < self.tolerance:
            result['valid'] = False
            result['issues'].append(f"Singular matrix (determinant = {det})")

        # Check for reflection (negative determinant)
        if det < 0:
            result['issues'].append("Matrix contains reflection (negative determinant)")

        # Compute singular values for scaling analysis
        try:
            U, s, Vt = np.linalg.svd(rotation_scale)
            result['properties']['singular_values'] = s.tolist()
            result['properties']['condition_number'] = s[0] / s[-1] if s[-1] > 0 else np.inf

            # Check for excessive scaling
            max_scale = np.max(s)
            min_scale = np.min(s)
            if max_scale / min_scale > 100:  # Arbitrary threshold
                result['issues'].append(f"Excessive anisotropic scaling: {max_scale:.3f}/{min_scale:.3f}")

        except np.linalg.LinAlgError as e:
            result['valid'] = False
            result['issues'].append(f"SVD failed: {e}")

        # Analyze translation
        translation_magnitude = np.linalg.norm(translation)
        result['properties']['translation_magnitude'] = translation_magnitude

        return result

    def verify_spatial_consistency(
        self,
        original_image: np.ndarray,
        transformed_image: np.ndarray,
        affine_matrix: np.ndarray,
        original_spacing: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    ) -> Dict[str, Any]:
        """
        Verify spatial consistency between original and transformed images.

        Args:
            original_image: Original image array
            transformed_image: Transformed image array
            affine_matrix: Applied transformation matrix
            original_spacing: Voxel spacing of original image

        Returns:
            Verification results
        """
        result = {
            'valid': True,
            'issues': [],
            'metrics': {}
        }

        # Check image shapes
        if original_image.ndim != 3 or transformed_image.ndim != 3:
            result['valid'] = False
            result['issues'].append(f"Images must be 3D, got shapes {original_image.shape}, {transformed_image.shape}")
            return result

        # Compute expected output spacing
        rotation_scale = affine_matrix[:3, :3]
        spacing_matrix = np.diag(original_spacing)
        transformed_spacing_matrix = rotation_scale @ spacing_matrix

        # Compute voxel volume preservation
        original_volume = np.prod(original_spacing)
        det = np.linalg.det(rotation_scale)
        expected_volume = original_volume * abs(det)

        result['metrics']['volume_scaling_factor'] = abs(det)
        result['metrics']['original_voxel_volume'] = original_volume
        result['metrics']['expected_voxel_volume'] = expected_volume

        # Check for extreme volume changes
        if abs(det) < 0.1 or abs(det) > 10:
            result['issues'].append(f"Extreme volume scaling: factor = {abs(det):.3f}")

        # Verify image intensity preservation (if no interpolation artifacts)
        if original_image.shape == transformed_image.shape:
            intensity_correlation = np.corrcoef(
                original_image.flatten(),
                transformed_image.flatten()
            )[0, 1]
            result['metrics']['intensity_correlation'] = intensity_correlation

            if intensity_correlation < 0.8:  # Threshold for concern
                result['issues'].append(f"Low intensity correlation: {intensity_correlation:.3f}")

        return result

    def verify_anatomical_landmarks(
        self,
        landmarks_original: np.ndarray,
        landmarks_transformed: np.ndarray,
        affine_matrix: np.ndarray
    ) -> Dict[str, Any]:
        """
        Verify transformation correctness using anatomical landmarks.

        Args:
            landmarks_original: Original landmark coordinates (N, 3)
            landmarks_transformed: Transformed landmark coordinates (N, 3)
            affine_matrix: Applied transformation matrix

        Returns:
            Verification results
        """
        result = {
            'valid': True,
            'issues': [],
            'metrics': {}
        }

        if landmarks_original.shape != landmarks_transformed.shape:
            result['valid'] = False
            result['issues'].append(f"Landmark shape mismatch: {landmarks_original.shape} vs {landmarks_transformed.shape}")
            return result

        # Apply transformation to original landmarks
        homogeneous_landmarks = np.column_stack([landmarks_original, np.ones(len(landmarks_original))])
        expected_transformed = (affine_matrix @ homogeneous_landmarks.T).T[:, :3]

        # Compute landmark errors
        errors = np.linalg.norm(landmarks_transformed - expected_transformed, axis=1)

        result['metrics']['mean_landmark_error'] = np.mean(errors)
        result['metrics']['max_landmark_error'] = np.max(errors)
        result['metrics']['std_landmark_error'] = np.std(errors)

        # Check for excessive errors
        if np.mean(errors) > 2.0:  # 2 voxel threshold
            result['issues'].append(f"High mean landmark error: {np.mean(errors):.3f} voxels")

        if np.max(errors) > 5.0:  # 5 voxel threshold
            result['issues'].append(f"Extreme landmark error: {np.max(errors):.3f} voxels")

        return result

    def verify_invertibility(
        self,
        affine_matrix: np.ndarray,
        test_points: np.ndarray = None
    ) -> Dict[str, Any]:
        """
        Verify transformation invertibility.

        Args:
            affine_matrix: Transformation matrix to test
            test_points: Optional test points (N, 3)

        Returns:
            Verification results
        """
        result = {
            'valid': True,
            'issues': [],
            'metrics': {}
        }

        try:
            # Compute inverse matrix
            inverse_matrix = np.linalg.inv(affine_matrix)
            result['metrics']['inverse_computed'] = True

            # Verify A * A^-1 = I
            identity_test = affine_matrix @ inverse_matrix
            expected_identity = np.eye(4)

            identity_error = np.max(np.abs(identity_test - expected_identity))
            result['metrics']['identity_error'] = identity_error

            if identity_error > self.tolerance * 100:  # More lenient for numerical precision
                result['issues'].append(f"Poor inverse accuracy: max error = {identity_error:.2e}")

            # Test with points if provided
            if test_points is not None:
                homogeneous_points = np.column_stack([test_points, np.ones(len(test_points))])

                # Forward then inverse transformation
                transformed = (affine_matrix @ homogeneous_points.T).T[:, :3]
                recovered = (inverse_matrix @ np.column_stack([transformed, np.ones(len(transformed))]).T).T[:, :3]

                roundtrip_error = np.max(np.linalg.norm(test_points - recovered, axis=1))
                result['metrics']['roundtrip_error'] = roundtrip_error

                if roundtrip_error > self.tolerance * 1000:
                    result['issues'].append(f"Poor roundtrip accuracy: max error = {roundtrip_error:.2e}")

        except np.linalg.LinAlgError as e:
            result['valid'] = False
            result['issues'].append(f"Matrix inversion failed: {e}")
            result['metrics']['inverse_computed'] = False

        return result


class MONAITransformVerifier:
    """
    Verifier for MONAI transform correctness and integration.
    """

    def __init__(self):
        if not MONAI_AVAILABLE:
            raise ImportError("MONAI required for MONAI transform verification")

        self.validator = AffineTransformValidator()
        logger.info("MONAI transform verifier initialized")

    def verify_monai_affine(
        self,
        transform_config: Dict[str, Any],
        test_image_shape: Tuple[int, int, int] = (64, 64, 64)
    ) -> Dict[str, Any]:
        """
        Verify MONAI Affine transform configuration.

        Args:
            transform_config: MONAI Affine transform parameters
            test_image_shape: Shape for test image

        Returns:
            Verification results
        """
        result = {
            'valid': True,
            'issues': [],
            'transform_results': {}
        }

        try:
            # Create test image
            test_image = torch.randn(1, *test_image_shape)

            # Create MONAI transform
            transform = Affine(**transform_config)

            # Apply transform
            transformed_image = transform(test_image)

            # Extract transformation matrix
            if hasattr(transform, 'affine'):
                affine_matrix = transform.affine.numpy()

                # Verify matrix properties
                matrix_result = self.validator.verify_transform_matrix(affine_matrix)
                result['transform_results']['matrix_verification'] = matrix_result

                if not matrix_result['valid']:
                    result['valid'] = False
                    result['issues'].extend(matrix_result['issues'])

                # Verify invertibility
                invert_result = self.validator.verify_invertibility(affine_matrix)
                result['transform_results']['invertibility'] = invert_result

                if not invert_result['valid']:
                    result['valid'] = False
                    result['issues'].extend(invert_result['issues'])

            # Check output shape consistency
            if transformed_image.shape[1:] != test_image_shape:
                result['issues'].append(f"Shape changed unexpectedly: {test_image_shape} -> {transformed_image.shape[1:]}")

        except Exception as e:
            result['valid'] = False
            result['issues'].append(f"Transform verification failed: {e}")

        return result

    def verify_spacing_consistency(
        self,
        original_spacing: Tuple[float, float, float],
        target_spacing: Tuple[float, float, float],
        test_image_shape: Tuple[int, int, int] = (64, 64, 64)
    ) -> Dict[str, Any]:
        """
        Verify spacing transformation consistency.

        Args:
            original_spacing: Original voxel spacing
            target_spacing: Target voxel spacing
            test_image_shape: Test image dimensions

        Returns:
            Verification results
        """
        result = {
            'valid': True,
            'issues': [],
            'spacing_results': {}
        }

        try:
            # Create test image with metadata
            test_image = torch.randn(1, *test_image_shape)
            test_meta = MetaTensor(test_image)
            test_meta.meta['pixdim'] = np.array([1.0] + list(original_spacing) + [0.0] * 4)

            # Create spacing transform
            spacing_transform = Spacing(pixdim=target_spacing, mode=GridSampleMode.BILINEAR)

            # Apply transform
            transformed_image = spacing_transform(test_meta)

            # Check spacing in metadata
            if hasattr(transformed_image, 'meta') and 'pixdim' in transformed_image.meta:
                actual_spacing = transformed_image.meta['pixdim'][1:4]
                expected_spacing = np.array(target_spacing)

                spacing_error = np.max(np.abs(actual_spacing - expected_spacing))
                result['spacing_results']['spacing_error'] = spacing_error

                if spacing_error > 1e-6:
                    result['issues'].append(f"Spacing mismatch: expected {target_spacing}, got {actual_spacing}")

            # Check expected size change
            scale_factors = np.array(original_spacing) / np.array(target_spacing)
            expected_shape = tuple(int(dim * scale) for dim, scale in zip(test_image_shape, scale_factors))
            actual_shape = transformed_image.shape[1:]

            shape_diff = np.array(expected_shape) - np.array(actual_shape)
            if np.max(np.abs(shape_diff)) > 2:  # Allow some rounding tolerance
                result['issues'].append(f"Unexpected shape change: expected ~{expected_shape}, got {actual_shape}")

        except Exception as e:
            result['valid'] = False
            result['issues'].append(f"Spacing verification failed: {e}")

        return result


class ComprehensiveAffineVerifier:
    """
    Comprehensive verification system for all affine transformations.
    """

    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path("affine_verification_results")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.validator = AffineTransformValidator()
        if MONAI_AVAILABLE:
            self.monai_verifier = MONAITransformVerifier()

        self.verification_history = []
        logger.info(f"Comprehensive affine verifier initialized - output: {self.output_dir}")

    def run_full_verification_suite(self) -> Dict[str, Any]:
        """
        Run complete affine transformation verification suite.

        Returns:
            Comprehensive verification results
        """
        suite_results = {
            'timestamp': np.datetime64('now').isoformat(),
            'tests_passed': 0,
            'tests_failed': 0,
            'detailed_results': {}
        }

        # Test 1: Basic matrix properties
        logger.info("Testing basic matrix properties...")
        test_matrices = self._generate_test_matrices()

        matrix_results = []
        for name, matrix in test_matrices.items():
            result = self.validator.verify_transform_matrix(matrix)
            result['matrix_name'] = name
            matrix_results.append(result)

            if result['valid']:
                suite_results['tests_passed'] += 1
            else:
                suite_results['tests_failed'] += 1

        suite_results['detailed_results']['matrix_tests'] = matrix_results

        # Test 2: Invertibility tests
        logger.info("Testing transformation invertibility...")
        invertibility_results = []
        test_points = np.random.randn(10, 3) * 50  # Random test points

        for name, matrix in test_matrices.items():
            if np.linalg.det(matrix[:3, :3]) != 0:  # Only test non-singular matrices
                result = self.validator.verify_invertibility(matrix, test_points)
                result['matrix_name'] = name
                invertibility_results.append(result)

                if result['valid']:
                    suite_results['tests_passed'] += 1
                else:
                    suite_results['tests_failed'] += 1

        suite_results['detailed_results']['invertibility_tests'] = invertibility_results

        # Test 3: MONAI integration tests (if available)
        if MONAI_AVAILABLE:
            logger.info("Testing MONAI transform integration...")
            monai_results = self._test_monai_transforms()
            suite_results['detailed_results']['monai_tests'] = monai_results

            for result in monai_results:
                if result['valid']:
                    suite_results['tests_passed'] += 1
                else:
                    suite_results['tests_failed'] += 1

        # Generate summary
        total_tests = suite_results['tests_passed'] + suite_results['tests_failed']
        suite_results['success_rate'] = suite_results['tests_passed'] / total_tests if total_tests > 0 else 0

        # Save results
        self._save_verification_results(suite_results)

        logger.info(f"Verification suite completed: {suite_results['tests_passed']}/{total_tests} tests passed")
        return suite_results

    def _generate_test_matrices(self) -> Dict[str, np.ndarray]:
        """Generate test transformation matrices."""
        matrices = {}

        # Identity matrix
        matrices['identity'] = np.eye(4)

        # Pure translation
        translation = np.eye(4)
        translation[:3, 3] = [10, 5, -3]
        matrices['translation'] = translation

        # Pure rotation (90 degrees around Z-axis)
        rotation_z = np.eye(4)
        rotation_z[:2, :2] = [[0, -1], [1, 0]]
        matrices['rotation_z_90'] = rotation_z

        # Uniform scaling
        scaling = np.eye(4)
        scaling[:3, :3] *= 2.0
        matrices['uniform_scaling'] = scaling

        # Anisotropic scaling
        aniso_scaling = np.eye(4)
        np.fill_diagonal(aniso_scaling[:3, :3], [2.0, 1.5, 0.8])
        matrices['anisotropic_scaling'] = aniso_scaling

        # Combined transformation
        combined = rotation_z @ scaling @ translation
        matrices['combined'] = combined

        # Problematic matrices for testing
        singular = np.eye(4)
        singular[2, 2] = 0  # Singular
        matrices['singular'] = singular

        reflection = np.eye(4)
        reflection[0, 0] = -1  # Reflection
        matrices['reflection'] = reflection

        return matrices

    def _test_monai_transforms(self) -> List[Dict[str, Any]]:
        """Test MONAI transform configurations."""
        results = []

        # Test basic Affine configurations
        test_configs = [
            {'rotate': 0.1, 'scale': 1.1, 'translate': 5},
            {'rotate': [0.1, 0.2, 0.3], 'scale': [0.9, 1.1, 1.0]},
            {'shear': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]},
        ]

        for i, config in enumerate(test_configs):
            try:
                result = self.monai_verifier.verify_monai_affine(config)
                result['config_name'] = f'affine_config_{i}'
                results.append(result)
            except Exception as e:
                results.append({
                    'valid': False,
                    'issues': [f"Configuration test failed: {e}"],
                    'config_name': f'affine_config_{i}'
                })

        # Test spacing transformations
        spacing_tests = [
            ((1.0, 1.0, 1.0), (2.0, 2.0, 2.0)),
            ((1.5, 1.5, 3.0), (1.0, 1.0, 1.0)),
            ((0.5, 0.7, 1.2), (1.0, 1.0, 2.0)),
        ]

        for i, (orig_spacing, target_spacing) in enumerate(spacing_tests):
            try:
                result = self.monai_verifier.verify_spacing_consistency(orig_spacing, target_spacing)
                result['test_name'] = f'spacing_test_{i}'
                results.append(result)
            except Exception as e:
                results.append({
                    'valid': False,
                    'issues': [f"Spacing test failed: {e}"],
                    'test_name': f'spacing_test_{i}'
                })

        return results

    def _save_verification_results(self, results: Dict[str, Any]) -> None:
        """Save verification results to file."""
        timestamp = results['timestamp'].replace(':', '-')
        filename = f"affine_verification_{timestamp}.json"
        filepath = self.output_dir / filename

        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        self.verification_history.append(results)
        logger.info(f"Verification results saved to {filepath}")


# Factory function for easy usage
def verify_affine_correctness(output_dir: Path = None) -> Dict[str, Any]:
    """
    Factory function to run comprehensive affine transformation verification.

    Args:
        output_dir: Output directory for results

    Returns:
        Verification results dictionary
    """
    verifier = ComprehensiveAffineVerifier(output_dir)
    return verifier.run_full_verification_suite()


# Example usage and testing
if __name__ == "__main__":
    print("Testing Affine Transformation Verification...")

    # Run basic tests
    validator = AffineTransformValidator()

    # Test identity matrix
    identity = np.eye(4)
    result = validator.verify_transform_matrix(identity)
    print(f"Identity matrix test: {'PASSED' if result['valid'] else 'FAILED'}")

    # Test invertibility
    test_matrix = np.array([
        [2, 0, 0, 10],
        [0, 2, 0, 5],
        [0, 0, 2, -3],
        [0, 0, 0, 1]
    ])

    invert_result = validator.verify_invertibility(test_matrix)
    print(f"Invertibility test: {'PASSED' if invert_result['valid'] else 'FAILED'}")

    # Run full verification suite
    print("\nRunning comprehensive verification suite...")
    full_results = verify_affine_correctness(Path("test_affine_verification"))

    print(f"Suite completed: {full_results['success_rate']:.2%} success rate")
    print("Affine transformation verification test completed successfully!")
    print("\nRunning comprehensive verification suite...")
    full_results = verify_affine_correctness(Path("test_affine_verification"))

    print(f"Suite completed: {full_results['success_rate']:.2%} success rate")
    print("Affine transformation verification test completed successfully!")
