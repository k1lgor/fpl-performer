# FPL Over/Underperformance Analyzer ⚽

Compare Fantasy Premier League players' **Actual FPL Points** to their **Expected FPL Points (xFPL)** to identify overperformers and underperformers.

## Features

- 📊 **xFPL Calculation**: Industry-standard algorithm using xG, xA, xCS, BPS
- 📈 **xFPL90 Metrics**: Per-90 minute stats for fair player comparison
- 💰 **Transfer Recommendations**: Percentile-based buy/sell targets
- 🔥 **Overperformers/Underperformers**: Split by regular starters vs rotation players
- 🎨 **Interactive Dashboard**: Built with Streamlit
- 🔄 **Live Data**: Fetches latest stats from official FPL API

## Installation

This project uses `uv` for package management.

```bash
# Install dependencies
uv sync
```

## Usage

Run the Streamlit app:

```bash
uv run streamlit run app.py
```

Or test individual modules:

```bash
# Test data fetcher
uv run python fpl_data_fetcher.py

# Test xFPL calculator
uv run python xfpl_calculator.py
```

## How xFPL is Calculated

**Expected FPL Points (xFPL)** uses an improved algorithm:

| Component        | Formula                                                      |
| ---------------- | ------------------------------------------------------------ |
| **Goals**        | `xG × position_multiplier` (GKP: 10, DEF: 6, MID: 5, FWD: 4) |
| **Assists**      | `xA × 3`                                                     |
| **Clean Sheets** | `e^(-xGC_per_match) × matches × CS_points`                   |
| **Bonus**        | Estimated from BPS (~3.5 per 100 BPS per match)              |
| **Appearance**   | 2 pts for ≥60 min, 1 pt for <60 min                          |

### Key Metrics

- **xFPL90** = xFPL per 90 minutes (fair comparison regardless of playing time)
- **Delta** = Actual Points - xFPL
- **xGI** = xG + xA (total attacking threat)

### Transfer Strategy

- **Buy Targets**: Top 25% xFPL90 + negative delta = Elite players in bad form
- **Sell Candidates**: Low xFPL90 (<4.0) + positive delta (>12) = Unsustainable luck

## Project Structure

```
fpl-performer/
├── app.py                  # Streamlit frontend
├── fpl_data_fetcher.py     # FPL API data fetcher (httpx + polars)
├── xfpl_calculator.py      # xFPL calculation engine
├── pyproject.toml          # Project configuration
├── RULES.md                # Development rules
└── README.md               # This file
```

## Deployment Options

### Docker Deployment (for any platform)

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install uv && uv sync
EXPOSE 8501
CMD ["uv", "run", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## Data Source

[Official FPL API](https://fantasy.premierleague.com/api/bootstrap-static/)

## Tech Stack

- **httpx** - HTTP client (per RULES.md)
- **polars** - DataFrame processing (per RULES.md)
- **streamlit** - Web dashboard
- **uv** - Package management

## License

[MIT](LICENSE)
