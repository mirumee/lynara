from typing import Any
from urllib.parse import unquote


def get_server(headers: dict[str, Any]) -> tuple[str, int]:
    server_name = headers.get("host", "lynara")
    parts = server_name.split(":")
    if len(parts) == 2:
        server_name = parts[0]
        server_port = parts[1]
    else:
        server_port = headers.get("x-forwarded-port", 80)
    return (server_name, int(server_port))


def strip_api_gateway_path(path: str, *, base_path: str | None = None) -> str:
    if not path:
        return "/"

    normalized_base_path = (
        f"/{base_path.lstrip('/')}" if base_path and base_path != "/" else ""
    )

    if path.startswith(normalized_base_path):
        path = path[len(normalized_base_path) :]

    return unquote(path)
