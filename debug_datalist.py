#!/usr/bin/env python3
"""
Debug script to understand the load_decathlon_datalist issue.
"""
import json
import tempfile
from pathlib import Path

import nibabel as nib
import numpy as np
from monai.data import load_decathlon_datalist


def _write_nifti(arr: np.ndarray, path: Path) -> None:
    affine = np.eye(4, dtype=np.float32)
    img = nib.Nifti1Image(arr.astype(np.float32), affine)
    nib.save(img, str(path))


def _make_minimal_synthetic_dataset(root: Path):
    """Create minimal synthetic dataset for debugging."""
    task = "Task01_BrainTumour"
    base = root / task
    imagesTr = base / "imagesTr"
    labelsTr = base / "labelsTr"

    imagesTr.mkdir(parents=True, exist_ok=True)
    labelsTr.mkdir(parents=True, exist_ok=True)

    # Create one simple training case
    vol = np.random.normal(0, 1, size=(32, 32, 32)).astype(np.float32)
    lbl = np.zeros((32, 32, 32), dtype=np.uint8)
    lbl[8:16, 8:16, 8:16] = 1

    # Write files
    image_path = imagesTr / "case_001_flair.nii.gz"
    label_path = labelsTr / "case_001.nii.gz"
    _write_nifti(vol, image_path)
    _write_nifti(lbl, label_path)

    # Create simple JSON structure
    dec_json = {
        "name": "SyntheticBrainTumour",
        "description": "Minimal synthetic dataset",
        "tensorImageSize": "4D",
        "modality": {"0": "MRI"},
        "labels": {"0": "background", "1": "tumor"},
        "numTraining": 1,
        "numTest": 0,
        "training": [
            {
                "image": str(image_path),
                "label": str(label_path)
            }
        ]
    }

    json_path = base / f"{task}.json"
    with open(json_path, "w") as f:
        json.dump(dec_json, f, indent=2)

    print(f"Created dataset at: {base}")
    print(f"JSON content:\n{json.dumps(dec_json, indent=2)}")
    print(f"Image exists: {image_path.exists()}")
    print(f"Label exists: {label_path.exists()}")
    print(f"JSON exists: {json_path.exists()}")

    return base, json_path


def debug_load_decathlon_datalist():
    """Debug the load_decathlon_datalist function."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        base_dir, json_path = _make_minimal_synthetic_dataset(tmp_path)

        print("\n--- Debug load_decathlon_datalist ---")
        print(f"JSON path: {json_path}")
        print(f"Base dir: {base_dir}")

        try:
            # Test with different parameters
            print("\n1. Testing with section='training'")
            data_list = load_decathlon_datalist(
                data_list_file_path=str(json_path),
                is_segmentation=True,
                data_list_key="training",
                base_dir=str(base_dir)
            )
            print(f"Result: {len(data_list)} items")
            if data_list:
                print(f"First item: {data_list[0]}")
            else:
                print("Empty list returned!")

        except Exception as e:
            print(f"Error: {e}")

        try:
            print("\n2. Testing without base_dir")
            data_list = load_decathlon_datalist(
                data_list_file_path=str(json_path),
                is_segmentation=True,
                data_list_key="training"
            )
            print(f"Result: {len(data_list)} items")
            if data_list:
                print(f"First item: {data_list[0]}")

        except Exception as e:
            print(f"Error: {e}")

        try:
            print("\n3. Testing with relative paths")
            # Modify JSON to use relative paths
            with open(json_path, 'r') as f:
                dec_json = json.load(f)

            # Convert to relative paths
            dec_json["training"][0]["image"] = "imagesTr/case_001_flair.nii.gz"
            dec_json["training"][0]["label"] = "labelsTr/case_001.nii.gz"

            with open(json_path, 'w') as f:
                json.dump(dec_json, f, indent=2)

            data_list = load_decathlon_datalist(
                data_list_file_path=str(json_path),
                is_segmentation=True,
                data_list_key="training",
                base_dir=str(base_dir)
            )
            print(f"Result: {len(data_list)} items")
            if data_list:
                print(f"First item: {data_list[0]}")

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    debug_load_decathlon_datalist()
    debug_load_decathlon_datalist()
