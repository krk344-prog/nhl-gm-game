#!/usr/bin/env python3
"""Select a non-loopback LAN API endpoint for a Technical Alpha APK build."""

from __future__ import annotations

import argparse
import ipaddress
import json
import socket
import sys
from dataclasses import asdict, dataclass
from typing import Iterable


@dataclass(frozen=True)
class EndpointSelection:
    recommended_api_base_url: str
    candidate_api_base_urls: tuple[str, ...]
    host_count: int
    ready: bool


def _usable_private_ipv4(addresses: Iterable[str]) -> tuple[str, ...]:
    usable: set[str] = set()
    for value in addresses:
        try:
            address = ipaddress.ip_address(value)
        except ValueError:
            continue
        if (
            address.version == 4
            and address.is_private
            and not address.is_loopback
            and not address.is_link_local
            and not address.is_multicast
            and not address.is_unspecified
            and not address.is_reserved
        ):
            usable.add(str(address))
    return tuple(sorted(usable, key=lambda item: tuple(int(part) for part in item.split("."))))


def discover_private_ipv4_addresses() -> tuple[str, ...]:
    """Return stable, deduplicated private IPv4 addresses for this host."""

    discovered: set[str] = set()
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            discovered.add(info[4][0])
    except socket.gaierror:
        pass

    # UDP connect selects the host interface used for ordinary outbound routing.
    # No packet is sent by this operation.
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("192.0.2.1", 9))
        discovered.add(probe.getsockname()[0])
    except OSError:
        pass
    finally:
        probe.close()

    return _usable_private_ipv4(discovered)


def select_endpoint(
    addresses: Iterable[str],
    *,
    port: int = 8000,
    api_prefix: str = "/api/v1",
) -> EndpointSelection:
    if not 1 <= port <= 65535:
        raise ValueError("port must be between 1 and 65535")

    prefix = "/" + api_prefix.strip("/")
    hosts = _usable_private_ipv4(addresses)
    if not hosts:
        raise RuntimeError(
            "No non-loopback private IPv4 address was found. Connect the facilitator "
            "computer to the trusted tester network before building the APK."
        )

    urls = tuple(f"http://{host}:{port}{prefix}" for host in hosts)
    return EndpointSelection(
        recommended_api_base_url=urls[0],
        candidate_api_base_urls=urls,
        host_count=len(hosts),
        ready=True,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--api-prefix", default="/api/v1")
    args = parser.parse_args(argv)

    try:
        result = select_endpoint(
            discover_private_ipv4_addresses(),
            port=args.port,
            api_prefix=args.api_prefix,
        )
    except (ValueError, RuntimeError) as exc:
        print(json.dumps({"ready": False, "error": str(exc)}, indent=2))
        return 1

    print(json.dumps(asdict(result), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
