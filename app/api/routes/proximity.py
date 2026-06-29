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


# proximity.py - Optimized version

@router.get("/nearby")
async def get_nearby_users(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    my_ping = await db.get(LocationPing, current_user.id)
    if my_ping is None:
        return {"nearby": []}

    # Use SQL for distance calculation - much faster
    # This uses PostGIS if available, or a simplified version
    from sqlalchemy import func, text
    
    # Get all pings except self with distance calculation
    # Assuming lat/lon columns exist
    stmt = text("""
        SELECT 
            u.id as user_id,
            u.name,
            u.bank_account_number,
            lp.latitude,
            lp.longitude,
            earth_distance(
                ll_to_earth(:my_lat, :my_lon),
                ll_to_earth(lp.latitude, lp.longitude)
            ) as distance_meters
        FROM location_pings lp
        JOIN users u ON u.id = lp.user_id
        WHERE lp.user_id != :my_user_id
        AND earth_distance(
            ll_to_earth(:my_lat, :my_lon),
            ll_to_earth(lp.latitude, lp.longitude)
        ) <= :radius
        ORDER BY distance_meters ASC
    """)
    
    result = await db.execute(
        stmt,
        {
            "my_lat": my_ping.latitude,
            "my_lon": my_ping.longitude,
            "my_user_id": current_user.id,
            "radius": NEARBY_RADIUS_METERS
        }
    )
    
    nearby = []
    for row in result:
        masked_account = (
            f"•••• {row.bank_account_number[-4:]}"
            if row.bank_account_number else "Not set"
        )
        nearby.append({
            "user_id": str(row.user_id),
            "name": row.name,
            "masked_account": masked_account,
            "distance_meters": round(row.distance_meters, 1),
        })
    
    return {"nearby": nearby}