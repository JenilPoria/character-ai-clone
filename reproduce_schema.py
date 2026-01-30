import sys
import os

# Add the project root to sys.path so we can import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

try:
    from app.schemas import UserCreate
    from pydantic import ValidationError
except ImportError as e:
    print(f"ImportError: {e}")
    sys.exit(1)

# Removed test_user_create function to avoid confusion


if __name__ == "__main__":
    # Test 1: Empty Password
    try:
        UserCreate(username="test", password="")
        print("Test 1 FAILED: Empty password was accepted.")
        sys.exit(1)
    except ValidationError:
        print("Test 1 PASSED: Empty password rejected.")

    # Test 2: 'string' Password
    try:
        UserCreate(username="test", password="string")
        print("Test 2 FAILED: 'string' password was accepted.")
        sys.exit(1)
    except ValidationError:
        print("Test 2 PASSED: 'string' password rejected.")
        
    # Test 3: Valid Password
    try:
        UserCreate(username="test", password="securepassword123")
        print("Test 3 PASSED: Valid password accepted.")
    except ValidationError as e:
        print(f"Test 3 FAILED: Valid password rejected. {e}")
        sys.exit(1)

    print("ALL TESTS PASSED")
    sys.exit(0)
