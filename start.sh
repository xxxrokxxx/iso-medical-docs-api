#!/bin/bash
# Startup script to run both FastAPI and Gradio services

# Start FastAPI backend in the background on port 8080
echo "Starting FastAPI backend on port 8080..."
PORT=8080 python main_api.py &
FASTAPI_PID=$!

# Wait for FastAPI to start
sleep 5

# Start Gradio frontend on port 7860 (Cloud Run will route to this)
echo "Starting Gradio frontend on port ${PORT:-7860}..."
API_URL=http://localhost:8080 python gradio_app.py &
GRADIO_PID=$!

# Function to handle shutdown
shutdown() {
    echo "Shutting down services..."
    kill $FASTAPI_PID $GRADIO_PID 2>/dev/null
    wait $FASTAPI_PID $GRADIO_PID 2>/dev/null
    echo "Services stopped"
    exit 0
}

# Trap termination signals
trap shutdown SIGTERM SIGINT

# Wait for both processes
wait $FASTAPI_PID $GRADIO_PID
