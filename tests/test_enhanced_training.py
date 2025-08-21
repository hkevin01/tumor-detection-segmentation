"""
Test Enhanced Training Framework
==============================

Comprehensive tests for advanced training strategies.
"""

import sys
import os
sys.path.append('/home/kevin/Projects/tumor-detection-segmentation/src')

import tempfile
import numpy as np
from pathlib import Path

try:
    from training.enhanced_trainer import (
        EnhancedTrainer, HybridTrainingOrchestrator, 
        TrainingConfig, TrainingMetrics,
        CurriculumScheduler, ProgressiveTrainer, MultiScaleTrainer
    )
    
    def test_training_config():
        """Test training configuration."""
        print("Testing training configuration...")
        
        config = TrainingConfig(
            epochs=50,
            batch_size=4,
            learning_rate=1e-3,
            enable_progressive_resizing=True,
            enable_curriculum=True,
            enable_multiscale=True
        )
        
        assert config.epochs == 50
        assert config.batch_size == 4
        assert config.enable_progressive_resizing is True
        assert config.enable_curriculum is True
        assert config.enable_multiscale is True
        
        print("✓ TrainingConfig initialized and validated")
    
    def test_curriculum_scheduler():
        """Test curriculum learning scheduler."""
        print("\nTesting curriculum scheduler...")
        
        scheduler = CurriculumScheduler(
            strategy="difficulty_based",
            patience=5,
            threshold=0.8
        )
        
        # Test advancement logic
        assert scheduler.current_level == 0
        
        # Should not advance with low metric
        advance = scheduler.should_advance(0.5)
        assert not advance
        assert scheduler.current_level == 0
        
        # Should advance with high metric
        advance = scheduler.should_advance(0.85)
        assert advance
        assert scheduler.current_level == 1
        
        # Test curriculum configuration
        config = scheduler.get_curriculum_config()
        assert "complexity" in config or "level" in config
        
        print("✓ CurriculumScheduler working correctly")
    
    def test_progressive_trainer():
        """Test progressive resizing trainer."""
        print("\nTesting progressive trainer...")
        
        trainer = ProgressiveTrainer(
            epochs=[10, 20, 30],
            sizes=[(64, 64, 32), (96, 96, 48), (128, 128, 64), (160, 160, 80)]
        )
        
        # Test size progression
        size_0 = trainer.get_current_size(5)
        size_1 = trainer.get_current_size(15)
        size_2 = trainer.get_current_size(25)
        size_3 = trainer.get_current_size(35)
        
        assert size_0 == (64, 64, 32)
        assert size_1 == (96, 96, 48)
        assert size_2 == (128, 128, 64)
        assert size_3 == (160, 160, 80)
        
        # Test resize detection
        assert trainer.should_resize(10) is True
        assert trainer.should_resize(5) is False
        
        print("✓ ProgressiveTrainer working correctly")
    
    def test_multiscale_trainer():
        """Test multi-scale training."""
        print("\nTesting multi-scale trainer...")
        
        trainer = MultiScaleTrainer(
            scale_factors=[0.8, 1.0, 1.2],
            probability=0.5
        )
        
        # Test scale selection
        scale = trainer.get_random_scale()
        assert scale in trainer.scale_factors
        
        # Test probability (run multiple times)
        applications = 0
        for _ in range(100):
            if trainer.should_apply_multiscale():
                applications += 1
        
        # Should be roughly around 50% (with some variance)
        assert 30 <= applications <= 70
        
        print("✓ MultiScaleTrainer working correctly")
    
    def test_enhanced_trainer():
        """Test enhanced trainer initialization and basic functionality."""
        print("\nTesting enhanced trainer...")
        
        config = TrainingConfig(
            epochs=10,
            batch_size=2,
            learning_rate=1e-4,
            enable_progressive_resizing=True,
            enable_curriculum=True,
            enable_multiscale=True,
            framework="hybrid"
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            trainer = EnhancedTrainer(
                config=config,
                model=None,  # No actual model for testing
                train_loader=None,
                val_loader=None,
                save_dir=temp_dir
            )
            
            # Test initialization
            assert trainer.config.framework == "hybrid"
            assert trainer.curriculum_scheduler is not None
            assert trainer.progressive_trainer is not None
            assert trainer.multiscale_trainer is not None
            
            # Test training epoch simulation
            metrics = trainer.train_epoch(0)
            assert isinstance(metrics, TrainingMetrics)
            assert metrics.epoch == 0
            assert metrics.train_loss > 0
            assert 0 <= metrics.train_accuracy <= 1
            
            # Test validation epoch simulation
            val_metrics = trainer.validate_epoch(0)
            assert isinstance(val_metrics, TrainingMetrics)
            assert val_metrics.val_loss > 0
            assert 0 <= val_metrics.val_accuracy <= 1
            
            print("✓ EnhancedTrainer initialized and basic operations working")
    
    def test_training_simulation():
        """Test full training simulation."""
        print("\nTesting training simulation...")
        
        config = TrainingConfig(
            epochs=5,  # Short training for testing
            batch_size=2,
            learning_rate=1e-4,
            enable_progressive_resizing=True,
            enable_curriculum=True,
            enable_multiscale=True,
            early_stopping_patience=10,
            save_frequency=2
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            trainer = EnhancedTrainer(
                config=config,
                save_dir=temp_dir
            )
            
            # Run training simulation
            metrics_history = trainer.train()
            
            # Validate results
            assert len(metrics_history) <= config.epochs
            assert len(metrics_history) > 0
            
            # Check metrics progression
            for metrics in metrics_history:
                assert isinstance(metrics, TrainingMetrics)
                assert metrics.train_loss > 0
                assert metrics.val_loss > 0
                assert 0 <= metrics.train_dice <= 1
                assert 0 <= metrics.val_dice <= 1
            
            # Test training summary
            summary = trainer.get_training_summary()
            assert "total_epochs" in summary
            assert "best_val_dice" in summary
            assert "config" in summary
            assert "strategies_used" in summary
            
            print(f"✓ Training completed: {summary['total_epochs']} epochs")
            print(f"  - Best validation Dice: {summary['best_val_dice']:.3f}")
            print(f"  - Strategies used: {summary['strategies_used']}")
    
    def test_hybrid_orchestrator():
        """Test hybrid training orchestrator."""
        print("\nTesting hybrid training orchestrator...")
        
        # Create configs for different frameworks
        framework_configs = {
            "nnunet": TrainingConfig(epochs=3, framework="nnunet"),
            "monai": TrainingConfig(epochs=3, framework="monai"),
            "detectron2": TrainingConfig(epochs=3, framework="detectron2")
        }
        
        orchestrator = HybridTrainingOrchestrator(
            framework_configs=framework_configs,
            ensemble_strategy="sequential"
        )
        
        # Add trainers
        with tempfile.TemporaryDirectory() as temp_dir:
            for framework, config in framework_configs.items():
                trainer = EnhancedTrainer(
                    config=config,
                    save_dir=str(Path(temp_dir) / framework)
                )
                orchestrator.add_trainer(framework, trainer)
            
            # Test sequential training
            results = orchestrator.train_all_frameworks()
            
            assert len(results) == 3
            assert "nnunet" in results
            assert "monai" in results
            assert "detectron2" in results
            
            for framework, metrics_list in results.items():
                assert len(metrics_list) <= framework_configs[framework].epochs
                assert len(metrics_list) > 0
            
            # Test ensemble summary
            summary = orchestrator.get_ensemble_summary()
            assert "strategy" in summary
            assert "frameworks" in summary
            assert "framework_summaries" in summary
            assert "best_framework" in summary
            
            print(f"✓ Hybrid orchestrator completed")
            print(f"  - Strategy: {summary['strategy']}")
            print(f"  - Frameworks: {summary['frameworks']}")
            print(f"  - Best framework: {summary['best_framework']}")
    
    def test_different_strategies():
        """Test different training strategies."""
        print("\nTesting different training strategies...")
        
        strategies = [
            {"enable_progressive_resizing": True, "enable_curriculum": False, "enable_multiscale": False},
            {"enable_progressive_resizing": False, "enable_curriculum": True, "enable_multiscale": False},
            {"enable_progressive_resizing": False, "enable_curriculum": False, "enable_multiscale": True},
            {"enable_progressive_resizing": True, "enable_curriculum": True, "enable_multiscale": True}
        ]
        
        for i, strategy in enumerate(strategies):
            config = TrainingConfig(
                epochs=3,
                **strategy
            )
            
            with tempfile.TemporaryDirectory() as temp_dir:
                trainer = EnhancedTrainer(
                    config=config,
                    save_dir=temp_dir
                )
                
                metrics_history = trainer.train()
                assert len(metrics_history) > 0
                
                summary = trainer.get_training_summary()
                expected_strategies = []
                
                if strategy["enable_progressive_resizing"]:
                    expected_strategies.append("progressive_resizing")
                if strategy["enable_curriculum"]:
                    expected_strategies.append("curriculum_learning")
                if strategy["enable_multiscale"]:
                    expected_strategies.append("multiscale_training")
                
                # Check that strategies are properly tracked
                for expected in expected_strategies:
                    assert expected in summary["strategies_used"]
                
                print(f"✓ Strategy {i+1} completed with {len(summary['strategies_used'])} techniques")
    
    def run_all_tests():
        """Run all enhanced training tests."""
        print("🧪 Enhanced Training Framework Tests")
        print("=" * 50)
        
        test_functions = [
            test_training_config,
            test_curriculum_scheduler,
            test_progressive_trainer,
            test_multiscale_trainer,
            test_enhanced_trainer,
            test_training_simulation,
            test_hybrid_orchestrator,
            test_different_strategies
        ]
        
        passed = 0
        failed = 0
        
        for test_func in test_functions:
            try:
                test_func()
                passed += 1
            except Exception as e:
                print(f"✗ {test_func.__name__} failed: {e}")
                failed += 1
        
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {passed} passed, {failed} failed")
        
        if failed == 0:
            print("🎉 All enhanced training tests passed!")
        else:
            print(f"⚠️  {failed} tests failed")
        
        return failed == 0

    if __name__ == "__main__":
        run_all_tests()

except ImportError as e:
    print(f"❌ Enhanced training tests skipped: {e}")
    print("Please ensure all dependencies are installed")
