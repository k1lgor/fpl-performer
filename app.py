# /// script
# dependencies = [
#   "streamlit",
#   "polars",
# ]
# ///

"""
FPL Over/Underperformance Analyzer - Streamlit App

Displays top overperforming and underperforming FPL players based on xFPL calculations.
Split by regular starters vs rotation/bench players.
"""

import streamlit as st
import polars as pl
from fpl_data_fetcher import fetch_fpl_data
from xfpl_calculator import XFPLCalculator


# Page configuration
st.set_page_config(page_title="FPL Performance Analyzer", page_icon="⚽", layout="wide")

# Minutes threshold to distinguish regular players from rotation/bench
REGULAR_PLAYER_MINUTES = 900  # ~10 full matches (900 minutes)


@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_and_calculate_data():
    """Load FPL data and calculate xFPL."""
    players_df = fetch_fpl_data()
    calculator = XFPLCalculator(players_df)
    results_df = calculator.calculate_xfpl()
    return results_df, calculator


def display_performance_table(df, title, caption, color_map, is_overperformer=True):
    """Display a styled performance table."""
    st.subheader(title)
    st.caption(caption)

    # Prepare display dataframe - convert to pandas for streamlit
    display_df = df.select(
        [
            "name",
            "team",
            "position",
            "minutes",
            "total_points",
            "xFPL",
            "delta",
            "performance_pct",
        ]
    ).to_pandas()

    display_df.columns = [
        "Player",
        "Team",
        "Pos",
        "Mins",
        "Actual",
        "xFPL",
        "Delta",
        "Perf %",
    ]
    display_df.insert(0, "Rank", range(1, len(display_df) + 1))

    # Style the dataframe
    if is_overperformer:
        styled_df = display_df.style.background_gradient(
            subset=["Delta"], cmap=color_map, vmin=0
        )
    else:
        styled_df = display_df.style.background_gradient(
            subset=["Delta"], cmap=color_map, vmax=0
        )

    styled_df = styled_df.format(
        {
            "Mins": "{:.0f}",
            "Actual": "{:.0f}",
            "xFPL": "{:.1f}",
            "Delta": "{:+.1f}",
            "Perf %": "{:.0f}%",
        }
    )

    st.dataframe(styled_df, hide_index=True, width="stretch", height=400)


