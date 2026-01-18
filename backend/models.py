from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import create_engine
import os

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///neighbourly.db')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# Use connection pooling to avoid connection overhead on every request
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=300  # Recycle connections every 5 minutes
)

__all__ = ['Base', 'Account', 'Order', 'OrderItem', 'Message', 'engine', 'DATABASE_URL']


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "account"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)


class Order(Base):
    __tablename__ = "order"
    id: Mapped[int] = mapped_column(primary_key=True)
    message: Mapped[str] = mapped_column(nullable=False)
    account_id: Mapped[int] = mapped_column(nullable=False)
    lat: Mapped[str] = mapped_column(nullable=False)
    lng: Mapped[str] = mapped_column(nullable=False)
    address: Mapped[str] = mapped_column(nullable=False)
    collectionTime: Mapped[str] = mapped_column(nullable=False)
    collectionDate: Mapped[str] = mapped_column(nullable=True)  # Format: YYYY-MM-DD
    fulfilled: Mapped[int] = mapped_column(nullable=True)


class OrderItem(Base):
    __tablename__ = "order_item"
    item_id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)


class Message(Base):
    __tablename__ = "message"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(nullable=False)
    sender_email: Mapped[str] = mapped_column(nullable=False)
    content: Mapped[str] = mapped_column(nullable=False)
    timestamp: Mapped[str] = mapped_column(nullable=False)


Base.metadata.create_all(engine)
