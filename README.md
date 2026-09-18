# SerwisOnline (ServisOnline) — serwer

**Serwer SerwisOnline to zmodyfikowana wersja RustDesk Server (AGPL-3.0). Nie jest oficjalnym produktem RustDesk.**

Zmiany: uwierzytelnianie techników certyfikatami, szyfrowane i uwierzytelniane porty
techników, autoryzacja relay, lokalna historyczna biblioteka `hbb_common` zgodna
z klientem 1.3.6 oraz usunięte automatyczne sprawdzanie aktualizacji.

- Opis zmian i licencji: [NOTICE-CNG.md](NOTICE-CNG.md)
- Budowanie i uruchomienie (Ubuntu x86_64): [BUILDING-CNG.md](BUILDING-CNG.md)
- Licencja: GNU AGPL-3.0 — [LICENSE](LICENSE); program udostępniany bez gwarancji
- Źródła wydania: tag [`cng-1.3.6-2026-09-16`](https://github.com/Unimetal1/UniRustDesk-Server/tree/cng-1.3.6-2026-09-16)
- Klient: [UniRustDesk-Client](https://github.com/Unimetal1/UniRustDesk-Client)

Najważniejsze różnice w uruchomieniu:

- Porty: TCP 21115–21119 i UDP 21116. **Porty 21118 i 21119 są wymagane** —
  łączą się przez nie technicy z certyfikatem (w oryginalnym RustDesk służą
  klientowi webowemu i są opcjonalne).
- Certyfikaty publiczne (`.cer`) techników: katalog `technicians` lub wskazany
  zmienną `TECHNICIAN_WHITELIST_DIR`.
- Klucz serwera `id_ed25519` jest tworzony przy pierwszym starcie, jeśli go brak.
  Zachowaj go — klienci mają wbudowany odpowiadający mu klucz publiczny.
  Nie umieszczaj go w repozytorium.

Prawa autorskie Purslane Ltd. i pozostałych autorów RustDesk zostały zachowane.
Nazwa i logo RustDesk należą do ich właścicieli.

*This is a modified RustDesk Server (AGPL-3.0) used by ServisOnline.
It is not an official RustDesk product.*

---

> Poniżej oryginalny opis projektu RustDesk Server. Linki do pobierania, dokumentacji
> i RustDesk Server Pro prowadzą do oryginalnego projektu.

# RustDesk Server Program

[![build](https://github.com/rustdesk/rustdesk-server/actions/workflows/build.yaml/badge.svg)](https://github.com/rustdesk/rustdesk-server/actions/workflows/build.yaml)

[**Download**](https://github.com/rustdesk/rustdesk-server/releases)

[**Manual**](https://rustdesk.com/docs/en/self-host/)

[**Configuration & environment variables**](docs/environment-variables.md)

[**FAQ**](https://github.com/rustdesk/rustdesk/wiki/FAQ)

[**How to migrate OSS to Pro**](https://rustdesk.com/docs/en/self-host/rustdesk-server-pro/installscript/#convert-from-open-source)

Self-host your own RustDesk server, it is free and open source.

> [!IMPORTANT]
> **Need more features?** [RustDesk Server Pro](https://rustdesk.com/pricing.html) might suit you better.
>
> **Want to develop your own server?** Start with [rustdesk-server-demo](https://github.com/rustdesk/rustdesk-server-demo), a simpler starting point than this repository.

## How to build manually

```bash
cargo build --release
```

Three executables will be generated in target/release.

- hbbs - RustDesk ID/Rendezvous server
- hbbr - RustDesk relay server
- rustdesk-utils - RustDesk CLI utilities

You can find updated binaries on the [Releases](https://github.com/rustdesk/rustdesk-server/releases) page.

## Configuration

`hbbs` and `hbbr` can be configured with command-line flags, environment
variables, or an `.env` / config file. Run `hbbs --help` or `hbbr --help` to see
the available flags.

The most common options:

| Option | Flag | Env var | Applies to | Purpose |
| --- | --- | --- | --- | --- |
| Key | `-k` | `KEY` | hbbs, hbbr | `hbbs` loads/generates one by default |
| Bind address | `-b` | `BIND` | hbbs, hbbr | Local IP address to listen on (default: all interfaces; requires 1.1.17+) |
| Port | `-p` | `PORT` | hbbs, hbbr | Listening port (hbbs `21116`, hbbr `21117`) |
| Relay servers | `-r` | `RELAY-SERVERS` | hbbs | Override when the relay uses a different address or a non-standard port |
| Force relay | — | `ALWAYS_USE_RELAY` | hbbs | `Y` disables direct connections |
| Log level | — | `RUST_LOG` | hbbs, hbbr | e.g. `debug` (default `info`) |

See **[docs/environment-variables.md](docs/environment-variables.md)** for the
full list of variables, the file/flag/env precedence rules, database and relay
bandwidth tuning, Docker image variables, and examples.

## Installation

Please follow this [doc](https://rustdesk.com/docs/en/self-host/rustdesk-server-oss/)
