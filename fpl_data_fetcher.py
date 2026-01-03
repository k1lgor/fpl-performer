# /// script
# dependencies = [
#   "httpx",
#   "polars",
# ]
# ///

"""
FPL Data Fetcher Module

Fetches player statistics from the Fantasy Premier League API.
"""

import httpx
import polars as pl
from typing import Dict, List, Optional


class FPLDataFetcher:
    """Fetches and processes FPL player data from the official API."""

    BASE_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"

    def __init__(self):
        self.raw_data: Optional[Dict] = None
        self.players_df: Optional[pl.DataFrame] = None

    def fetch_data(self) -> Dict:
        """
        Fetch raw data from FPL API.

        Returns:
            Dict containing all FPL data (players, teams, events, etc.)

        Raises:
            httpx.HTTPError: If API request fails
        """
        try:
            response = httpx.get(self.BASE_URL, timeout=10.0)
            response.raise_for_status()
            self.raw_data = response.json()
            return self.raw_data
        except httpx.HTTPError as e:
            raise Exception(f"Failed to fetch FPL data: {e}")

    def _get_team_name(self, team_id: int, teams: List[Dict]) -> str:
        """Get team short name from team ID."""
        for team in teams:
            if team["id"] == team_id:
                return team["short_name"]
        return "Unknown"

    def _get_position_name(self, element_type: int) -> str:
        """Convert element_type to position name."""
        positions = {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}
        return positions.get(element_type, "Unknown")

    def process_players(self) -> pl.DataFrame:
        """
        Process raw FPL data into a structured DataFrame.

        Returns:
            Polars DataFrame with player statistics
        """
        if not self.raw_data:
            self.fetch_data()

        elements = self.raw_data["elements"]
        teams = self.raw_data["teams"]

        # Extract relevant player data
        players_data = []
        for player in elements:
            # Only include players with minutes played
            if player["minutes"] > 0:
                players_data.append(
                    {
                        "id": player["id"],
                        "name": player["web_name"],
                        "team": self._get_team_name(player["team"], teams),
                        "position": self._get_position_name(player["element_type"]),
                        "element_type": player["element_type"],
                        "total_points": player["total_points"],
                        "minutes": player["minutes"],
                        "expected_goals": float(player["expected_goals"]),
                        "expected_assists": float(player["expected_assists"]),
                        "expected_goals_conceded": float(
                            player["expected_goals_conceded"]
                        ),
                        "bps": player["bps"],
                        "clean_sheets": player["clean_sheets"],
                        "starts": player["starts"],
                        "bonus": player["bonus"],
                    }
                )

        self.players_df = pl.DataFrame(players_data)
        return self.players_df

    def get_players_dataframe(self) -> pl.DataFrame:
        """
        Get processed players DataFrame. Fetches and processes if not already done.

        Returns:
            Polars DataFrame with player statistics
        """
        if self.players_df is None:
            self.process_players()
        return self.players_df


def fetch_fpl_data() -> pl.DataFrame:
    """
    Convenience function to fetch and return FPL player data.

    Returns:
        Polars DataFrame with player statistics
    """
    fetcher = FPLDataFetcher()
    return fetcher.get_players_dataframe()


if __name__ == "__main__":
    # Test the data fetcher
    print("Fetching FPL data...")
    df = fetch_fpl_data()
    print(f"\nFetched {len(df)} players with minutes > 0")
    print(f"\nSample data:\n{df.head()}")
    print(f"\nColumns: {list(df.columns)}")
