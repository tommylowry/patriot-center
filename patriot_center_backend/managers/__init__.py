"""
Manager metadata processing module.

Provides comprehensive manager metadata management including:
- Transaction processing (trades, adds, drops, waivers)
- Matchup and playoff tracking
- Awards and statistics
- Historical data queries

Main entry point: get_manager_metadata_manager()
"""
from patriot_center_backend.managers.manager_metadata_manager import ManagerMetadataManager, get_manager_metadata_manager

__all__ = ['ManagerMetadataManager', 'get_manager_metadata_manager']