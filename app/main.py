"""Compatibility import for local ASGI entrypoints.

The container starts ``ai_proxy.main:app`` from the packaged ``src`` tree.
"""

from ai_proxy.main import app
