#!/usr/bin/env python3
"""
Quick fix for the inference.py file to add post-processing flags properly.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def add_postprocessing_to_inference():
    """Add post-processing capabilities to inference.py correctly."""

    inference_file = ROOT / "src/inference/inference.py"

    # Read the current file
    with open(inference_file, 'r') as f:
        content = f.read()

    # Fix any syntax issues first by checking for the imports
    if "from scipy import ndimage" not in content:
        # Add scipy imports after the numpy import
        scipy_import = '''try:
    from scipy import ndimage
    from scipy.ndimage import binary_fill_holes, label
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

'''
        # Find where to insert (after numpy import)
        numpy_line = content.find("import numpy as np")
        if numpy_line != -1:
            # Find the end of that line
            end_line = content.find('\n', numpy_line) + 1
            content = content[:end_line] + scipy_import + content[end_line:]

    # Add post-processing method to TumorPredictor class if not already there
    postproc_method = '''
    def apply_postprocessing(
        self,
        prediction: np.ndarray,
        fill_holes: bool = False,
        largest_component: bool = False,
        min_component_size: int = 100
    ) -> np.ndarray:
        """Apply morphological post-processing to prediction."""
        if not SCIPY_AVAILABLE:
            print("Warning: SciPy not available, skipping post-processing")
            return prediction

        result = prediction.copy()

        # Fill holes
        if fill_holes:
            try:
                result = binary_fill_holes(result > 0).astype(result.dtype)
            except Exception as e:
                print(f"Warning: Hole filling failed: {e}")

        # Keep largest connected component
        if largest_component:
            try:
                labeled, num_features = label(result > 0)
                if num_features > 1:
                    sizes = [(labeled == i).sum() for i in range(1, num_features + 1)]
                    largest_label = np.argmax(sizes) + 1
                    result = (labeled == largest_label).astype(result.dtype)
            except Exception as e:
                print(f"Warning: Largest component extraction failed: {e}")

        # Remove small components
        if min_component_size > 0:
            try:
                labeled, num_features = label(result > 0)
                for i in range(1, num_features + 1):
                    component_mask = labeled == i
                    if component_mask.sum() < min_component_size:
                        result[component_mask] = 0
            except Exception as e:
                print(f"Warning: Small component removal failed: {e}")

        return result
'''

    if "apply_postprocessing" not in content:
        # Find the TumorPredictor class and add the method
        class_start = content.find("class TumorPredictor:")
        if class_start != -1:
            # Find a good place to insert (before def main or at end of class)
            main_def = content.find("def main():")
            if main_def != -1:
                content = content[:main_def] + postproc_method + "\n\n" + content[main_def:]

    # Add CLI arguments if not already there
    if "--postproc" not in content:
        cli_args = '''    parser.add_argument(
        "--postproc",
        action="store_true",
        help="Enable post-processing operations"
    )
    parser.add_argument(
        "--fill-holes",
        action="store_true",
        help="Fill holes in segmentation masks"
    )
    parser.add_argument(
        "--largest-component",
        action="store_true",
        help="Keep only largest connected component"
    )
    parser.add_argument(
        "--min-component-size",
        type=int,
        default=100,
        help="Minimum component size (voxels) to keep"
    )
'''

        # Find the last parser.add_argument call
        last_arg = content.rfind("parser.add_argument")
        if last_arg != -1:
            # Find the end of that argument definition
            next_line_start = content.find('\n', content.find(')', last_arg)) + 1
            content = content[:next_line_start] + cli_args + content[next_line_start:]

    # Write the corrected content back
    with open(inference_file, 'w') as f:
        f.write(content)

    print("✅ Added post-processing capabilities to inference.py")


def main():
    """Main function to fix the inference.py file."""
    print("🔧 Fixing inference.py post-processing implementation...")
    add_postprocessing_to_inference()
    print("✅ Inference.py post-processing implementation completed!")


if __name__ == "__main__":
    main()
