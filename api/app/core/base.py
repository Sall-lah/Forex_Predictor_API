"""Abstract base classes for services and repositories."""

import logging
from abc import ABC, abstractmethod

from app.core.config import get_settings, Settings


class BaseService(ABC):
    """Abstract base class for all feature services.
    
    Provides:
    - Automatic logger based on class module
    - Settings access via self.settings property
    - Standard lifecycle hooks
    """

    def __init__(self) -> None:
        """Initialize base service with logger and settings."""
        self.logger = logging.getLogger(self.__class__.__module__)

    @property
    def settings(self) -> Settings:
        """Access application settings."""
        return get_settings()


class BaseRepository(ABC):
    """Abstract base class for all data repositories.
    
    Provides:
    - Automatic logger based on class module
    - Settings access via self.settings property
    """

    def __init__(self) -> None:
        """Initialize base repository with logger and settings."""
        self.logger = logging.getLogger(self.__class__.__module__)

    @property
    def settings(self) -> Settings:
        """Access application settings."""
        return get_settings()
