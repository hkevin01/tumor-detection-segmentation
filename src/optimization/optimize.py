#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main optimization script for hyperparameter tuning in medical image segmentation.

This script provides a command-line interface for running hyperparameter
optimization studies using Optuna with comprehensive visualization and reporting.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict

import optuna

from .objective_functions import (FastObjective,
                                  MultiObjectiveSegmentationObjective,
                                  SegmentationObjective)
from .optuna_optimizer import OptunaTuner


def setup_logging(log_level: str = "INFO", log_file: str = None) -> None:
    """
    Set up logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional log file path
    """
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=handlers
    )


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate the optimization configuration.

    Args:
        config: Configuration dictionary

    Raises:
        ValueError: If configuration is invalid
    """
    required_sections = ["optimizer", "objective", "optimization"]
    for section in required_sections:
        if section not in config:
            raise ValueError(f"Missing required section: {section}")

    # Validate paths exist
    objective_config = config["objective"]
    required_paths = ["base_config_path", "dataset_config_path", "data_dir"]

    for path_key in required_paths:
        if path_key in objective_config:
            path = Path(objective_config[path_key])
            if not path.exists():
                raise ValueError(f"Path does not exist: {path}")


def create_objective_function(config: Dict[str, Any]) -> Any:
    """
    Create the appropriate objective function based on configuration.

    Args:
        config: Configuration dictionary

    Returns:
        Objective function instance
    """
    objective_config = config["objective"]
    objective_type = objective_config.get("type", "single")

    if objective_type == "multi":
        return MultiObjectiveSegmentationObjective(**objective_config)
    elif objective_type == "fast":
        return FastObjective(**objective_config)
    else:
        return SegmentationObjective(**objective_config)


def run_optimization(config_path: str, args: argparse.Namespace) -> None:
    """
    Run the hyperparameter optimization study.

    Args:
        config_path: Path to optimization configuration file
        args: Command line arguments
    """
    logger = logging.getLogger(__name__)

    # Load configuration
    logger.info(f"Loading configuration from: {config_path}")
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Override config with command line arguments
    if args.n_trials:
        config["optimization"]["n_trials"] = args.n_trials
    if args.timeout:
        config["optimization"]["timeout"] = args.timeout
    if args.n_jobs:
        config["optimization"]["n_jobs"] = args.n_jobs
    if args.output_dir:
        config["objective"]["output_dir"] = args.output_dir

    # Validate configuration
    validate_config(config)

    # Create optimizer
    logger.info("Creating Optuna optimizer...")
    tuner = OptunaTuner(**config["optimizer"])

    # Create objective function
    logger.info("Creating objective function...")
    objective_function = create_objective_function(config)

    # Run optimization
    logger.info("Starting hyperparameter optimization...")
    study = tuner.optimize(
        objective_function=objective_function,
        **config["optimization"]
    )

    # Save results
    output_dir = Path(config["objective"]["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Saving optimization results...")

    # Save best configuration
    tuner.save_best_config(output_dir / "best_config.json")

    # Save study statistics
    stats = tuner.get_study_statistics()
    with open(output_dir / "study_statistics.json", 'w') as f:
        json.dump(stats, f, indent=2)

    # Create visualizations
    tuner.visualize_optimization(output_dir / "visualizations")

    # Save study object for later analysis
    study_path = output_dir / f"{study.study_name}.pkl"
    optuna.study.dump_study(study, str(study_path))

    logger.info(f"Optimization completed! Results saved to: {output_dir}")
    logger.info(f"Best value: {study.best_value:.4f}")
    logger.info("Best parameters:")
    for key, value in study.best_params.items():
        logger.info(f"  {key}: {value}")


def resume_study(study_path: str, config_path: str, args: argparse.Namespace) -> None:
    """
    Resume a previous optimization study.

    Args:
        study_path: Path to saved study pickle file
        config_path: Path to optimization configuration file
        args: Command line arguments
    """
    logger = logging.getLogger(__name__)

    # Load saved study
    logger.info(f"Loading study from: {study_path}")
    study = optuna.study.load_study(storage=f"sqlite:///{study_path}")

    # Load configuration
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Override config with command line arguments
    if args.n_trials:
        config["optimization"]["n_trials"] = args.n_trials

    # Create objective function
    objective_function = create_objective_function(config)

    # Resume optimization
    logger.info("Resuming hyperparameter optimization...")
    study.optimize(
        objective_function,
        n_trials=config["optimization"]["n_trials"]
    )

    logger.info("Resumed optimization completed!")


def analyze_study(study_path: str, output_dir: str) -> None:
    """
    Analyze a completed optimization study.

    Args:
        study_path: Path to saved study pickle file
        output_dir: Directory to save analysis results
    """
    logger = logging.getLogger(__name__)

    # Load study
    logger.info(f"Loading study from: {study_path}")
    study = optuna.study.load_study(storage=f"sqlite:///{study_path}")

    # Create analyzer
    from .analysis import StudyAnalyzer
    analyzer = StudyAnalyzer(study)

    # Generate analysis report
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    analyzer.generate_report(output_path)

    logger.info(f"Analysis completed! Report saved to: {output_path}")


def main():
    """Main entry point for the optimization script."""
    parser = argparse.ArgumentParser(
        description="Hyperparameter optimization for medical image segmentation",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Optimize command
    optimize_parser = subparsers.add_parser("optimize", help="Run optimization study")
    optimize_parser.add_argument(
        "--config", required=True, help="Optimization configuration file"
    )
    optimize_parser.add_argument(
        "--n-trials", type=int, help="Number of trials to run"
    )
    optimize_parser.add_argument(
        "--timeout", type=float, help="Timeout in seconds"
    )
    optimize_parser.add_argument(
        "--n-jobs", type=int, help="Number of parallel jobs"
    )
    optimize_parser.add_argument(
        "--output-dir", help="Output directory for results"
    )
    optimize_parser.add_argument(
        "--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    optimize_parser.add_argument(
        "--log-file", help="Log file path"
    )

    # Resume command
    resume_parser = subparsers.add_parser("resume", help="Resume optimization study")
    resume_parser.add_argument(
        "--study", required=True, help="Path to saved study file"
    )
    resume_parser.add_argument(
        "--config", required=True, help="Optimization configuration file"
    )
    resume_parser.add_argument(
        "--n-trials", type=int, help="Additional trials to run"
    )

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze optimization study")
    analyze_parser.add_argument(
        "--study", required=True, help="Path to saved study file"
    )
    analyze_parser.add_argument(
        "--output-dir", required=True, help="Output directory for analysis"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Set up logging
    if hasattr(args, 'log_level'):
        setup_logging(args.log_level, getattr(args, 'log_file', None))
    else:
        setup_logging()

    # Execute command
    try:
        if args.command == "optimize":
            run_optimization(args.config, args)
        elif args.command == "resume":
            resume_study(args.study, args.config, args)
        elif args.command == "analyze":
            analyze_study(args.study, args.output_dir)
        else:
            parser.print_help()
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Command failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
