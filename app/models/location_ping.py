import uuid
from datetime import datetime, timezone

from sqlalchemy import Float, DateTime, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class LocationPing(Base):
    __tablename__ = "location_pings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True
    )
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    # server_default + explicit assignment in routes = reliable across async sessions.
    # Do NOT rely on onupdate alone — async SQLAlchemy doesn't always fire it on
    # attribute mutation without an explicit flush.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        # Composite index so the bounding-box WHERE lat BETWEEN / lng BETWEEN
        # clause in /nearby hits an index scan instead of a full table scan.
        Index("ix_location_pings_lat_lng", "latitude", "longitude"),
    )