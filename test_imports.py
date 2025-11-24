#!/usr/bin/env python3
print("Testing imports...")

try:
    from app.routes import login_required
    print("✅ login_required imported from app.routes")
except ImportError as e:
    print(f"❌ Failed to import login_required: {e}")

try:
    from app.clients import clients
    print("✅ clients blueprint imported")
except ImportError as e:
    print(f"❌ Failed to import clients: {e}")

try:
    from app.auth import auth
    print("✅ auth blueprint imported")
except ImportError as e:
    print(f"❌ Failed to import auth: {e}")

try:
    from app import create_app
    print("✅ create_app imported")
except ImportError as e:
    print(f"❌ Failed to import create_app: {e}")
