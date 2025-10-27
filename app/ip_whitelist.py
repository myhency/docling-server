"""IP-based access control middleware."""
from typing import List
from fastapi import Request, HTTPException, status
from ipaddress import ip_address, ip_network, IPv4Address, IPv6Address


def is_ip_allowed(client_ip: str, allowed_ips: List[str]) -> bool:
    """
    Check if the client IP is in the allowed list.

    Supports:
    - Individual IPs: "127.0.0.1", "::1"
    - CIDR notation: "192.168.1.0/24", "10.0.0.0/8"

    Args:
        client_ip: Client IP address
        allowed_ips: List of allowed IPs or CIDR ranges

    Returns:
        True if IP is allowed, False otherwise
    """
    try:
        client = ip_address(client_ip)

        for allowed in allowed_ips:
            try:
                # Check if it's a CIDR range
                if '/' in allowed:
                    network = ip_network(allowed, strict=False)
                    if client in network:
                        return True
                else:
                    # Check if it's an individual IP
                    if client == ip_address(allowed):
                        return True
            except ValueError:
                # Invalid IP/CIDR format, skip
                continue

        return False

    except ValueError:
        # Invalid client IP
        return False


async def verify_ip_whitelist(request: Request, allowed_ips: List[str]):
    """
    Verify that the client IP is in the whitelist.

    Args:
        request: FastAPI request object
        allowed_ips: List of allowed IPs or CIDR ranges

    Raises:
        HTTPException: If IP is not in whitelist
    """
    # Get client IP from request
    # Try X-Forwarded-For first (if behind proxy)
    client_ip = request.headers.get("X-Forwarded-For")

    if client_ip:
        # X-Forwarded-For can contain multiple IPs, take the first one
        client_ip = client_ip.split(',')[0].strip()
    else:
        # Get IP from request.client
        client_ip = request.client.host if request.client else None

    if not client_ip:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unable to determine client IP"
        )

    # Check if IP is allowed
    if not is_ip_allowed(client_ip, allowed_ips):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied for IP: {client_ip}"
        )

    return client_ip


def get_client_ip(request: Request) -> str:
    """
    Extract client IP from request.

    Args:
        request: FastAPI request object

    Returns:
        Client IP address
    """
    # Try X-Forwarded-For first (if behind proxy)
    client_ip = request.headers.get("X-Forwarded-For")

    if client_ip:
        # X-Forwarded-For can contain multiple IPs, take the first one
        client_ip = client_ip.split(',')[0].strip()
    else:
        # Get IP from request.client
        client_ip = request.client.host if request.client else "unknown"

    return client_ip
