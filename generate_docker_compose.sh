#!/bin/bash

# Define the number of peers
NUM_PEERS=$1

# Check if number of peers is at least 3
if [[ $NUM_PEERS -lt 3 ]]; then
  echo "Number of peers must be at least 3."
  exit 1
fi

# Start the Docker Compose YAML file
echo "version: '3'" > docker-compose.yml
echo "services:" >> docker-compose.yml

# Loop to define each peer service
for (( id=1; id<=NUM_PEERS; id++ ))
do
  # Define the port for this peer
  port=$((10000 + id))

  # Create a list of other peers in the format id:hostname:port
  peers=""
  for (( other_id=1; other_id<=NUM_PEERS; other_id++ ))
  do
    if [[ $other_id -ne $id ]]; then
      # Calculate the port for the other peer
      other_port=$((10000 + other_id))
      # Use the service name as the hostname
      peers+="${other_id}:peer${other_id}:${other_port},"
    fi
  done
  # Remove the trailing comma
  peers=${peers%,}

  # Add service to the docker-compose.yml file for peer
  cat <<EOF >> docker-compose.yml
  peer$id:
    image: peer_app
    container_name: peer$id
    command: --id $id --port $port --peers $peers
    ports:
      - "$port:$port"
EOF
done

# Add client_app service to the docker-compose.yml file
client_peers=""
for (( id=1; id<=NUM_PEERS; id++ ))
do
  # Calculate the port for the peer
  port=$((10000 + id))
  # Add the peer in the format peer_name:peer_port
  client_peers+="peer${id}:${port},"
done
# Remove the trailing comma
client_peers=${client_peers%,}

# Add client service definition to docker-compose.yml
cat <<EOF >> docker-compose.yml
  client_app:
    image: client_app
    container_name: client_app
    command: --peers $client_peers
    depends_on:
      - peer1
      - peer2
      - peer3
    volumes:
      - ./logs:/logs
EOF

echo "Generated docker-compose.yml for $NUM_PEERS peers using the peer_app image and client_app."
