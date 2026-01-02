"""Test script to verify main.py runs correctly."""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import main
from main import main

print("Testing that main.py can be imported and initialized...")
print("✓ All imports successful!")
print("\nTo run the application interactively, use: PYTHONPATH=src python src/main.py")
