#!/bin/bash

# Step 1: Create the vector store (one-time setup)
echo "Creating vector store from data.json..."
python vector_store.py

# Step 2: Start FastAPI Backend
echo "Starting FastAPI Backend..."
uvicorn main:app --reload &

# Step 3: Start Streamlit Frontend
echo "Starting Streamlit Frontend..."
streamlit run streamlit_app.py