def main():
    st.title("⚽ FPL Over/Underperformance Analyzer")
    st.markdown("""
    Compare players' **Actual FPL Points** to their **Expected FPL Points (xFPL)**
    to identify who's overperforming (lucky) vs. underperforming (unlucky).

    **Split by playing time:** Regular starters (≥900 mins) vs Rotation/Bench players (<900 mins)
    """)

    # Strategy Guide - Always visible
    with st.expander("📖 **How to Use This Tool for FPL Transfers**", expanded=False):
        st.markdown("""
        ### Understanding the Metrics

        **xFPL** = Expected FPL Points based on underlying stats (xG, xA, xCS, BPS)
        - Uses improved algorithm: per-match clean sheet probability, BPS-based bonus estimation

        **xFPL90** = Expected points per 90 minutes ⭐ **NEW**
        - Fair comparison between players with different minutes
        - Key metric for identifying true quality vs just playing time

        **Delta** = Actual Points - xFPL
        - **Positive (+)**: Overperforming underlying stats
        - **Negative (-)**: Underperforming underlying stats

        **Performance %** = (Actual / xFPL) × 100
        - **>100%**: Overperforming
        - **<100%**: Underperforming
        - **~100%**: Performing as expected

        ---

        ### 🎯 FPL Transfer Strategy

        #### ✅ **BUY TARGETS** (Underperformers)
        **Who to look for:**
        - **High xFPL90** (top 25% of players per 90 minutes)
        - **Negative delta** (-8 or worse)
        - **45+ actual points** (proven quality)

        **Why buy?** Elite underlying stats but unlucky with results. They're:
        - Creating tons of chances (high xG/xA)
        - Playing well defensively (low xGC for defenders)
        - Getting into bonus positions (high BPS)
        - Just not getting the points... yet!

        **Example:** A midfielder with 6.5 xFPL90, 60 actual points, 75 xFPL (-15 delta)
        → Elite quality, temporarily unlucky, **prime buy target** ✅

        #### ⚠️ **SELL CANDIDATES** (Overperformers with Weak Stats)
        **Who to avoid/sell:**
        - **Low xFPL90** (<4.0 points per 90)
        - **High positive delta** (+12 or more)
        - **35+ actual points** (has trade value)

        **Why sell?** Weak underlying stats but got lucky. They're:
        - Not creating many chances (low xG/xA)
        - Conceding often (high xGC for defenders)
        - Low involvement (low BPS)
        - Just scored a few lucky goals/clean sheets

        **⚠️ IMPORTANT:** Elite finishers like Haaland, Salah have high xFPL90 (6-7+) even when overperforming
        → This is **sustainable** overperformance (skill), not luck → **Keep them!**

        #### 🚫 **NOT Sell Candidates**
        Players with **high xFPL90** who overperform:
        - Haaland (xFPL90: 6.84) - Elite finisher, beats xG consistently
        - Salah, Palmer, etc. - World-class players
        - These players **should** overperform because they're genuinely that good

        ---

        ### 💡 Key Principles

        1. **xFPL90 is King**: Use it to identify true quality regardless of minutes played
        2. **Regression to the Mean**: Overperformers regress down, underperformers regress up
        3. **Sample Size Matters**: Trust 900+ minutes players more than rotation players
        4. **Elite Players Exempt**: High xFPL90 players can sustainably beat their xG/xA
        5. **Buy Low, Sell High**: Transfer before the market catches on!

        ---

        ### 📊 What's Different in This Tool?

        **Improved Algorithm:**
        - ✅ Accurate clean sheet calculation (per-match probability)
        - ✅ BPS-based bonus estimation (not circular logic)
        - ✅ Per-90 metrics for fair comparison
        - ✅ Percentile-based recommendations (adapts to player pool)
        """)

    st.markdown("---")

    # Load data
    with st.spinner("Loading FPL data..."):
        try:
            results_df, calculator = load_and_calculate_data()
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return

    # Summary statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Players", len(results_df))
    with col2:
        avg_delta = results_df["delta"].mean()
        st.metric("Avg Over/Under", f"{avg_delta:+.2f}")
    with col3:
        max_over = results_df["delta"].max()
        st.metric("Max Overperformance", f"+{max_over:.1f}")
    with col4:
        max_under = results_df["delta"].min()
        st.metric("Max Underperformance", f"{max_under:.1f}")

    st.markdown("---")

    # Split data by minutes
    regular_players = results_df.filter(pl.col("minutes") >= REGULAR_PLAYER_MINUTES)
    rotation_players = results_df.filter(pl.col("minutes") < REGULAR_PLAYER_MINUTES)

    # Filter by delta sign (all overperformers with +delta, all underperformers with -delta)
    regular_over = regular_players.filter(pl.col("delta") >= 0).sort(
        "delta", descending=True
    )
    regular_under = regular_players.filter(pl.col("delta") <= 0).sort(
        "delta", descending=False
    )
    rotation_over = rotation_players.filter(pl.col("delta") >= 0).sort(
        "delta", descending=True
    )
    rotation_under = rotation_players.filter(pl.col("delta") <= 0).sort(
        "delta", descending=False
    )

    # Tabs for different views
    tab1, tab2 = st.tabs(
        ["🏃 Regular Starters (≥900 mins)", "🪑 Rotation/Bench (<900 mins)"]
    )

    with tab1:
        st.info(f"**{len(regular_players)} players** with ≥900 minutes played")

        col_left, col_right = st.columns(2)

        with col_left:
            display_performance_table(
                regular_over,
                f"🔥 Overperformers (Delta ≥ 0) - {len(regular_over)} Players",
                "Regular players scoring MORE than expected (potentially unsustainable)",
                "Greens",
                is_overperformer=True,
            )

        with col_right:
            display_performance_table(
                regular_under,
                f"❄️ Underperformers (Delta ≤ 0) - {len(regular_under)} Players",
                "Regular players scoring LESS than expected (due for correction)",
                "Reds_r",
                is_overperformer=False,
            )

    with tab2:
        st.info(f"**{len(rotation_players)} players** with <900 minutes played")

        col_left, col_right = st.columns(2)

        with col_left:
            display_performance_table(
                rotation_over,
                f"🔥 Overperformers (Delta ≥ 0) - {len(rotation_over)} Players",
                "Rotation players scoring MORE than expected (small sample size)",
                "Greens",
                is_overperformer=True,
            )

        with col_right:
            display_performance_table(
                rotation_under,
                f"❄️ Underperformers (Delta ≤ 0) - {len(rotation_under)} Players",
                "Rotation players scoring LESS than expected (small sample size)",
                "Reds_r",
                is_overperformer=False,
            )

    st.markdown("---")

    # Transfer Recommendations Section
    st.header("💰 Transfer Recommendations")
    st.markdown("""
    Based on xFPL analysis, here are the **best buy targets** (underperformers with high xFPL)
    and **sell candidates** (overperformers likely to regress).
    """)

    # IMPROVED Transfer Recommendations (Percentile-Based + Per-90 Metrics)

    # Calculate percentiles for xFPL90 (quality per 90 minutes)
    xfpl90_75th = regular_players.select(pl.col("xFPL90").quantile(0.75)).item()

    # BUY TARGETS: High-quality players (top 25% xFPL90) who are underperforming
    buy_targets = (
        regular_players.filter(
            (pl.col("xFPL90") > xfpl90_75th)  # Top 25% underlying stats per 90
            & (pl.col("total_points") > 45)  # Has proven quality
            & (pl.col("delta") < -8)  # Underperforming
            & (pl.col("minutes") > 900)  # Regular starter
        )
        .sort(["delta", "xFPL90"], descending=[False, True])
        .head(20)
    )

    # SELL CANDIDATES: Weak xFPL90 players who are overperforming
    sell_candidates = (
        regular_players.filter(
            (pl.col("xFPL90") < 4.0)  # Weak stats (<4 pts/90)
            & (pl.col("total_points") > 35)  # Has value
            & (pl.col("delta") > 12)  # Significantly overperforming
            & (pl.col("performance_pct") > 125)  # >125% of expected
        )
        .sort("delta", descending=True)
        .head(20)
    )

    rec_col1, rec_col2 = st.columns(2)

    with rec_col1:
        st.subheader("✅ Top 20 Buy Targets")
        st.caption(
            f"Top 25% quality (xFPL90 > {xfpl90_75th:.2f}) + underperforming - elite stats, bad form"
        )

        if len(buy_targets) > 0:
            buy_display = buy_targets.select(
                [
                    "name",
                    "team",
                    "position",
                    "minutes",
                    "total_points",
                    "xFPL",
                    "xFPL90",
                    "delta",
                ]
            ).to_pandas()

            buy_display.columns = [
                "Player",
                "Team",
                "Pos",
                "Mins",
                "Actual",
                "xFPL",
                "xFPL90",
                "Delta",
            ]
            buy_display.insert(0, "Rank", range(1, len(buy_display) + 1))

            st.dataframe(
                buy_display.style.background_gradient(
                    subset=["Delta"], cmap="Reds_r", vmax=0
                ).format(
                    {
                        "Mins": "{:.0f}",
                        "Actual": "{:.0f}",
                        "xFPL": "{:.1f}",
                        "xFPL90": "{:.2f}",
                        "Delta": "{:+.1f}",
                    }
                ),
                hide_index=True,
                width="stretch",
                height=400,
            )
        else:
            st.info("No strong buy targets found with current criteria.")

    with rec_col2:
        st.subheader("⚠️ Top 20 Sell Candidates")
        st.caption("Weak stats (xFPL90 < 4.0) + overperforming - unsustainable luck")

        if len(sell_candidates) > 0:
            sell_display = sell_candidates.select(
                [
                    "name",
                    "team",
                    "position",
                    "minutes",
                    "total_points",
                    "xFPL",
                    "xFPL90",
                    "delta",
                ]
            ).to_pandas()

            sell_display.columns = [
                "Player",
                "Team",
                "Pos",
                "Mins",
                "Actual",
                "xFPL",
                "xFPL90",
                "Delta",
            ]
            sell_display.insert(0, "Rank", range(1, len(sell_display) + 1))

            st.dataframe(
                sell_display.style.background_gradient(
                    subset=["Delta"], cmap="Greens", vmin=0
                ).format(
                    {
                        "Mins": "{:.0f}",
                        "Actual": "{:.0f}",
                        "xFPL": "{:.1f}",
                        "xFPL90": "{:.2f}",
                        "Delta": "{:+.1f}",
                    }
                ),
                hide_index=True,
                width="stretch",
                height=400,
            )
        else:
            st.info("No strong sell candidates found with current criteria.")

    st.markdown("---")

    # Refresh button
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    # Expandable methodology section
    with st.expander("📊 How is xFPL Calculated?"):
        st.markdown("""
        **Expected FPL Points (xFPL)** uses an improved industry-standard algorithm:

        ### Core Components

        1. **Expected Goals Points**: `xG × position_multiplier`
           - Goalkeepers: **10 points** per goal
           - Defenders: **6 points** per goal
           - Midfielders: **5 points** per goal
           - Forwards: **4 points** per goal

        2. **Expected Assists Points**: `xA × 3`

        3. **Expected Clean Sheet Points**
           - **Per-match probability**: `e^(-xGC_per_match)` (not cumulative!)
           - Matches played = minutes ÷ 90
           - Expected clean sheets = CS probability × matches played
           - Goalkeepers/Defenders: 4 points per clean sheet
           - Midfielders: 1 point per clean sheet
           - Forwards: 0 points

        4. **Expected Bonus Points** ⭐
           - **Estimated from BPS** (not actual bonus - no circular logic!)
           - BPS per match = total BPS ÷ matches played
           - Expected bonus ≈ (BPS per match ÷ 100) × 0.035 × matches
           - ~3.5 bonus points per 100 BPS per match (empirical rate)

        5. **Expected Appearance Points**:
           - 2 points for playing ≥60 minutes (from starts)
           - 1 point for playing <60 minutes (from substitute minutes)

        ### New Metrics ⭐

        - **xFPL90** = (xFPL ÷ minutes) × 90 → Fair comparison regardless of playing time
        - **xGI** = xG + xA → Total attacking threat
        - **xGI90** = (xGI ÷ minutes) × 90 → Attacking threat per 90 minutes

        ### Performance Metrics

        **Delta** = Actual Points - xFPL

        - **Positive Delta**: Overperforming (could be skill or luck - check xFPL90!)
        - **Negative Delta**: Underperforming (likely due for improvement)

        **Performance %** = (Actual ÷ xFPL) × 100

        ### Data Source

        [Official FPL API](https://fantasy.premierleague.com/api/bootstrap-static/) - Updated live
        """)

    # Footer
    st.markdown("---")
    st.caption(
        "Data updates hourly. Last refresh: Check the timestamp in your browser."
    )


if __name__ == "__main__":
    main()
