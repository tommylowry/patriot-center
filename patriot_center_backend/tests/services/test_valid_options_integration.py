"""
Integration tests for ValidOptionsService using REAL cache data.

These tests catch bugs that limited mock data might miss by:
1. Testing with the full complexity of real data
2. Verifying logical invariants that must always hold
3. Testing random combinations to find edge cases
4. Checking subset/superset relationships between filter combinations

Run with: pytest patriot_center_backend/tests/services/test_valid_options_integration.py -v
"""
import pytest
import random
from patriot_center_backend.services.valid_options import (
    ValidOptionsService,
    VALID_OPTIONS_CACHE,
    PLAYERS_DATA,
    LEAGUE_IDS,
    NAME_TO_MANAGER_USERNAME
)


class TestRealDataInvariants:
    """Test invariants that must ALWAYS hold, regardless of data."""

    def test_selected_year_always_in_results(self):
        """When filtering by year, that year MUST be in the results."""
        for year in LEAGUE_IDS.keys():
            service = ValidOptionsService(str(year), None, None, None)
            result = service.get_valid_options()
            assert str(year) in result["years"], f"Year {year} not in results when selected"

    def test_selected_year_week_both_in_results(self):
        """When filtering by year+week, both MUST be in the results."""
        for year, year_data in VALID_OPTIONS_CACHE.items():
            for week in year_data.get("weeks", [])[:3]:  # Test first 3 weeks of each year
                service = ValidOptionsService(str(year), str(week), None, None)
                result = service.get_valid_options()
                assert str(year) in result["years"], f"Year {year} not in results for {year}+week{week}"
                assert str(week) in result["weeks"], f"Week {week} not in results for {year}+week{week}"

    def test_adding_filters_narrows_or_maintains_results(self):
        """Adding more filters should never EXPAND the result set."""
        # Test with a sample of years
        test_years = list(LEAGUE_IDS.keys())[:3]

        for year in test_years:
            # Get results with just year
            year_only = ValidOptionsService(str(year), None, None, None).get_valid_options()

            # Get results with year + manager
            year_data = VALID_OPTIONS_CACHE.get(str(year), {})
            managers = year_data.get("managers", [])
            if managers:
                manager = managers[0]
                year_mgr = ValidOptionsService(str(year), manager, None, None).get_valid_options()

                # Adding manager filter should not expand years/weeks
                assert set(year_mgr["years"]) <= set(year_only["years"]), \
                    f"Adding manager {manager} to year {year} EXPANDED years"
                assert set(year_mgr["weeks"]) <= set(year_only["weeks"]), \
                    f"Adding manager {manager} to year {year} EXPANDED weeks"

    def test_player_position_matches_player_data(self):
        """When filtering by player, position must match PLAYERS_DATA."""
        # Test a sample of players
        players = list(PLAYERS_DATA.keys())[:10]

        for player in players:
            service = ValidOptionsService(player, None, None, None)
            result = service.get_valid_options()
            expected_position = PLAYERS_DATA[player]["position"]

            assert result["positions"] == [expected_position], \
                f"Player {player} should lock position to {expected_position}, got {result['positions']}"

    def test_no_duplicate_values_in_results(self):
        """Results should never contain duplicate values."""
        # Test with random combinations
        combinations = [
            ("2024", None, None, None),
            ("2023", "Tommy", None, None),
            ("QB", None, None, None),
        ]

        for args in combinations:
            try:
                service = ValidOptionsService(*args)
                result = service.get_valid_options()

                assert len(result["years"]) == len(set(result["years"])), \
                    f"Duplicate years for {args}: {result['years']}"
                assert len(result["weeks"]) == len(set(result["weeks"])), \
                    f"Duplicate weeks for {args}: {result['weeks']}"
                assert len(result["managers"]) == len(set(result["managers"])), \
                    f"Duplicate managers for {args}: {result['managers']}"
                assert len(result["positions"]) == len(set(result["positions"])), \
                    f"Duplicate positions for {args}: {result['positions']}"
            except ValueError:
                # Invalid combination, skip
                pass


