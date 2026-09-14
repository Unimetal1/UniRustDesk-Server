use hbb_common::{
    anyhow::anyhow,
    protobuf::Message as _,
    rendezvous_proto::{rendezvous_message, KeyExchange, RendezvousMessage},
    tcp::{Encrypt, FramedStream},
    timeout, tokio, ResultType,
};
use ring::signature::{UnparsedPublicKey, RSA_PKCS1_2048_8192_SHA256};
use sodiumoxide::crypto::{box_, sign};

pub const ID_SERVER_ROLE: u8 = 0;
pub const RELAY_SERVER_ROLE: u8 = 1;

pub async fn secure_and_authenticate(
    stream: &mut FramedStream,
    server_key: &sign::SecretKey,
    server_role: u8,
) -> ResultType<()> {
    let (ephemeral_public_key, ephemeral_secret_key) = box_::gen_keypair();
    let mut key_exchange = RendezvousMessage::new();
    key_exchange.set_key_exchange(KeyExchange {
        keys: vec![sign::sign(ephemeral_public_key.as_ref(), server_key).into()],
        ..Default::default()
    });
    timeout(5_000, stream.send(&key_exchange)).await??;

    let reply = match timeout(5_000, stream.next()).await? {
        Some(result) => result?,
        None => return Err(anyhow!("Key exchange disconnected")),
    };
    let reply = RendezvousMessage::parse_from_bytes(&reply)?;
    let exchange = match reply.union {
        Some(rendezvous_message::Union::KeyExchange(exchange)) if exchange.keys.len() == 2 => {
            exchange
        }
        _ => return Err(anyhow!("Invalid key exchange response")),
    };
    let symmetric_key =
        Encrypt::decode(&exchange.keys[1], &exchange.keys[0], &ephemeral_secret_key)?;
    stream.set_key(symmetric_key);
    authenticate(stream, server_role).await
}

async fn authenticate(stream: &mut FramedStream, server_role: u8) -> ResultType<()> {
    let mut challenge = b"RustDesk technician v1\0".to_vec();
    challenge.push(server_role);
    challenge.extend(sodiumoxide::randombytes::randombytes(32));

    timeout(5_000, stream.send_raw(challenge.clone())).await??;
    let signature = match timeout(15_000, stream.next()).await? {
        Some(result) => result?,
        None => return Err(anyhow!("Certificate authentication disconnected")),
    };
    if signature.len() < 384 || signature.len() > 1024 {
        return Err(anyhow!("Invalid RSA signature size"));
    }

    tokio::task::spawn_blocking(move || verify_signature(&challenge, &signature)).await??;
    timeout(5_000, stream.send_raw(b"OK".to_vec())).await??;
    Ok(())
}

fn verify_signature(challenge: &[u8], signature: &[u8]) -> ResultType<()> {
    let directory = match std::env::var("TECHNICIAN_WHITELIST_DIR") {
        Ok(value) => value,
        Err(_) => "technicians".to_owned(),
    };
    for entry in std::fs::read_dir(directory)? {
        let path = entry?.path();
        let extension = match path.extension() {
            Some(value) => value,
            None => continue,
        };
        if extension != "cer" {
            continue;
        }
        let file_size = std::fs::metadata(&path)?.len();
        if file_size > 16_384 {
            return Err(anyhow!("Certificate too large"));
        }

        let certificate_bytes = std::fs::read(&path)?;
        let (remaining_bytes, certificate) =
            match x509_parser::parse_x509_certificate(&certificate_bytes) {
                Ok(parsed_certificate) => parsed_certificate,
                Err(error) => {
                    return Err(anyhow!("Invalid certificate {}: {error}", path.display()))
                }
            };
        if !remaining_bytes.is_empty() {
            return Err(anyhow!("Trailing certificate data"));
        }
        let public_key_bytes = certificate.public_key().subject_public_key.data.as_ref();
        let public_key = UnparsedPublicKey::new(&RSA_PKCS1_2048_8192_SHA256, public_key_bytes);
        if certificate.validity().is_valid() && public_key.verify(challenge, signature).is_ok() {
            return Ok(());
        }
    }
    Err(anyhow!(
        "Technician signature is not authorized by the certificate whitelist"
    ))
}
