"""
Post-processing script to organize and collect training visualization outputs.

This script collects overlay images from training runs and organizes them
into standardized reports for comparison across epochs and configurations.
"""

import argparse
import shutil
from pathlib import Path
from typing import Dict, List, Optional


def collect_training_overlays(
    model_dir: Path,
    output_dir: Path,
    experiment_name: str,
) -> Dict[str, int]:
    """
    Collect overlay images from a training run.

    Args:
        model_dir: Directory containing training outputs (e.g., models/unetr)
        output_dir: Directory to organize outputs (e.g., reports/learned_behaviors)
        experiment_name: Name for this experiment

    Returns:
        Dictionary with collection statistics
    """
    overlays_dir = model_dir / "overlays"
    if not overlays_dir.exists():
        print(f"No overlays directory found in {model_dir}")
        return {"collected": 0, "organized": 0}

    # Create experiment directory
    exp_dir = output_dir / experiment_name
    exp_dir.mkdir(parents=True, exist_ok=True)

    # Collect all overlay files
    overlay_files = list(overlays_dir.glob("*.png"))
    prob_map_files = list(overlays_dir.glob("*probmap*.png"))

    collected = 0
    organized = 0

    # Copy regular overlays
    for overlay_file in overlay_files:
        if "probmap" not in overlay_file.name:
            dest_file = exp_dir / f"overlay_{overlay_file.name}"
            shutil.copy2(overlay_file, dest_file)
            collected += 1

    # Copy probability maps to separate subdirectory
    if prob_map_files:
        prob_dir = exp_dir / "probability_maps"
        prob_dir.mkdir(exist_ok=True)
        for prob_file in prob_map_files:
            dest_file = prob_dir / prob_file.name
            shutil.copy2(prob_file, dest_file)
            organized += 1

    # Create experiment metadata
    metadata = {
        "experiment_name": experiment_name,
        "source_directory": str(model_dir),
        "overlay_count": collected,
        "probability_map_count": organized,
        "total_files": collected + organized,
    }

    import json
    with open(exp_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"Collected {collected} overlays and {organized} probability maps")
    print(f"Organized into: {exp_dir}")

    return {"collected": collected, "organized": organized}


def create_comparison_report(
    experiments_dir: Path,
    output_file: Path,
    experiment_names: Optional[List[str]] = None,
) -> None:
    """
    Create a comparison report across multiple experiments.

    Args:
        experiments_dir: Directory containing experiment subdirectories
        output_file: Path for the comparison report (HTML)
        experiment_names: List of experiment names to include. If None, uses all.
    """
    if not experiments_dir.exists():
        print(f"Experiments directory not found: {experiments_dir}")
        return

    # Find all experiment directories
    if experiment_names is None:
        exp_dirs = [d for d in experiments_dir.iterdir() if d.is_dir()]
        experiment_names = [d.name for d in exp_dirs]
    else:
        exp_dirs = [experiments_dir / name for name in experiment_names]

    # Generate HTML report
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Tumor Detection Training Visualization Report</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .experiment { border: 1px solid #ccc; margin: 20px 0; padding: 15px; }
            .experiment h2 { color: #333; }
            .overlay-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; }
            .overlay-item { text-align: center; }
            .overlay-item img { max-width: 100%; height: auto; border: 1px solid #ddd; }
            .metadata { background: #f5f5f5; padding: 10px; margin: 10px 0; font-family: monospace; }
        </style>
    </head>
    <body>
        <h1>Tumor Detection Training Visualization Report</h1>
        <p>Generated visualization comparisons across training experiments.</p>
    """

    for exp_dir in exp_dirs:
        if not exp_dir.exists():
            continue

        html_content += f"""
        <div class="experiment">
            <h2>Experiment: {exp_dir.name}</h2>
        """

        # Load metadata if available
        metadata_file = exp_dir / "metadata.json"
        if metadata_file.exists():
            import json
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            html_content += f"""
            <div class="metadata">
                <strong>Metadata:</strong><br>
                Source: {metadata.get('source_directory', 'Unknown')}<br>
                Overlays: {metadata.get('overlay_count', 0)}<br>
                Probability Maps: {metadata.get('probability_map_count', 0)}
            </div>
            """

        # Add overlay images
        overlay_files = list(exp_dir.glob("overlay_*.png"))
        if overlay_files:
            html_content += """
            <h3>Validation Overlays</h3>
            <div class="overlay-grid">
            """

            for overlay_file in sorted(overlay_files)[:6]:  # Limit to first 6
                rel_path = overlay_file.relative_to(output_file.parent)
                html_content += f"""
                <div class="overlay-item">
                    <img src="{rel_path}" alt="{overlay_file.name}">
                    <p>{overlay_file.name}</p>
                </div>
                """

            html_content += "</div>"

        # Add probability maps if available
        prob_dir = exp_dir / "probability_maps"
        if prob_dir.exists():
            prob_files = list(prob_dir.glob("*.png"))
            if prob_files:
                html_content += """
                <h3>Probability Maps</h3>
                <div class="overlay-grid">
                """

                for prob_file in sorted(prob_files)[:4]:  # Limit to first 4
                    rel_path = prob_file.relative_to(output_file.parent)
                    html_content += f"""
                    <div class="overlay-item">
                        <img src="{rel_path}" alt="{prob_file.name}">
                        <p>{prob_file.name}</p>
                    </div>
                    """

                html_content += "</div>"

        html_content += "</div>"

    html_content += """
    </body>
    </html>
    """

    # Write report
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Comparison report created: {output_file}")


def main():
    """Main function for post-processing script."""
    parser = argparse.ArgumentParser(
        description="Organize training visualization outputs"
    )
    parser.add_argument(
        "--model-dir",
        type=str,
        required=True,
        help="Training model directory (e.g., models/unetr)",
    )
    parser.add_argument(
        "--experiment-name",
        type=str,
        required=True,
        help="Name for this experiment",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="reports/learned_behaviors",
        help="Output directory for organized reports",
    )
    parser.add_argument(
        "--create-report",
        action="store_true",
        help="Create HTML comparison report",
    )

    args = parser.parse_args()

    model_dir = Path(args.model_dir)
    output_dir = Path(args.output_dir)

    if not model_dir.exists():
        print(f"Model directory not found: {model_dir}")
        return

    # Collect and organize overlays
    stats = collect_training_overlays(model_dir, output_dir, args.experiment_name)

    # Create comparison report if requested
    if args.create_report:
        report_file = output_dir / "comparison_report.html"
        create_comparison_report(output_dir, report_file)


if __name__ == "__main__":
    main()
