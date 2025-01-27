python3 main.py --id 1 --port 10001 --peers 2:localhost:10002,3:localhost:10003,4:localhost:10004 > script1.log 2>&1 &
PID1=$!
python3 main.py --id 2 --port 10002 --peers 1:localhost:10001,3:localhost:10003,4:localhost:10004 > script2.log 2>&1 &
PID2=$!
python3 main.py --id 3 --port 10003 --peers 1:localhost:10001,2:localhost:10002,4:localhost:10004 > script3.log 2>&1 &
PID3=$!
python3 main.py --id 4 --port 10004 --peers 1:localhost:10001,2:localhost:10002,3:localhost:10003 > script4.log 2>&1 &
PID4=$!
# Function to handle termination
cleanup() {
    echo "Terminating processes..."
    kill $PID1 $PID2 $PID3 $PID4 2>/dev/null
    wait $PID1 $PID2 $PID3 $PID4 2>/dev/null
    echo "Processes terminated."
    exit
}

# Trap SIGINT (Ctrl+C) and call cleanup
trap cleanup SIGINT

# Wait for both processes to complete
wait
