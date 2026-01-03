# /// script
# dependencies = [
#   "polars",
# ]
# ///

"""
xFPL Calculator Module (Improved Algorithm)

Calculates Expected FPL Points (xFPL) from underlying statistics.
Uses industry best practices for clean sheet probability and bonus estimation.
"""

import polars as pl


class XFPLCalculator:
    """Calculates Expected FPL Points based on underlying statistics."""

    # FPL scoring system
    GOALS_POINTS = {1: 10, 2: 6, 3: 5, 4: 4}  # GKP, DEF, MID, FWD
    ASSISTS_POINTS = 3
    CLEAN_SHEET_POINTS = {1: 4, 2: 4, 3: 1, 4: 0}  # GKP, DEF, MID, FWD
    APPEARANCE_60_MIN = 2
    APPEARANCE_1_MIN = 1

    # Bonus points estimation constants (empirical from FPL data)
    BONUS_PER_100_BPS_PER_MATCH = 0.035  # ~3.5 bonus points per 100 BPS per match

    def __init__(self, players_df: pl.DataFrame):
        """
        Initialize calculator with player data.

        Args:
            players_df: Polars DataFrame with player statistics
        """
        self.players_df = players_df.clone()

    def calculate_xfpl(self) -> pl.DataFrame:
        """
        Calculate xFPL for all players using improved algorithm.

        Returns:
            DataFrame with xFPL calculations and performance metrics
        """
        df = self.players_df.clone()

        # Calculate matches played (estimate)
        df = df.with_columns([(pl.col("minutes") / 90).alias("matches_played")])

        # Calculate expected goals points
        df = df.with_columns(
            [
                pl.when(pl.col("element_type") == 1)
                .then(pl.col("expected_goals") * 10)
                .when(pl.col("element_type") == 2)
                .then(pl.col("expected_goals") * 6)
                .when(pl.col("element_type") == 3)
                .then(pl.col("expected_goals") * 5)
                .when(pl.col("element_type") == 4)
                .then(pl.col("expected_goals") * 4)
                .otherwise(0.0)
                .alias("xG_points")
            ]
        )

        # Calculate expected assists points
        df = df.with_columns(
            [(pl.col("expected_assists") * self.ASSISTS_POINTS).alias("xA_points")]
        )

        # IMPROVED: Calculate expected clean sheet points using per-match probability
        # Average xGC per match
        xgc_per_match = pl.col("expected_goals_conceded") / pl.col("matches_played")
        # Clean sheet probability per match: P(CS) = e^(-xGC_per_match)
        cs_prob_per_match = (-xgc_per_match).exp()
        # Expected total clean sheets = CS probability * matches played
        expected_cs = cs_prob_per_match * pl.col("matches_played")

        df = df.with_columns(
            [
                pl.when(pl.col("element_type") == 1)
                .then(expected_cs * 4)
                .when(pl.col("element_type") == 2)
                .then(expected_cs * 4)
                .when(pl.col("element_type") == 3)
                .then(expected_cs * 1)
                .when(pl.col("element_type") == 4)
                .then(0.0)
                .otherwise(0.0)
                .alias("xCS_points")
            ]
        )

        # IMPROVED: Estimate expected bonus from BPS (not actual bonus)
        # Average BPS per match
        bps_per_match = pl.col("bps") / pl.col("matches_played")
        # Expected bonus = (BPS per match / 100) * bonus_rate * matches_played
        expected_bonus = (
            (bps_per_match / 100)
            * self.BONUS_PER_100_BPS_PER_MATCH
            * pl.col("matches_played")
        )

        df = df.with_columns([expected_bonus.alias("xBonus_points")])

        # Calculate expected appearance points
        df = df.with_columns(
            [
                (
                    (pl.col("starts") * self.APPEARANCE_60_MIN)
                    + (
                        (pl.col("minutes") - pl.col("starts") * 60)
                        / 30
                        * self.APPEARANCE_1_MIN
                    ).clip(0, None)
                ).alias("xAppearance_points")
            ]
        )

        # Calculate total xFPL
        df = df.with_columns(
            [
                (
                    pl.col("xG_points")
                    + pl.col("xA_points")
                    + pl.col("xCS_points")
                    + pl.col("xBonus_points")
                    + pl.col("xAppearance_points")
                ).alias("xFPL")
            ]
        )

        # NEW: Add per-90 metrics for fair comparison
        df = df.with_columns(
            [
                ((pl.col("expected_goals") / pl.col("minutes")) * 90).alias("xG90"),
                ((pl.col("expected_assists") / pl.col("minutes")) * 90).alias("xA90"),
                ((pl.col("xFPL") / pl.col("minutes")) * 90).alias("xFPL90"),
                (pl.col("expected_goals") + pl.col("expected_assists")).alias("xGI"),
                (
                    (
                        (pl.col("expected_goals") + pl.col("expected_assists"))
                        / pl.col("minutes")
                    )
                    * 90
                ).alias("xGI90"),
            ]
        )

        # Calculate performance metrics
        df = df.with_columns(
            [
                (pl.col("total_points") - pl.col("xFPL")).alias("delta"),
                ((pl.col("total_points") / pl.col("xFPL")) * 100)
                .fill_nan(0.0)
                .fill_null(0.0)
                .alias("performance_pct"),
            ]
        )

        # Round for readability
        df = df.with_columns(
            [
                pl.col("xFPL").round(2),
                pl.col("xG90").round(3),
                pl.col("xA90").round(3),
                pl.col("xGI").round(3),
                pl.col("xGI90").round(3),
                pl.col("xFPL90").round(2),
                pl.col("delta").round(2),
                pl.col("performance_pct").round(1),
                pl.col("matches_played").round(1),
            ]
        )

        return df

    def get_overperformers(self, n: int = 10) -> pl.DataFrame:
        """
        Get top N overperforming players.

        Args:
            n: Number of players to return

        Returns:
            DataFrame with top overperformers
        """
        df = self.calculate_xfpl()
        return df.sort("delta", descending=True).head(n)

    def get_underperformers(self, n: int = 10) -> pl.DataFrame:
        """
        Get top N underperforming players.

        Args:
            n: Number of players to return

        Returns:
            DataFrame with top underperformers
        """
        df = self.calculate_xfpl()
        return df.sort("delta", descending=False).head(n)


