import random
from datetime import datetime, timedelta

class DemoDataGenerator:
    """Generate realistic demo options data for testing."""
    
    def generate_options_chain(self, ticker='SPY', current_price=450.0):
        """Generate demo options chain data."""
        options_data = []
        
        # Generate expiration dates (weekly for next 4 weeks, then monthly)
        expiration_dates = []
        today = datetime.now()
        
        # Weekly expirations
        for i in range(4):
            exp_date = today + timedelta(days=(7 * i + (4 - today.weekday())))
            expiration_dates.append(exp_date.strftime('%Y-%m-%d'))
        
        # Monthly expirations
        for i in range(1, 4):
            exp_date = today + timedelta(days=30 * i)
            expiration_dates.append(exp_date.strftime('%Y-%m-%d'))
        
        # Generate strikes around current price
        strike_interval = 1.0 if current_price < 100 else 5.0 if current_price < 500 else 10.0
        min_strike = int(current_price * 0.9 / strike_interval) * strike_interval
        max_strike = int(current_price * 1.1 / strike_interval) * strike_interval
        
        strikes = []
        strike = min_strike
        while strike <= max_strike:
            strikes.append(strike)
            strike += strike_interval
        
        # Generate options for each expiration and strike
        for exp_date in expiration_dates:
            days_to_exp = (datetime.strptime(exp_date, '%Y-%m-%d') - today).days
            
            for strike in strikes:
                # Generate realistic open interest based on distance from current price
                distance_pct = abs(strike - current_price) / current_price
                
                # Calls
                call_oi_base = random.randint(500, 5000)
                if strike < current_price:  # ITM calls have higher OI
                    call_oi = int(call_oi_base * (1 + (current_price - strike) / current_price))
                else:  # OTM calls
                    call_oi = int(call_oi_base * max(0.1, 1 - distance_pct * 2))
                
                # Add some randomness
                call_oi = max(0, call_oi + random.randint(-200, 200))
                
                options_data.append({
                    'contract_ticker': f'O:{ticker}{exp_date.replace("-", "")}C{int(strike * 1000)}',
                    'strike_price': strike,
                    'contract_type': 'call',
                    'expiration_date': exp_date,
                    'open_interest': call_oi,
                    'volume': random.randint(0, call_oi // 2),
                    'last_price': max(0.01, (current_price - strike) if strike < current_price else 0.5 * max(0, 1 - distance_pct))
                })
                
                # Puts
                put_oi_base = random.randint(500, 5000)
                if strike > current_price:  # ITM puts have higher OI
                    put_oi = int(put_oi_base * (1 + (strike - current_price) / current_price))
                else:  # OTM puts
                    put_oi = int(put_oi_base * max(0.1, 1 - distance_pct * 2))
                
                # Add some randomness and typically higher put OI
                put_oi = max(0, int(put_oi * 1.2) + random.randint(-200, 200))
                
                options_data.append({
                    'contract_ticker': f'O:{ticker}{exp_date.replace("-", "")}P{int(strike * 1000)}',
                    'strike_price': strike,
                    'contract_type': 'put',
                    'expiration_date': exp_date,
                    'open_interest': put_oi,
                    'volume': random.randint(0, put_oi // 2),
                    'last_price': max(0.01, (strike - current_price) if strike > current_price else 0.5 * max(0, 1 - distance_pct))
                })
        
        # Add some concentrated open interest at key levels
        # This creates more realistic max pain scenarios
        key_strikes = [
            round(current_price / strike_interval) * strike_interval,  # ATM
            round((current_price - 5) / strike_interval) * strike_interval,  # Slightly below
            round((current_price + 5) / strike_interval) * strike_interval,  # Slightly above
        ]
        
        for i, option in enumerate(options_data):
            if option['strike_price'] in key_strikes and option['expiration_date'] == expiration_dates[0]:
                options_data[i]['open_interest'] = int(option['open_interest'] * random.uniform(1.5, 2.5))
        
        return options_data