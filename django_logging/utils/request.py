"""Verified, low-cost client IP resolution for Django and DRF requests."""

from functools import lru_cache
from ipaddress import IPv4Address, IPv6Address, ip_address, ip_network
from typing import Optional

from django.http import HttpRequest


def _parse_ip(value: object) -> IPv4Address | IPv6Address | None:
    if not isinstance(value, str):
        return None
    try:
        return ip_address(value.strip())
    except ValueError:
        return None


@lru_cache(maxsize=32)
def trusted_networks(cidrs: tuple[str, ...]) -> tuple:
    # Inputs have been validated before the middleware is activated.
    return tuple(ip_network(value, strict=True) for value in cidrs)


def get_ip_address(
    request: HttpRequest, proxy_cidrs: tuple[str, ...] = ()
) -> Optional[str]:
    """Trust X-Real-IP only when REMOTE_ADDR belongs to a configured proxy.

    The reverse proxy must *overwrite* client-supplied X-Real-IP.
    Arbitrary X-Forwarded-For lists are never trusted. A DRF request
    shares its cache with the underlying Django request.

    """
    django_request = getattr(request, "_request", request)
    cache = django_request.__dict__.get("_django_logging_verified_ip")
    if cache is not None and cache[0] == proxy_cidrs:
        return cache[1]

    peer = _parse_ip(django_request.META.get("REMOTE_ADDR"))
    result = str(peer) if peer is not None else None
    if peer is not None and proxy_cidrs:
        if any(peer in network for network in trusted_networks(proxy_cidrs)):
            forwarded = _parse_ip(django_request.META.get("HTTP_X_REAL_IP"))
            if forwarded is not None:
                result = str(forwarded)
    django_request.__dict__["_django_logging_verified_ip"] = (proxy_cidrs, result)
    return result
