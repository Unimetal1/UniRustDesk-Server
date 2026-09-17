# Bundled source dependency

`libsodium-sys` 0.2.7 is included because this server build uses its local
source package through `[patch.crates-io]`. The package originates from
revision `179e13c5bc3941e46f87f6748bfb3f9ed95936ba` and includes the bundled
libsodium 1.0.18 source.

The Rust wrapper is offered under MIT or Apache-2.0; both license texts are in
`libsodium-sys`. The bundled libsodium source carries its own ISC license in
`libsodium-sys/libsodium/LICENSE`.

The local build script only changes compiler/tool discovery so the dependency
can be built natively on Ubuntu and cross-compiled with explicitly configured
`CC`, `AR`, and `RANLIB` tools.
