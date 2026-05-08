from starlette.requests import Request


def add_flash(request: Request, level: str, message: str) -> None:
    flashes = request.session.get("flashes", [])
    flashes.append({"level": level, "message": message})
    request.session["flashes"] = flashes


def pop_flashes(request: Request) -> list[dict]:
    flashes = request.session.get("flashes", [])
    request.session["flashes"] = []
    return flashes
