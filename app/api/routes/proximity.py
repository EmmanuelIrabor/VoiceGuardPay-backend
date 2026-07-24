

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from geopy.distance import geodesic
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.location_ping import LocationPing

router = APIRouter()

NEARBY_RADIUS_METERS = 100
STALE_SECONDS = 300         
DEGREE_PER_METER = 1 / 111_320 




class LocationUpdate(BaseModel):
    latitude: float
    longitude: float




@router.post("/update-location")
async def update_location(
    payload: LocationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
  
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
        return {"nearby": [], "debug": "caller has no ping — push location first"}

    
    delta = NEARBY_RADIUS_METERS * DEGREE_PER_METER
    stale_cutoff = datetime.now(timezone.utc) - timedelta(seconds=STALE_SECONDS)

    result = await db.execute(
        select(LocationPing, User)
        .join(User, User.id == LocationPing.user_id)
        .where(
            LocationPing.user_id != current_user.id,
            LocationPing.latitude.between(
                my_ping.latitude - delta, my_ping.latitude + delta
            ),
            LocationPing.longitude.between(
                my_ping.longitude - delta, my_ping.longitude + delta
            ),
            LocationPing.updated_at >= stale_cutoff,
        )
    )

    nearby = []
    for ping, user in result.all():
        
        distance_m = geodesic(
            (my_ping.latitude, my_ping.longitude),
            (ping.latitude, ping.longitude),
        ).meters

        if distance_m <= NEARBY_RADIUS_METERS:
            masked_account = (
                f"•••• {user.bank_account_number[-4:]}"
                if getattr(user, "bank_account_number", None)
                else "Not set"
            )
            nearby.append({
                "user_id": str(user.id),
                "name": user.name,
                "masked_account": masked_account,
                "distance_meters": round(distance_m, 1),
            })

    nearby.sort(key=lambda x: x["distance_meters"])
    return {"nearby": nearby}


@router.get("/debug-ping")
async def debug_ping(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    
    ping = await db.get(LocationPing, current_user.id)
    if ping is None:
        return {
            "status": "no_ping",
            "message": "No location on record. The push hasn't landed yet.",
        }

    age_seconds = (datetime.now(timezone.utc) - ping.updated_at).total_seconds()
    stale = age_seconds > STALE_SECONDS

    return {
        "status": "stale" if stale else "fresh",
        "latitude": ping.latitude,
        "longitude": ping.longitude,
        "age_seconds": round(age_seconds, 1),
        "stale_threshold_seconds": STALE_SECONDS,
        "will_appear_in_nearby": not stale,
    }