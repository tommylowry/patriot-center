"""Central manager metadata orchestration.

This is the ONLY place where manager metadata operations should be coordinated.
All other code should use ManagerMetadataManager methods.

Single Responsibility: Orchestrate sub-processors and manage persistence.
"""

from patriot_center_backend.managers.manager_metadata_manager import (
    ManagerMetadataManager,
    get_manager_metadata_manager,
)

MANAGER_METADATA_MANAGER = get_manager_metadata_manager()
__all__ = [
    'MANAGER_METADATA_MANAGER',
    'ManagerMetadataManager'
]
