python3 main.py --id 1 --port 10001 --peers 2:localhost:10002 > script1.log 2>&1 &
PID1=$!
python3 main.py --id 2 --port 10002 --peers 1:localhost:10001 > script2.log 2>&1 &
PID2=$!

# Function to handle termination
cleanup() {
    echo "Terminating processes..."
    kill $PID1 $PID2 2>/dev/null
    wait $PID1 $PID2 2>/dev/null
    echo "Processes terminated."
    exit
}

# Trap SIGINT (Ctrl+C) and call cleanup
trap cleanup SIGINT

# Wait for both processes to complete
wait
