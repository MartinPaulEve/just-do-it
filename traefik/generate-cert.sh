#!/bin/bash
set -e

CERT_DIR="/etc/traefik/certs"

if [ ! -f "$CERT_DIR/cert.pem" ]; then
    echo "Generating self-signed certificate..."
    mkdir -p "$CERT_DIR"
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$CERT_DIR/key.pem" \
        -out "$CERT_DIR/cert.pem" \
        -subj "/C=GB/ST=Dev/L=Dev/O=Dev/CN=localhost"
    echo "Certificate generated."
else
    echo "Certificate already exists, skipping generation."
fi

exec "$@"
