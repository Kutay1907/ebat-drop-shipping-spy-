#!/usr/bin/env python3
"""
Generate a secure encryption key for eBay OAuth token storage.
This key is used with Fernet symmetric encryption to protect user tokens.
"""

import secrets
import base64
from cryptography.fernet import Fernet

def generate_fernet_key():
    """Generate a valid Fernet encryption key."""
    # Fernet.generate_key() creates a URL-safe base64-encoded 32-byte key
    return Fernet.generate_key().decode()

def generate_simple_key():
    """Generate a simple 32-character key using secrets."""
    # Generate 24 random bytes and encode to base64 (results in 32 chars)
    return base64.urlsafe_b64encode(secrets.token_bytes(24)).decode()

if __name__ == "__main__":
    print("=" * 60)
    print("eBay OAuth Encryption Key Generator")
    print("=" * 60)
    print()
    
    # Generate a proper Fernet key
    fernet_key = generate_fernet_key()
    print("Recommended Fernet Key (use this):")
    print(f"ENCRYPTION_KEY={fernet_key}")
    print()
    
    print("This key will be used to encrypt/decrypt eBay OAuth tokens.")
    print("Keep this key SECRET and never commit it to version control!")
    print()
    print("Add this to your .env file or Railway environment variables.")
    print("=" * 60) 