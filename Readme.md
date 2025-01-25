# CONS Project

## Requirements

1. Rust
   1. Go to [https://www.rust-lang.org/tools/install](https://www.rust-lang.org/tools/install) and execute the command shown there.
   2. Install cross, which enables you to easily cross-compile the client on different operating systems, just run: `cargo install cross --git https://github.com/cross-rs/cross`
2. Docker
   1. Go to [https://docs.docker.com/engine/install/](https://docs.docker.com/engine/install/) and follow the installation instructions based on your operating system
   2. You may also have to install docker-compose if its not installed together with docker [https://docs.docker.com/compose/install/](https://docs.docker.com/compose/install/)

> **_Hint_** Make sure that docker is running before continuing

## Building the client binary

1. `cd client`
2. Run `cargo build --release x86_64-unknown-linux-gnu` (as the docker container should be x86), depending on your operating system this could fail, then you should try replacing `cargo` with `cross`, so `cross build --release x86_64-unknown-linux-gnu`
3. The binary should be created inside `target/x86_64-unknown-linux-gnu/release/client` inside the client folder

## Peer binary

There are multiple peer files: peer (x86), peer-x86-x, and peer-aarch64-x. When utilizing the docker-compose you should use the peer (x86-linux) version.

## Generating the docker containers

Execute `./build_docker_containers.sh`, this will create a container called `client_app` and `peer_app`.

> **_Hint_** You may have to adapt the path to the client binary inside the `Dockerfile.client` inside the COPY command: `COPY {PATH_TO_CLIENT_BINARY} .`

> **_Hint_** The same applies for your peer implementation as the Dockerfile.peer currently copies our peer binary.
> You may also have to adapt the command to execute you peer if its not a binary, e.g., `ENTRYPOINT ["python peer.py"]`

## Starting the containers using docker-compose

1. Execute `./generate_docker_compose.sh {NUMBER_OF_PEERS | start with 3}`
2. Run `docker-compose up --build --remove-orphans`
3. You can stop using either `CTRL+C` or `docker-compose down` when you ran it in background

> **_Hint_** Remember to always execute at least these commands before running a new version of your code:
>
> 1.Build your peer code, e.g, using go build (doesn't apply for interpreted languages like python) or better add your build command at the beginning of the `build_docker_containers.sh`
> 2. Run `./build_docker_containers.sh`
> 3. Only then (re)start the docker-compose
