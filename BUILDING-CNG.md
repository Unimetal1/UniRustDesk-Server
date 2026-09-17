# Building the CNG server on Ubuntu x86_64

This repository contains the modified server, its historical `hbb_common`,
and the locally patched `libsodium-sys` dependency under `third_party/`. It does not
require files from a sibling `.build-tools` directory.

Install a Rust toolchain and the native build tools required by the locked
dependencies. On Ubuntu:

```sh
sudo apt update
sudo apt install build-essential clang cmake git perl pkg-config libsqlite3-dev
rustup toolchain install 1.97.1
rustup override set 1.97.1
cargo build --locked --release --bins
```

The deployment binaries are `target/release/hbbs` and
`target/release/hbbr`. Check them before deployment:

```sh
./target/release/hbbs --help
./target/release/hbbr --help
ldd ./target/release/hbbs
ldd ./target/release/hbbr
```

Keep deployment data outside the public repository. In particular, do not
commit `.env`, `db_v2.sqlite3*`, `id_ed25519`, private certificates, or the
`technicians/` deployment directory. When updating an existing installation,
preserve its server key, database and technician whitelist.

Run both binaries with the same working directory. The ID server must receive
the relay address, for example:

```sh
./hbbr
./hbbs -r SERVER_ADDRESS:21117
```

The modified server uses TCP ports 21115–21119 and UDP port 21116. Ports
21118 and 21119 authenticate technicians using public certificates from the
configured whitelist.