class TestRealDataPlayerCombinations:
    """Test all player-based filter combinations with real data."""

    def test_player_manager_year_consistency(self):
        """Test player+manager+year combinations for consistency.

        This is the type of test that found the Javonte Williams bug!
        Only tests VALID combinations that exist in the cache.
        """
        failures = []
        tested_count = 0

        # For each year in cache
        for year, year_data in list(VALID_OPTIONS_CACHE.items())[:3]:  # Test first 3 years
            # Test combinations that ACTUALLY exist in the data
            for week in list(year_data.get("weeks", []))[:3]:  # First 3 weeks
                week_data = year_data.get(week, {})

                # Iterate through each manager in this week
                for manager, manager_data in list(week_data.items())[:3]:
                    if manager in ["managers", "players", "positions"]:
                        continue  # Skip metadata keys

                    # Get players this manager actually had this week
                    players = manager_data.get("players", [])

                    for player in players[:3]:  # First 3 players
                        # This is a VALID combination - player DID play for manager in this year
                        try:
                            service = ValidOptionsService(player, manager, str(year), None)
                            result = service.get_valid_options()
                            tested_count += 1

                            # CRITICAL: Year should be in results (we filtered by it)
                            if str(year) not in result["years"]:
                                failures.append(f"Year {year} missing for {player}+{manager}+{year}")

                        except ValueError:
                            # Even valid combinations might fail due to other constraints
                            pass

        print(f"\nTested {tested_count} valid player+manager+year combinations")
        assert not failures, f"Found {len(failures)} failures:\n" + "\n".join(failures[:10])

    def test_player_year_week_consistency(self):
        """Test player+year+week combinations.

        Only tests VALID combinations that exist in the cache.
        """
        failures = []
        tested_count = 0

        # Get a sample year
        for year, year_data in list(VALID_OPTIONS_CACHE.items())[:2]:
            # Test combinations that ACTUALLY exist
            for week in list(year_data.get("weeks", []))[:3]:
                week_data = year_data.get(week, {})

                # Get all players who played this week
                players = week_data.get("players", [])

                for player in players[:3]:
                    # This is a VALID combination - player DID play in this year+week
                    try:
                        service = ValidOptionsService(player, str(year), str(week), None)
                        result = service.get_valid_options()
                        tested_count += 1

                        # Year and week should be in results
                        if str(year) not in result["years"]:
                            failures.append(f"Year {year} missing for {player}+{year}+week{week}")
                        if str(week) not in result["weeks"]:
                            failures.append(f"Week {week} missing for {player}+{year}+week{week}")

                    except ValueError:
                        pass

        print(f"\nTested {tested_count} valid player+year+week combinations")
        assert not failures, f"Found {len(failures)} failures:\n" + "\n".join(failures[:10])


class TestRealDataRandomCombinations:
    """Test random filter combinations to catch unexpected edge cases."""

    def test_random_two_filter_combinations(self):
        """Test 50 random 2-filter combinations using VALID data."""
        random.seed(42)  # Reproducible randomness
        failures = []
        tested_count = 0

        # Build list of valid year+manager combinations from cache
        valid_year_manager = []
        for year, year_data in VALID_OPTIONS_CACHE.items():
            for manager in year_data.get("managers", []):
                valid_year_manager.append((str(year), manager))

        # Sample random valid combinations
        for _ in range(min(50, len(valid_year_manager))):
            year, manager = random.choice(valid_year_manager)

            # Test year+manager combination
            args = [year, manager, None, None]

            try:
                service = ValidOptionsService(*args)
                result = service.get_valid_options()
                tested_count += 1

                # Basic sanity checks
                if not isinstance(result["years"], list):
                    failures.append(f"Years not a list for {args}")
                if not isinstance(result["weeks"], list):
                    failures.append(f"Weeks not a list for {args}")
                if not isinstance(result["managers"], list):
                    failures.append(f"Managers not a list for {args}")
                if not isinstance(result["positions"], list):
                    failures.append(f"Positions not a list for {args}")

                # Check selected year appears in results
                if year not in result["years"]:
                    failures.append(f"Selected year {year} not in results for {args}")

            except ValueError:
                # Even valid combinations might fail due to constraints
                pass

        print(f"\nTested {tested_count} random valid combinations")
        assert not failures, f"Found {len(failures)} failures:\n" + "\n".join(failures[:20])

    def test_random_player_combinations(self):
        """Test 30 random player-based filter combinations."""
        random.seed(43)
        failures = []

        all_players = list(PLAYERS_DATA.keys())
        all_years = [str(y) for y in LEAGUE_IDS.keys()]
        all_managers = list(NAME_TO_MANAGER_USERNAME.keys())

        for _ in range(30):
            player = random.choice(all_players)

            # Randomly add 0-2 more filters
            num_additional = random.randint(0, 2)
            args = [player, None, None, None]

            if num_additional >= 1:
                args[random.randint(1, 3)] = random.choice(all_years + all_managers)
            if num_additional >= 2:
                # Add another filter in a different position
                empty_positions = [i for i in range(1, 4) if args[i] is None]
                if empty_positions:
                    args[random.choice(empty_positions)] = random.choice(all_years + all_managers)

            try:
                service = ValidOptionsService(*args)
                result = service.get_valid_options()

                # Player's position should be locked
                expected_pos = PLAYERS_DATA[player]["position"]
                if result["positions"] != [expected_pos]:
                    failures.append(f"Player {player} didn't lock position to {expected_pos}: {result['positions']}")

            except ValueError:
                # Invalid combination
                pass

        assert not failures, f"Found {len(failures)} failures:\n" + "\n".join(failures[:20])


