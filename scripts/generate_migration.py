#!/usr/bin/env python3
"""Script to generate the initial Alembic migration."""

import subprocess
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import models to ensure they're loaded
from app.models import User, UserRole, Client, Document, DocumentType, DocumentStatus

def main():
    """Generate the initial migration."""
    try:
        # Generate the migration
        message = sys.argv[1] if len(sys.argv) > 1 else "Add document upload functionality"
        result = subprocess.run([
            "alembic", "revision", "--autogenerate", "-m", message
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Migration generated successfully!")
            print(result.stdout)
        else:
            print("Error generating migration:")
            print(result.stderr)
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()