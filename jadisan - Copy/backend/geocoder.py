"""
geocoder.py
Geocodes text location strings to (lat, lng) using OpenStreetMap Nominatim.
Rate-limited to 1 request/second per Nominatim ToS.
"""
import asyncio
import logging
from typing import Optional

from geopy.geocoders import Nominatim # type: ignore
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from geopy.extra.rate_limiter import RateLimiter
logger = logging.getLogger(__name__)

_geocoder = Nominatim(user_agent="jadisan_civic_app")

# Simple in-process cache to avoid repeated Nominatim calls for the same string.
_cache: dict[str, Optional[tuple[float, float]]] = {}

# Lock to serialise requests (Nominatim ToS: 1 req/sec).
_lock = asyncio.Lock()


async def geocode_location(location_text: str) -> Optional[tuple[float, float]]:
    """
    Convert a free-text location string to (latitude, longitude).

    Returns None if the location cannot be resolved.
    """
    if not location_text or not location_text.strip():
        return None

    key = location_text.strip().lower()
    if key in _cache:
        return _cache[key]

    async with _lock:
        # Respect Nominatim's 1 req/sec rate limit.
        await asyncio.sleep(1)
        try:
            location = await asyncio.to_thread(
            _geocoder.geocode,
            location_text,
            exactly_one=True,
            timeout=10,
            country_codes="in",   # restrict results to India — fixes cross-country mismatches
            )            
            if location:
                result = (location.latitude, location.longitude)
                logger.info(
                    "Geocoded '%s' → %s", location_text, result
                )
            else:
                result = None
                logger.warning("Nominatim could not geocode: '%s'", location_text)
        except (GeocoderTimedOut, GeocoderUnavailable) as exc:
            logger.error("Geocoder error for '%s': %s", location_text, exc)
            result = None

    _cache[key] = result
    return result


_reverse_cache: dict[str, Optional[str]] = {}


async def reverse_geocode(lat: float, lng: float) -> Optional[str]:
    """
    Convert (latitude, longitude) coordinates to a human-readable street address using Nominatim.
    """
    key = f"{round(lat, 5)},{round(lng, 5)}"
    if key in _reverse_cache:
        return _reverse_cache[key]

    async with _lock:
        await asyncio.sleep(1)
        try:
            location = await asyncio.to_thread(
                _geocoder.reverse,
                (lat, lng),
                exactly_one=True,
                timeout=10,
            )
            if location and hasattr(location, "address"):
                result = str(location.address)
                logger.info("Reverse geocoded (%s, %s) → '%s'", lat, lng, result)
            else:
                result = None
        except (GeocoderTimedOut, GeocoderUnavailable) as exc:
            logger.error("Reverse geocoder error for (%s, %s): %s", lat, lng, exc)
            result = None

    _reverse_cache[key] = result
    return result

