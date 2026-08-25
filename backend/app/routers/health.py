from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
def health(request: Request) -> dict[str, object]:
    """Reports whether the LLM config was found at boot. A deployment can look
    healthy while every deliberation quietly returns stub reports, so this
    surfaces the one thing that failure mode otherwise hides."""
    return {
        "status": "ok",
        "settings_path": getattr(request.app.state, "settings_path", None),
        "settings_found": getattr(request.app.state, "settings_found", None),
    }
