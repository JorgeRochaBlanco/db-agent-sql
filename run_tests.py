"""Test runner script for db-query-agent."""

import sys
import subprocess


def run_tests(test_type="all"):
    """Run tests based on type."""
    
    if test_type == "all":
        print("🧪 Running all tests...")
        cmd = ["pytest", "tests/", "-v", "--tb=short"]
    
    elif test_type == "phase4":
        print("🧪 Running Phase 4 tests...")
        cmd = [
            "pytest",
            "tests/test_dynamic_configuration.py",
            "tests/test_streaming.py",
            "tests/test_utility_methods.py",
            "tests/test_phase4_integration.py",
            "-v",
            "--tb=short"
        ]
    
    elif test_type == "integration":
        print("🧪 Running integration tests...")
        cmd = [
            "pytest",
            "tests/test_phase4_integration.py",
            "tests/test_agent_integration.py",
            "-v",
            "--tb=short"
        ]
    
    elif test_type == "quick":
        print("🧪 Running quick tests (no integration)...")
        cmd = [
            "pytest",
            "tests/",
            "-v",
            "--tb=short",
            "-k", "not integration"
        ]
    
    elif test_type == "coverage":
        print("🧪 Running tests with coverage...")
        cmd = [
            "pytest",
            "tests/",
            "--cov=db_query_agent",
            "--cov-report=html",
            "--cov-report=term",
            "-v"
        ]
    
    else:
        print(f"❌ Unknown test type: {test_type}")
        print("Available types: all, phase4, integration, quick, coverage")
        return 1
    
    # Run tests
    result = subprocess.run(cmd)
    return result.returncode


if __name__ == "__main__":
    test_type = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    print("=" * 60)
    print("DB Query Agent - Test Suite")
    print("=" * 60)
    
    exit_code = run_tests(test_type)
    
    print("\n" + "=" * 60)
    if exit_code == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")
    print("=" * 60)
    
    sys.exit(exit_code)
