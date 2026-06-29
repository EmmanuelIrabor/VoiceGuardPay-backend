
import math
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.location_ping import LocationPing

router = APIRouter()

NEARBY_RADIUS_METERS = 100          # generous for same-room / same-building
STALE_SECONDS = 30                  # ignore pings older than this


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _degree_delta(meters: float) -> float:
    """Rough degree delta for a metre distance (good enough for a bounding box)."""
    return meters / 111_320


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance in metres between two GPS points."""
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * R * math.asin(math.sqrt(a))


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class LocationUpdate(BaseModel):
    latitude: float
    longitude: float


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/update-location")
async def update_location(
    payload: LocationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upsert the caller's location ping.

    We use an explicit INSERT … ON CONFLICT DO UPDATE (via two-step
    get-then-set) but touch updated_at ourselves so the async ORM session
    doesn't miss the mutation.
    """
    now = datetime.now(timezone.utc)
    ping = await db.get(LocationPing, current_user.id)

    if ping is None:
        ping = LocationPing(
            user_id=current_user.id,
            latitude=payload.latitude,
            longitude=payload.longitude,
            updated_at=now,
        )
        db.add(ping)
    else:
        # Assign all three so SQLAlchemy marks the row dirty and emits UPDATE
        ping.latitude = payload.latitude
        ping.longitude = payload.longitude
        ping.updated_at = now

    await db.commit()
    return {"status": "updated"}


@router.get("/nearby")
async def get_nearby_users(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    my_ping = await db.get(LocationPing, current_user.id)
    if my_ping is None:
        return {"nearby": []}

    # --- Bounding box in SQL so the (lat, lng) index is used ---------------
    delta = _degree_delta(NEARBY_RADIUS_METERS)
    lat_min = my_ping.latitude - delta
    lat_max = my_ping.latitude + delta
    lng_min = my_ping.longitude - delta
    lng_max = my_ping.longitude + delta
    stale_cutoff = datetime.now(timezone.utc) - timedelta(seconds=STALE_SECONDS)

    result = await db.execute(
        select(LocationPing, User)
        .join(User, User.id == LocationPing.user_id)
        .where(
            LocationPing.user_id != current_user.id,
            LocationPing.latitude.between(lat_min, lat_max),
            LocationPing.longitude.between(lng_min, lng_max),
            LocationPing.updated_at >= stale_cutoff,   # drop ghost users
        )
    )

    # --- Exact haversine check on the much-smaller candidate set ------------
    nearby = []
    for ping, user in result.all():
        distance = haversine_distance(
            my_ping.latitude, my_ping.longitude,
            ping.latitude, ping.longitude,
        )
        if distance <= NEARBY_RADIUS_METERS:
            masked_account = (
                f"•••• {user.bank_account_number[-4:]}"
                if getattr(user, "bank_account_number", None)
                else "Not set"
            )
            nearby.append({
                "user_id": str(user.id),
                "name": user.name,
                "masked_account": masked_account,
                "distance_meters": round(distance, 1),
            })

    nearby.sort(key=lambda x: x["distance_meters"])
    return {"nearby": nearby}