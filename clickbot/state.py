"""Client state tracking module.

Provides in-memory tracking of processed clients to prevent
duplicate processing during bot execution.
"""

import logging
from dataclasses import dataclass, field
from typing import Set

logger = logging.getLogger(__name__)


@dataclass
class ClientTracker:
    """Tracks which clients have been processed in the current session.

    Uses an in-memory set to prevent duplicate processing.
    State is lost when the bot restarts (no persistence).
    """

    processed: Set[str] = field(default_factory=set)

    def mark_processed(self, client_name: str) -> None:
        """Mark a client as processed.

        Args:
            client_name: Name of the client to mark
        """
        self.processed.add(client_name)
        logger.debug(f"Marked client as processed: {client_name}")

    def is_processed(self, client_name: str) -> bool:
        """Check if a client has been processed.

        Args:
            client_name: Name of the client to check

        Returns:
            True if client was already processed, False otherwise
        """
        return client_name in self.processed

    def get_count(self) -> int:
        """Get the number of processed clients.

        Returns:
            Number of clients marked as processed
        """
        return len(self.processed)

    def clear(self) -> None:
        """Clear all processed client records."""
        count = len(self.processed)
        self.processed.clear()
        logger.debug(f"Cleared {count} processed clients")
