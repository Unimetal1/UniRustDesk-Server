# Historical source restoration

Base: `rustdesk-server` commit `772db7422f679db1fa06be1097cd676a73055851`,
directory `libs/hbb_common`, immediately before extraction in `7a509f6`.
The historical repository license is in its root `LICENSE` (GNU AGPL v3).

The backup in `libs/hbb_common - kopia` has no local changes relative to its
submodule HEAD. It remains unchanged. No newer library sources were copied.

Compatibility changes:
- The `KeyExchange` protocol and encryption helper originate in the historical
  client revision `4b066b1fbaa8d5d6f9b53cb1e5b25e484f229da1`, plus the user's
  transport/session encryption changes. These support certificate authentication.
- The listener call uses the historical explicit address-reuse parameter.
- The newer automatic software-update check was removed; the historical server
  had no such check.
- The lockfile selects `signature` 1.6.4, compatible with `ed25519` 1.5.0.

Validation: `cargo check --manifest-path rustdesk-server/Cargo.toml --bins` passes.
The debug binaries build, all seven server library tests pass, and the existing
certificate integration test passes using the debug binaries and the local LAN
address (loopback is reserved for the server administration console).
The integration test covers valid authentication, replay rejection, expired
certificates, bidirectional relay traffic, and rejection of unauthenticated
technicians. Its test harness was executed with log handles closed after launch
so temporary directory cleanup works on Windows.
