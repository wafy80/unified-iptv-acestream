"""
Authentication utilities
"""
from datetime import datetime, timedelta
from typing import Optional

from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.models import User
from app.config import get_config

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    config = get_config()
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=config.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.secret_key, algorithm="HS256")
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify a JWT token"""
    config = get_config()
    try:
        payload = jwt.decode(token, config.secret_key, algorithms=["HS256"])
        return payload
    except JWTError:
        return None


def verify_user(db: Session, username: str, password: str) -> Optional[User]:
    """Verify user credentials"""
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        return None
    
    if not verify_password(password, user.password_hash):
        return None
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    return user


def create_user(
    db: Session,
    username: str,
    password: str,
    email: Optional[str] = None,
    is_admin: bool = False,
    is_trial: bool = False,
    max_connections: int = 1,
    expiry_date: Optional[datetime] = None
) -> User:
    """Create a new user"""
    user = User(
        username=username,
        password_hash=get_password_hash(password),
        email=email,
        is_admin=is_admin,
        is_trial=is_trial,
        max_connections=max_connections,
        expiry_date=expiry_date
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


# Dependency for FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = None
SessionLocal = None


def init_db():
    """Initialize database"""
    global engine, SessionLocal
    config = get_config()
    
    engine = create_engine(
        config.database_url,
        echo=config.database_echo,
        pool_size=config.database_pool_size,
        max_overflow=config.database_max_overflow
    )
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create all tables
    from app.models import Base
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session (FastAPI dependency)"""
    if SessionLocal is None:
        init_db()
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
