from sqlalchemy.orm import Session
from . import models, security
from datetime import datetime, timedelta

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, email: str):
    db_user = models.User(email=email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_token_for_user(db: Session, user_id: int):
    return db.query(models.EbayOAuthToken).filter(models.EbayOAuthToken.user_id == user_id).first()

def update_or_create_token(db: Session, user_id: int, token_data: dict):
    # Calculate expiration dates
    access_token_expires_in = token_data.get("expires_in", 7200)
    refresh_token_expires_in = token_data.get("refresh_token_expires_in", 47304000) # 18 months
    
    access_token_expires_at = datetime.utcnow() + timedelta(seconds=access_token_expires_in)
    refresh_token_expires_at = datetime.utcnow() + timedelta(seconds=refresh_token_expires_in)

    # Encrypt tokens
    encrypted_access_token = security.encrypt_token(token_data["access_token"])
    encrypted_refresh_token = security.encrypt_token(token_data["refresh_token"])

    # Find existing token
    db_token = get_token_for_user(db, user_id)

    if db_token:
        # Update existing token
        db_token.encrypted_access_token = encrypted_access_token
        db_token.encrypted_refresh_token = encrypted_refresh_token
        db_token.access_token_expires_at = access_token_expires_at
        db_token.refresh_token_expires_at = refresh_token_expires_at
    else:
        # Create new token
        db_token = models.EbayOAuthToken(
            user_id=user_id,
            encrypted_access_token=encrypted_access_token,
            encrypted_refresh_token=encrypted_refresh_token,
            access_token_expires_at=access_token_expires_at,
            refresh_token_expires_at=refresh_token_expires_at
        )
        db.add(db_token)
    
    db.commit()
    db.refresh(db_token)
    return db_token 