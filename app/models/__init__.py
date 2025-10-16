"""
Database models for unified IPTV platform
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, 
    Text, Float, UniqueConstraint, Index
)
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    
    # User status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_trial: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Limits
    max_connections: Mapped[int] = mapped_column(Integer, default=1)
    allowed_output_formats: Mapped[Optional[str]] = mapped_column(String(255))  # JSON list: ["ts", "m3u8"]
    
    # Dates
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expiry_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relationships
    sessions: Mapped[List["UserSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    activities: Mapped[List["UserActivity"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserSession(Base):
    """Active user sessions for connection tracking"""
    __tablename__ = "user_sessions"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Session info
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Stream info
    stream_id: Mapped[Optional[str]] = mapped_column(String(255))
    channel_id: Mapped[Optional[int]] = mapped_column(ForeignKey("channels.id"))
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_activity: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="sessions")
    channel: Mapped[Optional["Channel"]] = relationship()


class UserActivity(Base):
    """User activity log"""
    __tablename__ = "user_activities"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Activity details
    activity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # login, logout, stream_start, etc.
    description: Mapped[Optional[str]] = mapped_column(Text)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="activities")


class Channel(Base):
    """Channel model - combines AceStream and IPTV channels"""
    __tablename__ = "channels"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Channel identification
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    acestream_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True)
    stream_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Metadata
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"))
    logo_url: Mapped[Optional[str]] = mapped_column(String(500))
    epg_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    
    # Channel info
    language: Mapped[Optional[str]] = mapped_column(String(10))
    country: Mapped[Optional[str]] = mapped_column(String(50))
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_online: Mapped[Optional[bool]] = mapped_column(Boolean)
    last_checked: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_error: Mapped[Optional[str]] = mapped_column(Text)
    
    # Source info
    source_url_id: Mapped[Optional[int]] = mapped_column(ForeignKey("scraper_urls.id"))
    
    # Order
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    category: Mapped[Optional["Category"]] = relationship(back_populates="channels")
    source_url: Mapped[Optional["ScraperURL"]] = relationship(back_populates="channels")
    epg_programs: Mapped[List["EPGProgram"]] = relationship(back_populates="channel", cascade="all, delete-orphan")


class Category(Base):
    """Category model for channel organization"""
    __tablename__ = "categories"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"))
    
    # Display
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    icon_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    channels: Mapped[List["Channel"]] = relationship(back_populates="category")
    parent: Mapped[Optional["Category"]] = relationship(remote_side=[id])


class ScraperURL(Base):
    """URLs for scraping channels"""
    __tablename__ = "scraper_urls"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    
    # Settings
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    scraper_type: Mapped[str] = mapped_column(String(50), default="auto")  # auto, json, html, zeronet
    
    # Status
    last_scraped: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_success: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_error: Mapped[Optional[str]] = mapped_column(Text)
    channels_found: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    channels: Mapped[List["Channel"]] = relationship(back_populates="source_url")


class EPGSource(Base):
    """EPG data sources"""
    __tablename__ = "epg_sources"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    
    # Settings
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_gzipped: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Status
    last_updated: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_success: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_error: Mapped[Optional[str]] = mapped_column(Text)
    programs_found: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EPGProgram(Base):
    """EPG program data"""
    __tablename__ = "epg_programs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"), nullable=False)
    
    # Program info
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    
    # Additional metadata
    category: Mapped[Optional[str]] = mapped_column(String(100))
    icon_url: Mapped[Optional[str]] = mapped_column(String(500))
    rating: Mapped[Optional[str]] = mapped_column(String(10))
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    channel: Mapped["Channel"] = relationship(back_populates="epg_programs")
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_epg_channel_time', 'channel_id', 'start_time', 'end_time'),
    )


class Setting(Base):
    """Application settings"""
    __tablename__ = "settings"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
