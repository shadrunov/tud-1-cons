# TODO: Place your peer build command here
# cargo build --release --target x86_64-unknown-linux-gnu
docker build -f Dockerfile.peer -t peer_app .
docker build -f Dockerfile.client -t client_app .