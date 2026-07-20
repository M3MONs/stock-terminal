from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .screen import RecommendationHistoryScreen

__all__ = ["RecommendationHistoryScreen"]


def __getattr__(name: str):
    if name == "RecommendationHistoryScreen":
        from .screen import RecommendationHistoryScreen

        return RecommendationHistoryScreen
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
