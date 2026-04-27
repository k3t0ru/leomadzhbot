from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, Float, ForeignKey, func, text, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    
    profile: Mapped["Profile"] = relationship("Profile", back_populates="user", uselist=False)
    preferences: Mapped["UserPreference"] = relationship("UserPreference", back_populates="user", uselist=False)

class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(10), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    interests: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    photo_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    photos_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    completeness_score: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0")
    
    user: Mapped["User"] = relationship("User", back_populates="profile")

class UserPreference(Base):
    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    min_age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    preferred_gender: Mapped[str | None] = mapped_column(String(10), nullable=True)
    preferred_city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    user: Mapped["User"] = relationship("User", back_populates="preferences")

class ProfileInteraction(Base):
    __tablename__ = "profile_interactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    from_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    to_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    interaction_type: Mapped[str] = mapped_column(String(20)) # "LIKE", "SKIP", "MATCH"
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

