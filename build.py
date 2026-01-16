
import subprocess
import sys
import os

def install_pyinstaller():
    try:
        import PyInstaller
        print("PyInstaller is already installed.")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

def build():
    print("Starting build process...")
    try:
        # Run PyInstaller with the spec file using the current python interpreter
        subprocess.check_call([sys.executable, "-m", "PyInstaller", "main.spec", "--clean"])
        print("\nBuild completed successfully!")
        print("The executable can be found in the 'dist' directory.")
        
        # Determine executable name based on OS
        exe_name = "factur-x-generator"
        if sys.platform == "win32":
            exe_name += ".exe"
            
        print(f"\nTo run it: dist/{exe_name}")
        
    except subprocess.CalledProcessError as e:
        print(f"\nError during build: {e}")
        sys.exit(1)

if __name__ == "__main__":
    install_pyinstaller()
    build()
