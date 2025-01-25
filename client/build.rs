use std::io;

fn main() -> io::Result<()> {
    tonic_build::configure()
        .compile_protos(
            &[
                "proto/types.proto",
                "proto/zab_peer.proto",
                "proto/zab_client.proto",
            ],
            &["proto"],
        )?;
    Ok(())
}