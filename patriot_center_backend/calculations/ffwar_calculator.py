"""Calculates the ffWAR for a given week."""

from statistics import mean

from patriot_center_backend.cache.queries.replacement_score_queries import (
    get_replacement_scores,
)
from patriot_center_backend.constants import Position
from patriot_center_backend.models import Manager, Player
from patriot_center_backend.utils.sleeper_helpers import get_season_state


class FFWARCalculator:
    """Calculates the ffWAR for a given week."""

    # ==========================================================================
    # ============================= Constructor ================================
    # ==========================================================================
    def __init__(self, year: int, week: int):
        """Initialize the FFWARCalculator.

        Args:
            year: The season year.
            week: The week number.
        """
        self.year = year
        self.week = week

        self._dynamic_vars_set = False

        self.season_state = get_season_state(str(year), str(week))

        self.managers = Manager.get_all_managers(str(year), str(week))

        self.replacement_scores = dict.fromkeys(Position, 0.0)
        self.baseline_scores = {position: {} for position in Position}
        self.weighted_scores = {position: {} for position in Position}

    # ==========================================================================
    # ============================= Public Methods =============================
    # ==========================================================================
    def calculate_and_set_ffwar_for_week(self, players: list[Player]) -> None:
        """Calculates the ffWAR for a given week.

        Returns:
            A dictionary with the ffWAR scores for each player.

        Notes:
            - This function assumes that the player data has already been
            populated with the necessary information.
        """
        self._apply_dynamic_vars()

        # Get all the players that played that week
        for player in players:
            points = player.get_points(
                year=str(self.year),
                week=str(self.week),
                only_started=False,
                only_rostered=False,
            )

            ffwar = self.calculate_ffwar_for_player(
                player_points=points,
                position=player.position,
            )

            player.set_week_data(str(self.year), str(self.week), ffwar=ffwar)

    def calculate_ffwar_for_player(
        self, player_points: float, position: Position
    ) -> float:
        """Simulates all possible manager pairings with a specific player.

        This function takes a player's points and simulates all possible
        manager pairings. For each manager pairing, it calculates the score
        with the given player and the score with the replacement player at the
        same position. It then determines if the player would win or lose the
        matchup and if the replacement player would win or lose the matchup.
        The results of these simulations are used to calculate the final ffWAR
        score as a win rate differential.

        Args:
            player_points: The points scored by the player.
            position: The position of the player.

        Returns:
            The ffWAR score for the player.

        Raises:
            ValueError: If no simulated games are played

        Notes:
            - The ffWAR score is calculated as the win rate differential
            between the player and the replacement player.
            - The ffWAR score is adjusted for the playoffs by scaling it down
            by 1/3. This is because only 4 of 12 teams play each week in the
            playoffs.
        """
        self._apply_dynamic_vars()

        replacement_score = self.replacement_scores[position]

        num_wins = 0
        num_simulated_games = 0

        for manager_playing in self.baseline_scores[position]:
            baseline = self.baseline_scores[position][manager_playing]

            # Manager's score with THIS player at this position
            simulated_player_score = baseline + player_points

            # Manager's score with REPLACEMENT player at this position
            simulated_replacement_score = baseline + replacement_score

            for manager_opposing in self.weighted_scores[position]:
                if manager_playing == manager_opposing:
                    continue  # Skip self-matchups

                # Opponent's score with the week's positional average
                # applied instead of the average of all players with this
                # position
                simulated_opponent_score = self.weighted_scores[position][
                    manager_opposing
                ]

                # Determine if the player would win or lose the matchup
                player_wins = simulated_player_score > simulated_opponent_score
                player_loses = simulated_player_score < simulated_opponent_score

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

        ffwar = num_wins / num_simulated_games

        # Playoff adjustment: scale down by 1/3 since only 4 of 12 teams
        # play each week
        return self._apply_playoff_adjustment(ffwar)

    # =========================================================================
    # ============================ Private Methods ============================
    # =========================================================================
    def _apply_dynamic_vars(self) -> None:
        """Applies the dynamic variables to the calculator."""
        # Calculate the prerequisites for calculating ffWAR
        if self._dynamic_vars_set:
            return

        self._apply_replacement_scores()
        self._calculate_and_apply_baseline_and_weighted_scores()

        self._dynamic_vars_set = True

    def _calculate_and_apply_baseline_and_weighted_scores(self) -> None:
        """Calculates the baseline and weighted scores for each position.

        The baseline score is the manager's total points minus their positional
        average. The weighted score is the manager's total points minus their
        positional average, plus the average of all other managers at this
        position.
        """
        managers = Manager.get_all_managers(
            year=str(self.year), week=str(self.week)
        )

        league_pos_scores = {p: [] for p in Position}

        for manager in managers:
            matchup_data = manager.get_matchup_data(
                year=str(self.year), week=str(self.week)
            )
            points_for = matchup_data.get("points_for", 0.0)

            # Group scores by position in one pass
            pos_scores = manager.get_positional_scores_for_starters(
                year=str(self.year), week=str(self.week)
            )

            for pos, scores in pos_scores.items():
                league_pos_scores[pos].extend(scores)

                if not scores:
                    continue  # No starters at this position

                self.baseline_scores[pos][str(manager)] = points_for - mean(
                    scores
                )

        # Now compute weighted scores
        for pos, scores in league_pos_scores.items():
            pos_average = mean(scores)

            for manager in managers:

                # Use baseline if it exists, otherwise use total.
                if str(manager) in self.baseline_scores[pos]:
                    baseline = self.baseline_scores[pos][str(manager)]
                else:
                    # No players at this position — use total + avg
                    matchup_data = manager.get_matchup_data(
                        year=str(self.year), week=str(self.week)
                    )
                    baseline = matchup_data.get("points_for", 0.0)

                self.weighted_scores[pos][str(manager)] = baseline + pos_average

    def _apply_replacement_scores(self) -> None:
        """Fetches replacement scores for every positinon in the given week.

        Raises:
            ValueError: If no replacement scores are found for the given year
                and week.
        """
        weekly_replacement_scores = get_replacement_scores(self.year, self.week)

        if not weekly_replacement_scores:
            raise ValueError(
                f"No replacement scores found for {self.year}-{self.week}"
            )

        for position in Position:
            replacement_score = weekly_replacement_scores.get(
                f"{position}_3yr_avg"
            )

            if replacement_score is None:
                raise ValueError(
                    f"No replacement scores found for "
                    f"{position} at {self.year}-{self.week}"
                )

            self.replacement_scores[position] = replacement_score

    def _apply_playoff_adjustment(self, ffwar: float) -> float:
        """Apply playoff adjustment to score based on season state.

        Args:
            ffwar: The unadjusted ffwar.

        Returns:
            The adjusted ffwar if season is playoffs, otherwise the unadjusted
        """
        return ffwar / 3 if self.season_state == "playoffs" else ffwar


FFWARCalculator(2023, 1)
