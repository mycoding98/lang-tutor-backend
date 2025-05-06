#!/bin/bash

# Ensure pip is updated
python3 -m pip install --upgrade pip

# Install dependencies from requirements.txt
pip install -r requirements.txt

# Start the app with Gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
