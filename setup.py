#!/usr/bin/env python3
"""
ReadingView Setup Script
Creates necessary __init__.py files for Python packages
"""

import os
from pathlib import Path


def main():
    print("ReadingView Setup")
    print("=" * 50)
    print()

    # Get script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    # Packages that need __init__.py
    packages = ["api", "components", "utils"]

    print("Creating Python package files...")
    for package in packages:
        package_dir = Path(package)
        package_dir.mkdir(parents=True, exist_ok=True)

        init_file = package_dir / "__init__.py"
        init_file.touch(exist_ok=True)

        print(f"✓ Created {init_file}")

    print()
    print("Setup complete!")
    print()
    print("Next steps:")
    print("1. Activate virtual environment:")
    print("   source venv/bin/activate")
    print()
    print("2. Install dependencies:")
    print("   pip install -r requirements.txt")
    print()
    print("3. Configure environment:")
    print("   cp .env.example .env")
    print("   # Edit .env with your credentials")
    print()
    print("4. Run the app:")
    print("   streamlit run app.py")
    print()


if __name__ == "__main__":
    main()
