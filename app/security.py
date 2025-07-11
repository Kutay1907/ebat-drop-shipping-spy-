import os
from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if not ENCRYPTION_KEY:
    raise ValueError("ENCRYPTION_KEY not found in environment variables. Please set it in your .env file.")

fernet = Fernet(ENCRYPTION_KEY.encode())

def encrypt_token(token: str) -> str:
    """Encrypts a token using Fernet symmetric encryption."""
    if not token:
        return ""
    return fernet.encrypt(token.encode()).decode()

def decrypt_token(encrypted_token: str) -> str:
    """Decrypts a token, raising an HTTPException on failure."""
    if not encrypted_token:
        return ""
    try:
        return fernet.decrypt(encrypted_token.encode()).decode()
    except InvalidToken:
        raise HTTPException(status_code=500, detail="Failed to decrypt token; it may be invalid or corrupted.")
    except Exception:
        raise HTTPException(status_code=500, detail="An unexpected error occurred during token decryption.") 