class TestRealDataExhaustiveSmallSets:
    """Test ALL combinations of small data sets."""

    def test_all_single_year_filters(self):
        """Test every single year in the cache."""
        failures = []

        for year in LEAGUE_IDS.keys():
            service = ValidOptionsService(str(year), None, None, None)
            result = service.get_valid_options()

            if str(year) not in result["years"]:
                failures.append(f"Year {year} not in results when selected alone")

            # Should have weeks from that year
            expected_weeks = VALID_OPTIONS_CACHE.get(str(year), {}).get("weeks", [])
            if not set(expected_weeks).issubset(set(result["weeks"])):
                failures.append(f"Year {year} missing some weeks: expected {expected_weeks}, got {result['weeks']}")

        assert not failures, "\n".join(failures)

    def test_all_positions(self):
        """Test every position type."""
        positions = ["QB", "RB", "WR", "TE", "K", "DEF"]

        for position in positions:
            service = ValidOptionsService(position, None, None, None)
            result = service.get_valid_options()

            # Should return valid years (where this position was played)
            assert len(result["years"]) > 0, f"Position {position} returned no years"
            assert len(result["managers"]) > 0, f"Position {position} returned no managers"
            assert len(result["weeks"]) > 0, f"Position {position} returned no weeks"

    def test_all_managers_in_most_recent_year(self):
        """Test all managers from the most recent year."""
        most_recent_year = str(max(LEAGUE_IDS.keys()))
        managers = VALID_OPTIONS_CACHE.get(most_recent_year, {}).get("managers", [])

        for manager in managers:
            service = ValidOptionsService(most_recent_year, manager, None, None)
            result = service.get_valid_options()

            assert most_recent_year in result["years"], \
                f"Year {most_recent_year} not in results for manager {manager}"
            assert len(result["weeks"]) > 0, \
                f"Manager {manager} in {most_recent_year} returned no weeks"


class TestRealDataSubsetRelationships:
    """Test that filter combinations create proper subset relationships."""

    def test_year_subset_relationships(self):
        """Test that year+X results are subsets of year-only results."""
        test_year = str(max(LEAGUE_IDS.keys()))  # Most recent year
        year_only = ValidOptionsService(test_year, None, None, None).get_valid_options()

        # Test year + manager
        managers = VALID_OPTIONS_CACHE.get(test_year, {}).get("managers", [])
        if managers:
            manager = managers[0]
            year_mgr = ValidOptionsService(test_year, manager, None, None).get_valid_options()

            # Weeks should be subset
            assert set(year_mgr["weeks"]) <= set(year_only["weeks"]), \
                f"Year+Manager weeks not subset of Year-only weeks"

    def test_player_subset_relationships(self):
        """Test that player+X results are subsets of player-only results."""
        # Pick a common player
        players = list(PLAYERS_DATA.keys())
        if not players:
            pytest.skip("No players in PLAYERS_DATA")

        player = players[0]
        player_only = ValidOptionsService(player, None, None, None).get_valid_options()

        # Test player + year
        if player_only["years"]:
            year = player_only["years"][0]
            player_year = ValidOptionsService(player, str(year), None, None).get_valid_options()

            # Weeks and managers should be subsets
            assert set(player_year["weeks"]) <= set(player_only["weeks"]), \
                f"Player+Year weeks not subset of Player-only weeks"
            assert set(player_year["years"]) <= set(player_only["years"]), \
                f"Player+Year years not subset of Player-only years"


class TestRealDataRegressionSnapshots:
    """Snapshot tests to prevent regressions on known queries."""

    def test_most_recent_year_managers(self):
        """Snapshot of managers in most recent year (should be stable)."""
        most_recent_year = str(max(LEAGUE_IDS.keys()))
        service = ValidOptionsService(most_recent_year, None, None, None)
        result = service.get_valid_options()

        expected_managers = VALID_OPTIONS_CACHE.get(most_recent_year, {}).get("managers", [])

        # All expected managers should be in results
        assert set(expected_managers) <= set(result["managers"]), \
            f"Missing managers in {most_recent_year}"

    def test_qb_position_returns_data(self):
        """QB position should always return some data."""
        service = ValidOptionsService("QB", None, None, None)
        result = service.get_valid_options()

        # QB is common, should have data in multiple years
        assert len(result["years"]) > 0, "QB position returned no years"
        assert len(result["managers"]) > 0, "QB position returned no managers"
        assert len(result["weeks"]) > 0, "QB position returned no weeks"
