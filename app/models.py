"""SQLAlchemy models for ScribdDown CMS."""
from datetime import datetime, timezone
from sqlalchemy import (
    String, Text, Boolean, DateTime, Integer, ForeignKey, Table, Column,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def utcnow():
    return datetime.now(timezone.utc)


post_tags = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", ForeignKey("posts.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True),
)


class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value: Mapped[str] = mapped_column(Text, default="")


class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128))
    slug: Mapped[str] = mapped_column(String(128), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")


class Tag(Base):
    __tablename__ = "tags"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64))
    slug: Mapped[str] = mapped_column(String(64), unique=True)


class Post(Base):
    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255), unique=True)
    excerpt: Mapped[str] = mapped_column(Text, default="")
    content: Mapped[str] = mapped_column(Text, default="")  # HTML, shortcodes allowed
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    featured_image: Mapped[str] = mapped_column(String(512), default="")
    published: Mapped[bool] = mapped_column(Boolean, default=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    meta_title: Mapped[str] = mapped_column(String(255), default="")
    meta_description: Mapped[str] = mapped_column(String(512), default="")
    lang: Mapped[str] = mapped_column(String(8), default="en")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    category: Mapped[Category | None] = relationship()
    tags: Mapped[list[Tag]] = relationship(secondary=post_tags)


class Page(Base):
    __tablename__ = "pages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255), unique=True)
    content: Mapped[str] = mapped_column(Text, default="")  # HTML, shortcodes allowed
    published: Mapped[bool] = mapped_column(Boolean, default=False)
    meta_title: Mapped[str] = mapped_column(String(255), default="")
    meta_description: Mapped[str] = mapped_column(String(512), default="")
    lang: Mapped[str] = mapped_column(String(8), default="en")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class MenuItem(Base):
    __tablename__ = "menu_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    label: Mapped[str] = mapped_column(String(128))
    url: Mapped[str] = mapped_column(String(512))
    position: Mapped[int] = mapped_column(Integer, default=0)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("menu_items.id"), nullable=True)


class ContactMessage(Base):
    __tablename__ = "contact_messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128))
    email: Mapped[str] = mapped_column(String(255))
    subject: Mapped[str] = mapped_column(String(255), default="")
    message: Mapped[str] = mapped_column(Text)
    ip_hash: Mapped[str] = mapped_column(String(64), default="")
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
