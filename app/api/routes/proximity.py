"""
GPS-based proximity discovery. Each device periodically reports its own
location; /nearby returns other users within a radius, excluding self.
"""

import math
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.location_ping import LocationPing

router = APIRouter()

NEARBY_RADIUS_METERS = 100  # generous for testing across a room/building


class LocationUpdate(BaseModel):
    latitude: float
    longitude: float


def haversine_distance(lat1, lon1, lat2, lon2) -> float:
    """Distance in meters between two GPS points."""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


@router.post("/update-location")
async def update_location(
    payload: LocationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ping = await db.get(LocationPing, current_user.id)
    if ping is None:
        ping = LocationPing(
            user_id=current_user.id,
            latitude=payload.latitude,
            longitude=payload.longitude,
        )
        db.add(ping)
    else:
        ping.latitude = payload.latitude
        ping.longitude = payload.longitude

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

    result = await db.execute(
        select(LocationPing, User)
        .join(User, User.id == LocationPing.user_id)
        .where(LocationPing.user_id != current_user.id)  # exclude self — explicit, not implicit
    )

    nearby = []
    for ping, user in result.all():
        distance = haversine_distance(my_ping.latitude, my_ping.longitude, ping.latitude, ping.longitude)
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