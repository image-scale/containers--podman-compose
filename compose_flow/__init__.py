"""Compose Flow - A compose file orchestration tool with Podman backend."""

__version__ = "1.0.0"

from compose_flow.interpolation import interpolate

__all__ = ['interpolate', '__version__']
