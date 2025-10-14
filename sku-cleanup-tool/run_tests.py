#!/usr/bin/env python3
"""
Test runner script for SKU Cleanup Tool
Provides convenient commands for running different test suites
"""
import subprocess
import sys
import argparse
import os


def run_command(cmd, description=""):
    """Run a command and return the result"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"✅ SUCCESS: {description}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ FAILED: {description}")
        print(f"Exit code: {e.returncode}")
        return False
    except KeyboardInterrupt:
        print("⏹️  INTERRUPTED by user")
        return False


def main():
    parser = argparse.ArgumentParser(description='Test runner for SKU Cleanup Tool')
    parser.add_argument('--coverage', action='store_true',
                       help='Run tests with coverage reporting')
    parser.add_argument('--unit', action='store_true',
                       help='Run only unit tests')
    parser.add_argument('--integration', action='store_true',
                       help='Run only integration tests')
    parser.add_argument('--fast', action='store_true',
                       help='Run tests without coverage (faster)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')

    args = parser.parse_args()

    # Base pytest command - use python3 for compatibility
    cmd = ['python3', '-m', 'pytest']

    if args.verbose:
        cmd.append('-v')

    # Test selection
    if args.unit:
        cmd.extend(['-m', 'unit'])
    elif args.integration:
        cmd.extend(['-m', 'integration'])
    # Default: run all tests

    # Coverage configuration
    if args.coverage and not args.fast:
        cmd.extend([
            '--cov=.',
            '--cov-report=term-missing',
            '--cov-report=html:htmlcov',
            '--cov-fail-under=80'
        ])
    elif args.fast:
        cmd.extend(['--no-cov'])

    # Add test directory
    cmd.append('tests/')

    success = run_command(cmd, "Running test suite")

    if success:
        print(f"\n{'='*60}")
        print("🎉 All tests passed!")
        print(f"{'='*60}")

        if args.coverage and not args.fast:
            print("📊 Coverage report generated in: htmlcov/index.html")
            print("📈 Check coverage details above")

        print("\n✅ Your SKU Cleanup Tool is well-tested and ready!")
    else:
        print(f"\n{'='*60}")
        print("❌ Some tests failed!")
        print("🔍 Check the output above for details")
        print(f"{'='*60}")
        sys.exit(1)


if __name__ == "__main__":
    main()
