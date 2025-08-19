"""
Compatibility shim for legacy imports:

    from TuringBotClient import TuringBotClient

Prefer:

    from turing_bot_client import TuringBotClient
"""
from warnings import warn
from turing_bot_client import TuringBotClient as _TuringBotClient

warn(
    "Deprecated import path. Use 'from turing_bot_client import TuringBotClient'.",
    DeprecationWarning,
    stacklevel=2,
)

TuringBotClient = _TuringBotClient
__all__ = ["TuringBotClient"]
