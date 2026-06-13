#!/usr/bin/env python
"""
Setup script to install required packages and run query_agent.py
"""
import subprocess
import sys
import os


def setup_and_run():
    """Configure conda channels and install required packages"""

    print("="*80)
    print("SETTING UP DEPENDENCIES FOR NEXUS CORE AI ASSISTANT")
    print("="*80)

    # Step 1: Configure conda
    print("\n[Setup] Configuring conda channels...")
    try:
        subprocess.run(
            ["conda", "config", "--add", "channels", "conda-forge"],
            check=True,
            capture_output=True
        )
        print("✓ Conda channels configured")
    except Exception as e:
        print(f"⚠ Conda configuration warning: {e}")

    # Step 2: Install packages via pip
    print("\n[Setup] Installing required Python packages...")
    packages = [
        "langchain-community",
        "langchain-ollama",
        "chromadb"
    ]

    try:
        for package in packages:
            print(f"  Installing {package}...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", package, "-q"],
                check=True,
                timeout=120
            )
            print(f"  ✓ {package} installed")

        print("\n✓ All packages installed successfully")
    except Exception as e:
        print(f"✗ Installation error: {e}")
        return False

    # Step 3: Run query_agent.py
    print("\n" + "="*80)
    print("LAUNCHING QUERY AGENT")
    print("="*80)

    try:
        os.chdir("/workspaces/GEMMA4")
        subprocess.run(
            [sys.executable, "query_agent.py"],
            check=False
        )
    except Exception as e:
        print(f"✗ Error running query_agent.py: {e}")
        return False

    return True


if __name__ == "__main__":
    success = setup_and_run()
    sys.exit(0 if success else 1)
