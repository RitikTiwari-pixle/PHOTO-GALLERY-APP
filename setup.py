import subprocess
import sys
import os
import venv
import platform

def run_command(command, ignore_errors=False):
    try:
        subprocess.run(command, check=True, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError as e:
        if not ignore_errors:
            print(f"Error executing command: {command}")
            print(f"Error message: {e.stderr.decode()}")
        return False

def install_vs_buildtools():
    print("Installing Visual Studio Build Tools...")
    print("Please download and install from: https://visualstudio.microsoft.com/visual-cpp-build-tools/")
    input("Press Enter after installing Visual Studio Build Tools...")

def main():
    print("Setting up Photo Gallery App environment...")
    
    # Create virtual environment
    print("\n1. Creating virtual environment...")
    try:
        venv.create("venv", with_pip=True)
    except Exception as e:
        print(f"Error creating virtual environment: {e}")
        return

    # Determine the correct pip and python commands
    if platform.system() == "Windows":
        pip_cmd = ".\\venv\\Scripts\\pip"
        python_cmd = ".\\venv\\Scripts\\python"
    else:
        pip_cmd = "./venv/bin/pip"
        python_cmd = "./venv/bin/python"
    
    # Upgrade pip
    print("\n2. Upgrading pip...")
    run_command(f"{python_cmd} -m pip install --upgrade pip")
    
    # Install build tools
    print("\n3. Installing build tools...")
    if not run_command(f"{pip_cmd} install cmake"):
        install_vs_buildtools()
    run_command(f"{pip_cmd} install wheel")
    
    # Install dlib separately first
    print("\n4. Installing dlib (required for face recognition)...")
    if not run_command(f"{pip_cmd} install dlib"):
        print("Failed to install dlib. Please make sure Visual Studio Build Tools are installed.")
        install_vs_buildtools()
        if not run_command(f"{pip_cmd} install dlib"):
            print("dlib installation failed. Cannot proceed with face recognition.")
            return

    # Install required packages
    print("\n5. Installing required packages...")
    packages = [
        ("numpy", "Required for numerical operations"),
        ("Flask==2.3.3", "Web framework"),
        ("opencv-python==4.8.0", "Computer vision library"),
        ("Pillow==10.0.0", "Image processing"),
        ("python-dotenv==1.0.0", "Environment variables"),
        ("qrcode==7.4.2", "QR code generation")
    ]
    
    for package, description in packages:
        print(f"Installing {package} ({description})...")
        if not run_command(f"{pip_cmd} install {package}"):
            print(f"Failed to install {package}. This might affect {description} functionality.")
    
    # Create uploads directory
    print("\n6. Creating uploads directory...")
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
    
    # Test imports
    print("\n7. Testing imports...")
    test_imports = [
        "import flask",
        "import cv2",
        "import numpy",
        "import PIL",
        "import qrcode"
    ]
    
    for test in test_imports:
        try:
            exec(test)
            print(f"✓ {test} successful")
        except ImportError as e:
            print(f"✗ {test} failed: {e}")
            print("Please try running setup.py again or install the package manually.")
    
    print("\nSetup complete! You can now run the application with:")
    print(f"{python_cmd} app.py")
    print("\nIf you see any errors above, please address them before running the application.")
