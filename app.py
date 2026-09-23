from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from dragon_core.engine import dragon_engine
from dragon_core.security import security


app = FastAPI(
    title="DRAGON AI CORE",
    version="1.2.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


@app.get("/")
def root():
    return {
        "system": "DRAGON AI CORE",
        "status": "online",
        "version": "1.2.0"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/chat")
def chat(request: ChatRequest):
    return dragon_engine.process(request.message)


# ==========================================================
# Security Status
# ==========================================================

@app.get("/security/status")
def security_status():
    return security.get_status()


# ==========================================================
# Security Kill Switch Test
# ==========================================================

@app.post("/security/test-kill-switch")
def test_kill_switch():
    """
    Temporary non-destructive Kill Switch test.

    The previous Kill Switch state is restored
    automatically after the test.
    """

    previous_state = security.is_kill_switch_active()

    try:
        # Activate Kill Switch
        security.set_kill_switch(True)

        # Test whether a capability is blocked
        blocked_result = not security.is_allowed(
            "file_read"
        )

        # Test an actual authorization check
        execution_blocked = not security.can_execute(
            "file_read"
        )

        test_passed = (
            blocked_result
            and execution_blocked
        )

        return {
            "status": (
                "success"
                if test_passed
                else "failed"
            ),
            "kill_switch_test": test_passed,
            "permission_blocked": blocked_result,
            "execution_blocked": execution_blocked,
            "previous_kill_switch_state": previous_state,
            "current_kill_switch_state": (
                security.is_kill_switch_active()
            )
        }

    finally:
        # Always restore previous state
        security.set_kill_switch(
            previous_state
        )
