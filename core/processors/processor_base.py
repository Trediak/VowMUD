"""This module contains the base class for processors.

ProcessorBase is an abstract baseclass to guarantee a base interface for processors which inherit from it.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from core.user import User

class ProcessorBase(ABC):
    """Base class for processors.

    Parameters
    ----------
    ABC : Class
        Inherits from ABC (abstract base class)
    """
    @abstractmethod
    async def process(self, user: User, command: str):
        """Interface to add work to processor queue.

        Parameters
        ----------
        user : User
            Instance of User class which is attached as source of command
        command : str
            Command to be processed
        """
        pass

    @abstractmethod
    async def run() -> int:
        """Start the processor. Initialize queue and loop, processing commands in queue until shutdown initiated.

        Returns
        -------
        int
            Return code of processor, 0 being the only good return
        """
        pass

    @abstractmethod
    async def shutdown() -> None:
        """Initate shutdown of the chat processor.
        """
        pass

    @abstractmethod
    async def _consume() -> Tuple[User, str]:
        """Consume work from queue.

        Returns
        -------
        Tuple[User, str]
            Tuple containing source and command to be processed
        """
        pass
  