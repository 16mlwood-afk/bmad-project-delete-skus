#!/usr/bin/env python3
"""
Demo script showing different testing modes for the SKU cleanup tool
"""

import os
import sys
from core.config import config

def demo_test_modes():
    """Demonstrate different testing configurations"""

    print("🧪 SKU Cleanup Tool - Testing Modes Demo")
    print("=" * 50)

    # Mode 1: Production Mode (Full Scale)
    print("\n1️⃣ PRODUCTION MODE (Full Scale)")
    print("   - Processes ALL SKUs from Amazon")
    print("   - Uses batch processing for performance")
    print("   - Recommended for daily automated runs")
    print(f"   - Batch Size: {config.settings.batch_size}")
    print("   - Environment: TEST_MODE=false")

    # Mode 2: Test Mode with Random Sampling
    print("\n2️⃣ TEST MODE (Random Sample)")
    print("   - Processes only a small random sample")
    print("   - Fast testing of logic with real data")
    print("   - Reproducible results (fixed seed)")
    print(f"   - Sample Size: {config.settings.test_sample_size}")
    print("   - Environment: TEST_MODE=true, TEST_SAMPLE_SIZE=10")

    # Mode 3: Test Mode with Specific SKUs
    print("\n3️⃣ TEST MODE (Specific SKUs)")
    print("   - Tests with known problematic or edge-case SKUs")
    print("   - Perfect for debugging specific scenarios")
    print("   - Fast feedback on fixes")
    if config.settings.test_seed_skus:
        print(f"   - Test SKUs: {config.settings.test_seed_skus}")
        print("   - Environment: TEST_MODE=true, TEST_SEED_SKUS=SKU1,SKU2,SKU3")
    else:
        print("   - No seed SKUs configured")
        print("   - Set TEST_SEED_SKUS environment variable")

    # Mode 4: Dry Run Mode (Safe Testing)
    print("\n4️⃣ DRY RUN MODE (Safe Testing)")
    print("   - Processes all logic but doesn't delete anything")
    print("   - Safe for testing in production environment")
    print("   - Perfect for validating changes before deployment")
    print(f"   - Current Setting: {config.settings.dry_run}")
    print("   - Environment: DRY_RUN=true")

    print("\n🚀 Quick Start Commands:")
    print("=" * 30)

    print("\n📊 Production Run:")
    print("   python3 main.py")
    print("   # Processes all SKUs with full resilience")

    print("\n🧪 Small Batch Test:")
    print("   TEST_MODE=true TEST_SAMPLE_SIZE=5 python3 main.py")
    print("   # Tests with 5 random SKUs")

    print("\n🎯 Specific SKU Test:")
    print("   TEST_MODE=true TEST_SEED_SKUS=KNOWN-SKU-1,KNOWN-SKU-2 python3 main.py")
    print("   # Tests with specific SKUs")

    print("\n🔍 Dry Run (Safe):")
    print("   DRY_RUN=true python3 main.py")
    print("   # Full processing but no actual deletions")

    print("\n⚡ Combined Test:")
    print("   TEST_MODE=true TEST_SAMPLE_SIZE=3 DRY_RUN=true python3 main.py")
    print("   # Quick 3-SKU test with no deletions")

    print("\n📋 Configuration Summary:")
    print(f"   Test Mode: {config.settings.test_mode}")
    print(f"   Dry Run: {config.settings.dry_run}")
    print(f"   Batch Size: {config.settings.batch_size}")
    print(f"   Sample Size: {config.settings.test_sample_size}")
    print(f"   Seed SKUs: {len(config.settings.test_seed_skus)} configured")

if __name__ == "__main__":
    demo_test_modes()
