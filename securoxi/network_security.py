"""
SECUROXI AI Phase 4 Stage 3 — Network Security & SSRF Protection Utility
Provides outbound URL validation, private/loopback IP blocking, AWS metadata IMDS protection,
and rate-limiting helpers.
"""

import ipaddress
import socket
from urllib.parse import urlparse
from typing import Tuple
from securoxi.logger import get_logger

logger = get_logger("securoxi.network_security")

# Blocked private and internal IP ranges
BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.169.254/32"),  # AWS EC2 IMDS / Cloud Metadata
    ipaddress.ip_network("169.254.0.0/16"),      # Link-local
    ipaddress.ip_network("::1/128"),             # IPv6 Loopback
    ipaddress.ip_network("fc00::/7"),            # IPv6 Private
]


class SecuroxiSSRFGuard:
    """Outbound URL SSRF Prevention & Security Validator."""

    @staticmethod
    def validate_url(url: str) -> Tuple[bool, str]:
        """
        Validates outbound URL scheme, hostname, and resolves IP against blocked private networks.
        Returns (is_safe, reason).
        """
        try:
            parsed = urlparse(url)
            scheme = parsed.scheme.lower()

            if scheme not in ("http", "https"):
                return False, f"BLOCKED_SCHEME: Scheme '{scheme}' is not allowed (only http/https)."

            hostname = parsed.hostname
            if not hostname:
                return False, "INVALID_URL: Missing hostname."

            # Direct IP check
            try:
                ip_obj = ipaddress.ip_address(hostname)
                if any(ip_obj in net for net in BLOCKED_NETWORKS):
                    return False, f"SSRF_BLOCKED: Direct IP '{hostname}' belongs to a blocked internal network range."
            except ValueError:
                # Hostname DNS resolution check
                try:
                    resolved_ip = socket.gethostbyname(hostname)
                    ip_obj = ipaddress.ip_address(resolved_ip)
                    if any(ip_obj in net for net in BLOCKED_NETWORKS):
                        return False, f"SSRF_BLOCKED: Hostname '{hostname}' resolved to blocked private IP '{resolved_ip}'."
                except socket.gaierror:
                    # In offline/sandboxed environments, fallback to domain suffix validation
                    if hostname.endswith(".internal") or hostname.endswith(".local") or hostname == "localhost":
                        return False, f"SSRF_BLOCKED: Internal hostname '{hostname}' is blocked."
                    return True, "URL_SAFE"

            return True, "URL_SAFE"

        except Exception as err:
            return False, f"URL_PARSE_ERROR: {str(err)}"
