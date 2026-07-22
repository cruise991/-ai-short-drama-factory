#!/bin/bash

# Setup Python and Node.js dependencies for OpenMontage Integration

echo "==========================================="
echo "⚙️ Setting up dependencies for Short Drama Pipeline & OpenMontage..."
echo "==========================================="

# Check Python environment
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed or not in PATH."
    exit 1
fi

echo "📦 Installing Python dependencies..."
python3 -m pip install -r requirements.txt || echo "Warning: Some python requirements failed to install, continuing..."

# Check Node environment
echo "🔍 Checking Node.js environment..."
if ! command -v node &> /dev/null; then
    echo "⚠️ Warning: Node.js is not installed."
    echo "OpenMontage Remotion composer requires Node.js 18+."
    echo "The orchestrator will automatically fallback to FFmpeg for composition."
else
    NODE_VER=$(node -v)
    echo "✅ Node.js found: $NODE_VER"
    
    if [ -d "third_party/OpenMontage/remotion-composer" ]; then
        echo "📦 Installing NPM dependencies for Remotion Composer..."
        cd third_party/OpenMontage/remotion-composer
        npm install
        cd ../../..
        echo "✅ Node dependencies installed successfully."
    else
        echo "⚠️ Warning: third_party/OpenMontage/remotion-composer directory not found."
    fi
fi

echo "==========================================="
echo "🎉 Setup complete! You can now run the orchestrator."
echo "==========================================="
