#!/bin/bash
# Run Agent Factory Mission Control Dashboard

cd "$(dirname "$0")"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

# Run the dashboard
echo "🚀 Starting Agent Factory Mission Control..."
echo "📊 Open http://localhost:8000 in your browser"
python -m src.web.app
