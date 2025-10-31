#!/bin/bash
# Startup script to run both FastAPI and Gradio services

# Start FastAPI backend in the background
echo "Starting FastAPI backend on port ${PORT:-8080}..."
python main_api.py &
FASTAPI_PID=$!

# Wait a bit for FastAPI to start
sleep 5

# Start Gradio frontend
echo "Starting Gradio frontend on port ${GRADIO_PORT:-7860}..."
python gradio_app.py &
GRADIO_PID=$!

# Function to handle shutdown
shutdown() {
    echo "Shutting down services..."
    kill $FASTAPI_PID $GRADIO_PID
    wait $FASTAPI_PID $GRADIO_PID
    echo "Services stopped"
    exit 0
}

# Trap termination signals
trap shutdown SIGTERM SIGINT

# Wait for both processes
wait $FASTAPI_PID $GRADIO_PID
