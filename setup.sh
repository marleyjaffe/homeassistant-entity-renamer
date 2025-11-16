#!/bin/bash
# Setup script for HomeAssistant Entity Renamer

echo "Setting up HomeAssistant Entity Renamer..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
else
    echo "Virtual environment already exists."
fi

# Activate virtual environment and install dependencies
echo "Installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt

# Create a wrapper script for easy execution
echo "Creating wrapper script..."
cat > run.sh << 'EOF'
#!/bin/bash
# Wrapper script to run HomeAssistant Entity Renamer with virtual environment
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/venv/bin/activate"
python "$SCRIPT_DIR/homeassistant-entity-renamer.py" "$@"
EOF

chmod +x run.sh

echo "Setup complete!"
echo ""
echo "The script is now ready to use in one of these ways:"
echo "1. Using the wrapper (recommended):"
echo "   ./run.sh --search <pattern>"
echo ""
echo "2. Activate virtual environment first:"
echo "   source venv/bin/activate"
echo "   ./homeassistant-entity-renamer.py --search <pattern>"
echo ""
echo "3. Direct python execution:"
echo "   source venv/bin/activate"
echo "   python homeassistant-entity-renamer.py --search <pattern>"