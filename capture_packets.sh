#!/bin/bash

# Variables
SERVER_IP=0.0.0.0
CAPTURE_INTERFACE=eth0
CLIENT_CAPTURE_FILE=client_capture.pcap
SERVER_CAPTURE_FILE=server_capture.pcap
FILTERED_LOG_FILE=filtered_packets.log

# Function to start tcpdump
start_tcpdump() {
    echo "Starting tcpdump on $CAPTURE_INTERFACE..."
    tcpdump -i $CAPTURE_INTERFACE -w $1 port 8000 &
    TCPDUMP_PID=$!
    echo "tcpdump started with PID $TCPDUMP_PID"
}

# Function to stop tcpdump
stop_tcpdump() {
    echo "Stopping tcpdump with PID $TCPDUMP_PID..."
    kill $TCPDUMP_PID
    echo "tcpdump stopped"
}

# Function to run the client requests
run_client_requests() {
    echo "Running client requests..."
    python3 video_client.py
}

# Function to filter captured packets and save to log file
filter_packets() {
    echo "Filtering captured packets..."
    tcpdump -r $1 'tcp port 8000' -w $2
    echo "Filtered packets saved to $2"
}

# Main script
start_tcpdump $CLIENT_CAPTURE_FILE
run_client_requests
stop_tcpdump
filter_packets $CLIENT_CAPTURE_FILE $FILTERED_LOG_FILE
