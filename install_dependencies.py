#!/usr/bin/env python3
import subprocess
import sys

def install_dependencies():
    dependencies = [
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
    
    for dep in dependencies:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"✓ Successfully installed {dep}")
        except subprocess.CalledProcessError:
            print(f"✗ Failed to install {dep}")
            # ادامه دادن حتی اگر بعضی dependencies نصب نشوند

if __name__ == "__main__":
    install_dependencies()
