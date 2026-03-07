"""
Build and verify package for distribution.

This script automates the package building process.
"""

import subprocess
import sys
import shutil
from pathlib import Path


def run_command(cmd, description):
    """Run a command and print status."""
    print(f"\n{'='*60}")
    print(f"📦 {description}")
    print(f"{'='*60}")
    print(f"Running: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ {description} - SUCCESS")
        if result.stdout:
            print(result.stdout)
        return True
    else:
        print(f"❌ {description} - FAILED")
        if result.stderr:
            print(result.stderr)
        return False


def clean_build_dirs():
    """Clean previous build artifacts."""
    print("\n🧹 Cleaning previous builds...")
    
    dirs_to_clean = ['build', 'dist', 'src/db_query_agent.egg-info']
    
    for dir_name in dirs_to_clean:
        dir_path = Path(dir_name)
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"  Removed: {dir_name}")
    
    print("✅ Cleanup complete")


def check_dependencies():
    """Check if required tools are installed."""
    print("\n🔍 Checking dependencies...")
    
    required = ['build', 'twine']
    missing = []
    
    for package in required:
        # Try importing the package instead of using pip show
        try:
            __import__(package)
            print(f"  ✅ {package} - installed")
        except ImportError:
            missing.append(package)
            print(f"  ❌ {package} - NOT INSTALLED")
    
    if missing:
        print(f"\n❌ Missing dependencies: {', '.join(missing)}")
        print(f"Install with: uv pip install {' '.join(missing)}")
        print(f"Or: pip install {' '.join(missing)}")
        return False
    
    return True


def run_tests():
    """Run test suite."""
    return run_command(
        [sys.executable, '-m', 'pytest', 'tests/', '-v', '--tb=short'],
        "Running tests"
    )


def build_package():
    """Build distribution packages."""
    return run_command(
        [sys.executable, '-m', 'build'],
        "Building distribution packages"
    )


def check_package():
    """Check package with twine."""
    return run_command(
        [sys.executable, '-m', 'twine', 'check', 'dist/*'],
        "Checking package quality"
    )


def list_dist_files():
    """List created distribution files."""
    print("\n📦 Distribution files created:")
    dist_path = Path('dist')
    
    if dist_path.exists():
        for file in dist_path.iterdir():
            size = file.stat().st_size / 1024  # KB
            print(f"  - {file.name} ({size:.1f} KB)")
    else:
        print("  No distribution files found")


def main():
    """Main build process."""
    print("\n" + "="*60)
    print("🚀 DB Query Agent - Package Builder")
    print("="*60)
    
    # Step 1: Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Step 2: Clean previous builds
    clean_build_dirs()
    
    # Step 3: Run tests
    if not run_tests():
        print("\n❌ Tests failed. Fix tests before building.")
        sys.exit(1)
    
    # Step 4: Build package
    if not build_package():
        print("\n❌ Build failed.")
        sys.exit(1)
    
    # Step 5: Check package
    if not check_package():
        print("\n❌ Package check failed.")
        sys.exit(1)
    
    # Step 6: List files
    list_dist_files()
    
    # Success!
    print("\n" + "="*60)
    print("✅ Package built successfully!")
    print("="*60)
    print("\nNext steps:")
    print("1. Test on TestPyPI:")
    print("   python -m twine upload --repository testpypi dist/*")
    print("\n2. Upload to PyPI:")
    print("   python -m twine upload dist/*")
    print("\n3. Create GitHub release:")
    print("   git tag -a v0.1.0 -m 'Release v0.1.0'")
    print("   git push origin v0.1.0")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
