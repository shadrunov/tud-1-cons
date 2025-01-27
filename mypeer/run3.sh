python3 main.py --id 1 --port 10001 --peers 2:localhost:10002,3:localhost:10003 > script1.log 2>&1 &
PID1=$!
python3 main.py --id 2 --port 10002 --peers 1:localhost:10001,3:localhost:10003 > script2.log 2>&1 &
PID2=$!
python3 main.py --id 3 --port 10003 --peers 1:localhost:10001,2:localhost:10002 > script3.log 2>&1 &
PID3=$!
# Function to handle termination
cleanup() {
    echo "Terminating processes..."
    kill $PID1 $PID2 $PID3 2>/dev/null
    wait $PID1 $PID2 $PID3 2>/dev/null
    echo "Processes terminated."
    exit
}

# Trap SIGINT (Ctrl+C) and call cleanup
trap cleanup SIGINT

# Wait for both processes to complete
wait
