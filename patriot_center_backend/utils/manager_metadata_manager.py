class ManagerMetadataManager:
    def __init__(self):
        self._cache = {
            # "manager_username":{
            #     "summary": { ... },
            #     "seasons": {
            #         "2020": {
            #             "summary": { ... },
            #             "roster_id": 123456,
            #             "weeks": {
            #                 "1": {
            #                     "points_for": 120.5,
            #                     "points_against": 98.3,
            #                     ...
            #                 },
            #             },
            #         },
            #         ...
            #     }
            # }
        }


    def _manager_initialized(self, manager_username: str, year: str):        return (manager_username in self._cache and
                year in self._cache[manager_username]["seasons"])

    def set_roster_id(self, manager_username: str, year: str, roster_id: int):
        """Set the roster ID for a given manager and year."""

        if manager_username not in self._cache:
            self._cache[manager_username] = {"summary": {}, "seasons": {}}
        if year not in self._cache[manager_username]["seasons"]:
            self._cache[manager_username]["seasons"][year] = {
                "summary": {},
                "roster_id": None,
                "weeks": {}
            }
        self._cache[manager_username]["seasons"][year]["roster_id"] = roster_id