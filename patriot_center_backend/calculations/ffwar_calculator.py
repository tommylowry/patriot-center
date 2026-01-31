"""Calculates the ffWAR for a given week."""

from statistics import mean
from typing import Any

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.managers.formatters import get_season_state
from patriot_center_backend.players.player_scores_fetcher import (
    fetch_all_player_scores,
    fetch_rostered_players,
    fetch_starters_by_position,
)


class FFWARCalculator:
    """Calculates the ffWAR for a given week."""
    def __init__(self, year: int, week: int):
        """Initialize the FFWARCalculator.

        Args:
            year (int): The season year.
            week (int): The week number.
        """
        self.year = year
        self.week = week

        self.season_state = get_season_state(str(self.week), str(self.year))

        self.starter_scores = fetch_starters_by_position(self.year, self.week)

        self.managers = []

        self.replacement_scores = dict.fromkeys(self.starter_scores, 0.0)
        self.baseline_scores = {
            position: {} for position in self.starter_scores
        }
        self.weighted_scores = {
            position: {} for position in self.starter_scores
        }

        self.player_data = {}

# ==================== Public Methods ====================
    def calculate_ffwar(self) -> dict[str, dict[str, Any]]:
        """Calculates the ffWAR for a given week.

        Returns:
            A dictionary with the ffWAR scores for each player.
        """
        # Fetch all managers for the given week
        self._apply_managers()

        # Calculate the prerequisites for calculating ffWAR
        self._apply_replacement_scores()
        self._apply_baseline_and_weighted_scores()
        self._apply_player_data()

        # Simulate all possible manager pairings
        self._simulate_matchups()

        # Sort the player_data by ffWAR descending, then by name ascending
        self._sort_player_data()

        return self.player_data

    def _simulate_matchups(self) -> None:
        """Simulates all possible manager pairings with the given player data.

        This function takes the given player data and simulates all possible
        manager pairings. For each manager pairing, it calculates the score
        with the given player and the score with the replacement player at the
        same position. It then determines if the player would win or lose the
        matchup and if the replacement player would win or lose the matchup.
        The results of these simulations are used to calculate the final ffWAR
        score as a win rate differential.

        Raises:
            ValueError: If no simulated games are played

        Notes:
            - This function assumes that the player data has already been
            populated with the necessary information.
            - The ffWAR score is calculated as the win rate differential
            between the player and the replacement player.
            - The ffWAR score is adjusted for the playoffs by scaling it down
            by 1/3. This is because only 4 of 12 teams play each week in the
            playoffs.
        """
        # Simulate all possible manager pairings with this player
        for player_id in self.player_data:

            position = self.player_data[player_id]["position"]

            player_score = self.player_data[player_id]["score"]
            replacement_score = self.replacement_scores[position]

            num_wins = 0
            num_simulated_games = 0

            for manager_playing in self.baseline_scores[position]:

                baseline = self.baseline_scores[position][manager_playing]

                # Manager's score with THIS player at this position
                simulated_player_score = baseline + player_score

                # Manager's score with REPLACEMENT player at this position
                simulated_replacement_score = baseline + replacement_score

                for manager_opposing in self.weighted_scores[position]:
                    if manager_playing == manager_opposing:
                        continue  # Skip self-matchups

                    # Opponent's score with the week's positional average
                    # applied instead of the average of all players with this
                    # position
                    simulated_opponent_score = (
                        self.weighted_scores[position][manager_opposing]
                    )

                    # Determine if the player would win or lose the matchup
                    player_wins = (
                        simulated_player_score > simulated_opponent_score
                    )
                    player_loses = (
                        simulated_player_score < simulated_opponent_score
                    )

                    # Determine if the replacement would win or lose the matchup
                    replacement_wins = (
                        simulated_replacement_score > simulated_opponent_score
                    )
                    replacement_loses = (
                        simulated_replacement_score < simulated_opponent_score
                    )

                    # Case 1: Player wins but replacement would lose
                    # (+1 fantasy football Win Above Replacement aka ffWAR)
                    if player_wins and replacement_loses:
                        num_wins += 1

                    # Case 2: Player loses but replacement would win
                    # (-1 fantasy football Win Above Replacement aka ffWAR)
                    if player_loses and replacement_wins:
                        num_wins -= 1

                    # Case 3 & 4: Both win or both lose
                    # (no change to ffWAR)

                    num_simulated_games += 1

            # Calculate final ffWAR score as win rate differential
            if num_simulated_games == 0:
                raise ValueError("No simulated games played")

            ffwar_score = num_wins / num_simulated_games

            # Playoff adjustment: scale down by 1/3 since only 4 of 12 teams
            # play each week
            ffwar_score = self._apply_playoff_adjustment(ffwar_score)

            self.player_data[player_id]["ffWAR"] = round(ffwar_score, 3)

    def _apply_managers(self) -> None:
        """Fetches valid manager options for the given year and week.

        Raises:
            ValueError: If no valid options are found for the given year and
                week.
        """
        valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

        managers = (
            valid_options_cache
            .get(str(self.year), {})
            .get(str(self.week), {})
            .get("managers", [])
        )
        if not managers:
            raise ValueError(
                f"No valid options found for year={self.year}, week={self.week}"
            )

        self.managers = managers


    def _apply_baseline_and_weighted_scores(self) -> None:
        """Calculates the baseline and weighted scores for each position.

        The baseline score is the manager's total points minus their positional
        average. The weighted score is the manager's total points minus their
        positional average, plus the average of all other managers at this
        position.
        """
        for position in self.starter_scores:
            position_scores = self.starter_scores[position]

            pos_average = mean(position_scores["scores"])

            # Pre-compute normalized scores for each manager
            # These values are used in the simulation to isolate positional
            #   impact
            managers_with_scores = position_scores["managers"]
            for manager in managers_with_scores:

                manager_position_scores = managers_with_scores[manager]

                # The manager has no players at this position, so no
                # baseline should be used and the weighted score is simply
                # the manager's total points
                if len(manager_position_scores["scores"]) == 0:
                    self.weighted_scores[position][manager] = (
                        manager_position_scores["total_points"] + pos_average
                    )

                else:
                    # Calculate this manager's average score at this position
                    mgr_average = mean(
                        manager_position_scores["scores"]
                    )

                    # Store manager's total points minus their positional
                    #   contribution
                    # This represents the manager's "baseline" without this
                    #   position's impact
                    self.baseline_scores[position][manager] = (
                        manager_position_scores["total_points"] - mgr_average
                    )

                    # Store normalized weighted score (baseline + league
                    #   average at position)
                    # Used as opponent's score in simulations
                    self.weighted_scores[position][manager] = (
                        manager_position_scores["total_points"]
                        - mgr_average
                        + pos_average
                    )

    def _apply_player_data(self) -> None:
        """Populate scores and roster information for each player.

        For each player, we store the following information:
            - name: The player's full name.
            - score: The player's fantasy score for the week.
            - ffWAR: The player's ffWAR score for the week.
            - position: The player's position (QB, RB, WR, TE, K, DEF).
            - manager: The manager who rostered this player, or None if not
                rostered.
            - started: A boolean indicating whether this player was a starter
                for the week.
        """
        player_scores = fetch_all_player_scores(self.year, self.week)
        rostered_players = fetch_rostered_players(self.year, self.week)

        for position in player_scores:
            position_scores = player_scores[position]
            for player_id in position_scores:
                # Player's Full Name
                player = position_scores[player_id]["name"]

                # Determine if this player is a starter
                started = player in self.starter_scores[position]["players"]

                # Determine if this player is rostered and by whom
                player_data_manager_value = None
                for manager in self.managers:
                    if player_id in rostered_players[manager]:
                        player_data_manager_value = manager
                        break

                self.player_data[player_id] = {
                    "name": player,
                    "score": position_scores[player_id]["score"],
                    "ffWAR": 0.0,
                    "position": position,
                    "manager": player_data_manager_value,
                    "started": started,
                }


    def _apply_replacement_scores(self):
        """Fetches replacement scores for every positinon in the given week.

        Raises:
            ValueError: If no replacement scores are found for the given year
                and week.
        """
        replacement_scores_cache = CACHE_MANAGER.get_replacement_score_cache()

        weekly_replacement_scores = (
            replacement_scores_cache
            .get(str(self.year), {})
            .get(str(self.week), {})
        )
        if not weekly_replacement_scores:
            raise ValueError(
                f"No replacement scores found for "
                f"{self.year}-{self.week}"
            )


        for position in self.replacement_scores:
            replacement_score = weekly_replacement_scores.get(
                f"{position}_3yr_avg"
            )

            if replacement_score is None:
                raise ValueError(
                    f"No replacement scores found for "
                    f"{position} at {self.year}-{self.week}"
                )

            self.replacement_scores[position] = replacement_score

    def _apply_playoff_adjustment(self, score: float) -> float:
        """Apply playoff adjustment to score based on season state.

        Args:
            score: The score to adjust.

        Returns:
            The adjusted score.
        """
        return score / 3 if self.season_state == "playoffs" else score

    def _sort_player_data(self):
        """Sorts the player data.

        - Sorts player data by ffWAR in descending order.
        - Then by name in ascending order.
        """
        sorted_player_data = dict(
            sorted(
                self.player_data.items(),
                key=lambda item: (-item[1]["ffWAR"], item[1]["name"]),
            )
        )
        self.player_data = sorted_player_data
