#!/usr/bin/env python3
import subprocess
import sys

def install_requirements():
    """نصب dependencies از requirements.txt"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ All dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("⚠ Failed to install from requirements.txt, trying individual packages...")
        return install_individual()

def install_individual():
    """نصب تکی packages در صورت شکست"""
    packages = [
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0",
        "sqlalchemy==2.0.23",
        "python-dotenv==1.0.0",
        "pydantic-settings==2.1.0",
        "pydantic==2.5.0",
        "email-validator==2.0.0",
        "passlib[bcrypt]==1.7.4",
        "python-jose[cryptography]==3.3.0"
    ]
    
    success = True
    for package in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✓ Installed {package}")
        except subprocess.CalledProcessError:
            print(f"✗ Failed to install {package}")
            success = False
    
    return success

if __name__ == "__main__":
    install_requirements()