def calculate_xfpl(players_df: pl.DataFrame) -> pl.DataFrame:
    """
    Convenience function to calculate xFPL.

    Args:
        players_df: Polars DataFrame with player statistics

    Returns:
        DataFrame with xFPL calculations
    """
    calculator = XFPLCalculator(players_df)
    return calculator.calculate_xfpl()


if __name__ == "__main__":
    # Test the calculator
    from fpl_data_fetcher import fetch_fpl_data

    print("Fetching FPL data...")
    df = fetch_fpl_data()

    print("Calculating xFPL with improved algorithm...")
    calculator = XFPLCalculator(df)

    print("\nTop 10 Overperformers:")
    overperformers = calculator.get_overperformers(10)
    print(
        overperformers.select(
            ["name", "team", "position", "total_points", "xFPL", "delta", "xFPL90"]
        )
    )

    print("\nTop 10 Underperformers:")
    underperformers = calculator.get_underperformers(10)
    print(
        underperformers.select(
            ["name", "team", "position", "total_points", "xFPL", "delta", "xFPL90"]
        )
    )

    print("\nTop 10 by xFPL90 (best underlying stats per 90):")
    top_xfpl90 = calculator.calculate_xfpl().sort("xFPL90", descending=True).head(10)
    print(
        top_xfpl90.select(
            ["name", "position", "minutes", "xFPL", "xFPL90", "xG90", "xA90"]
        )
    )
