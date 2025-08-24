#!/usr/bin/env python3
"""
Build script for Flask Tweet App
This script builds the Tailwind CSS for production deployment
"""

import subprocess
import sys
import os

def run_command(command, cwd=None):
    """Run a command and return its result"""
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, check=True, 
                              capture_output=True, text=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def main():
    """Main build function"""
    print("🚀 Building Flask Tweet App for production...")
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check if npm is available
    print("📦 Checking npm availability...")
    success, output = run_command("npm --version")
    if not success:
        print("❌ npm is not available. Please install Node.js and npm first.")
        return False
    
    print(f"✅ npm version: {output.strip()}")
    
    # Install dependencies
    print("📥 Installing dependencies...")
    success, output = run_command("npm install", cwd=script_dir)
    if not success:
        print(f"❌ Failed to install dependencies: {output}")
        return False
    
    print("✅ Dependencies installed successfully")
    
    # Build Tailwind CSS
    print("🎨 Building Tailwind CSS...")
    success, output = run_command("npx tailwindcss -i ./static/src/input.css -o ./static/css/tailwind.css --minify", 
                                 cwd=script_dir)
    if not success:
        print(f"❌ Failed to build Tailwind CSS: {output}")
        return False
    
    print("✅ Tailwind CSS built successfully")
    
    # Check if the output file exists
    css_file = os.path.join(script_dir, "static", "css", "tailwind.css")
    if os.path.exists(css_file):
        file_size = os.path.getsize(css_file)
        print(f"📁 Generated tailwind.css size: {file_size:,} bytes")
    else:
        print("❌ tailwind.css file was not generated")
        return False
    
    print("\n🎉 Build completed successfully!")
    print("📝 To deploy:")
    print("   1. Upload all files to your server")
    print("   2. Make sure static/css/tailwind.css is accessible")
    print("   3. The app will now use optimized Tailwind CSS instead of CDN")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)