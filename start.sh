#!/bin/bash

# Start Chromium in background (for Selenium)
export PATH=$PATH:/usr/bin
export CHROME_BIN=/usr/bin/chromium-browser

# Run Streamlit
streamlit run app/match_explorer.py --server.port=$PORT --server.enableCORS false
