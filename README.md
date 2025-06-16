# Max Pain Calculator

A Python application that calculates the max pain price for options using Polygon.io API data. The calculator runs daily at market open to analyze options chains and identify price levels where the maximum number of options would expire worthless.

## What is Max Pain?

Max pain is the strike price with the most open options contracts (puts and calls) where the stock would cause financial losses for the largest number of option holders at expiration. Market makers often try to pin the stock price near max pain levels.

## Features

- Fetches real-time options data from Polygon.io API
- Calculates max pain for multiple expiration dates
- Tracks put/call ratios and open interest
- Saves historical data for trend analysis
- Generates daily reports with nearby strike analysis
- Can run as a scheduled daemon or one-time calculation

## Setup

1. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables in `.env`:
```
POLYGON_API_KEY=your_polygon_api_key_here
TICKER=SPY
MARKET_TIMEZONE=America/New_York
```

## Usage

### Run once (default):
```bash
python src/main.py
```

### Run once with explicit flag:
```bash
python src/main.py --once
```

### Run as daemon (scheduled daily at 9:31 AM ET):
```bash
python src/main.py --daemon
```

## Output

The calculator produces:

1. **JSON files** with detailed calculation results in `data/daily/`
2. **CSV history** tracking max pain over time in `data/summaries/`
3. **Text reports** with analysis in `data/daily/`
4. **Log files** in `logs/`

## Example Report

```
MAX PAIN REPORT - SPY
Generated: 2024-01-16 09:31:00
Current Price: $450.25
============================================================

NEAREST EXPIRATION: 2024-01-19
Max Pain Price: $448.00
Distance from Current: $2.25 (-0.50%)
Put/Call Ratio: 1.234

Nearby Strike Analysis:
  $446.00: Pain Value = $1,234,567
  $447.00: Pain Value = $1,123,456
  $448.00: Pain Value = $1,012,345 <- MAX PAIN
  $449.00: Pain Value = $1,134,567
  $450.00: Pain Value = $1,245,678
```

## Data Structure

The calculator analyzes options contracts and produces results containing:
- Max pain price for each expiration
- Current stock price and distance to max pain
- Put/Call ratio
- Total open interest for puts and calls
- Pain values for nearby strikes
