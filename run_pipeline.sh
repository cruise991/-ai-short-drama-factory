#!/bin/bash
set -e
echo "Starting production agent..."
python3 departments/03_production/production_agent.py
echo "Starting post production agent..."
python3 departments/06_post_production/post_production_agent.py
