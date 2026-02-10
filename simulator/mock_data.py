"""Mock data for TaxAct Simulator.

Provides configurable test data for the Client Manager table.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class MockClient:
    """Mock client data for testing."""
    name: str
    return_type: str  # "1120" or "1120S"
    fed_ef_status: str  # "" (empty), "Submitted", "Accepted", etc.

    @property
    def needs_processing(self) -> bool:
        """Check if client needs E-File processing."""
        return self.fed_ef_status == ""


# Default mock clients for testing
MOCK_CLIENTS: List[MockClient] = [
    MockClient("SANDMEYER INC", "1120", ""),
    MockClient("SMITH LLC", "1120S", ""),
    MockClient("JONES CORP", "1120", "Submitted"),
    MockClient("TECH SOLUTIONS", "1120S", ""),
    MockClient("ABC HOLDINGS", "1120", ""),
    MockClient("XYZ PARTNERS", "1120S", "Accepted"),
    MockClient("ACME CORP", "1120", ""),
    MockClient("BETA INDUSTRIES", "1120S", ""),
    MockClient("GAMMA LLC", "1120", "Rejected"),
    MockClient("DELTA INC", "1120", ""),
]


def get_clients_by_return_type(return_type: str) -> List[MockClient]:
    """Get all clients with specific return type."""
    return [c for c in MOCK_CLIENTS if c.return_type == return_type]


def get_unprocessed_clients() -> List[MockClient]:
    """Get all clients with empty Fed EF Status."""
    return [c for c in MOCK_CLIENTS if c.needs_processing]
