import pandas as pd
import numpy as np
import logging
from datetime import datetime

class MaxPainCalculator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_max_pain(self, options_data, current_stock_price=None):
        """
        Calculate the max pain price based on options data.
        
        Args:
            options_data: List of dictionaries containing option contract data
            current_stock_price: Current price of the underlying stock
            
        Returns:
            Dictionary containing max pain price and related statistics
        """
        try:
            if not options_data:
                raise ValueError("No options data provided")
            
            # Convert to DataFrame for easier manipulation
            df = pd.DataFrame(options_data)
            
            # Filter out contracts with zero open interest
            df = df[df['open_interest'] > 0]
            
            if df.empty:
                raise ValueError("No options with open interest found")
            
            # Get unique strike prices
            strike_prices = sorted(df['strike_price'].unique())
            
            # Vectorized pain calculation for better performance
            pain_values = []
            
            # Separate calls and puts
            calls_df = df[df['contract_type'] == 'call']
            puts_df = df[df['contract_type'] == 'put']
            
            for strike in strike_prices:
                # Calculate pain for calls (ITM calls when price < strike)
                itm_calls = calls_df[calls_df['strike_price'] < strike]
                call_pain = ((strike - itm_calls['strike_price']) * itm_calls['open_interest'] * 100).sum()
                
                # Calculate pain for puts (ITM puts when price > strike)
                itm_puts = puts_df[puts_df['strike_price'] > strike]
                put_pain = ((itm_puts['strike_price'] - strike) * itm_puts['open_interest'] * 100).sum()
                
                pain_values.append({
                    'strike_price': strike,
                    'total_pain': call_pain + put_pain
                })
            
            # Convert to DataFrame
            pain_df = pd.DataFrame(pain_values)
            
            # Find the strike price with minimum total pain (max pain for option holders)
            max_pain_row = pain_df.loc[pain_df['total_pain'].idxmin()]
            max_pain_price = max_pain_row['strike_price']
            
            # Calculate Put/Call ratio
            total_put_oi = df[df['contract_type'] == 'put']['open_interest'].sum()
            total_call_oi = df[df['contract_type'] == 'call']['open_interest'].sum()
            pc_ratio = total_put_oi / total_call_oi if total_call_oi > 0 else 0
            
            # Get nearby strikes for context
            max_pain_idx = pain_df.index[pain_df['strike_price'] == max_pain_price][0]
            nearby_strikes = []
            
            for i in range(max(0, max_pain_idx - 2), min(len(pain_df), max_pain_idx + 3)):
                nearby_strikes.append({
                    'strike': pain_df.iloc[i]['strike_price'],
                    'pain': pain_df.iloc[i]['total_pain'],
                    'is_max_pain': i == max_pain_idx
                })
            
            result = {
                'max_pain_price': max_pain_price,
                'current_stock_price': current_stock_price,
                'distance_from_current': abs(current_stock_price - max_pain_price) if current_stock_price else None,
                'percentage_from_current': ((max_pain_price - current_stock_price) / current_stock_price * 100) if current_stock_price else None,
                'put_call_ratio': round(pc_ratio, 3),
                'total_put_oi': total_put_oi,
                'total_call_oi': total_call_oi,
                'nearby_strikes': nearby_strikes,
                'calculation_time': datetime.now().isoformat(),
                'total_contracts_analyzed': len(df)
            }
            
            self.logger.info(f"Max pain calculated at ${max_pain_price:.2f}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error calculating max pain: {str(e)}")
            raise
    
    def get_expiration_dates(self, options_data):
        """
        Get unique expiration dates from options data.
        """
        df = pd.DataFrame(options_data)
        return sorted(df['expiration_date'].unique())
    
    def calculate_max_pain_by_expiration(self, options_data, current_stock_price=None):
        """
        Calculate max pain for each expiration date.
        """
        results = {}
        df = pd.DataFrame(options_data)
        
        for exp_date in self.get_expiration_dates(options_data):
            exp_data = df[df['expiration_date'] == exp_date].to_dict('records')
            try:
                results[exp_date] = self.calculate_max_pain(exp_data, current_stock_price)
                results[exp_date]['expiration_date'] = exp_date
            except Exception as e:
                self.logger.warning(f"Could not calculate max pain for {exp_date}: {str(e)}")
                continue
        
        return results
    
    def calculate_nearest_expiration_max_pain(self, options_data, current_stock_price=None):
        """
        Calculate max pain for the nearest expiration date only.
        """
        df = pd.DataFrame(options_data)
        
        # Get nearest expiration date
        today = datetime.now().date()
        df['exp_date'] = pd.to_datetime(df['expiration_date']).dt.date
        df['days_to_exp'] = df['exp_date'].apply(lambda x: (x - today).days)
        
        # Filter to nearest expiration with enough liquidity
        nearest_exp = df[df['days_to_exp'] >= 0].groupby('expiration_date')['open_interest'].sum()
        nearest_exp = nearest_exp[nearest_exp > 1000].index.min()  # Minimum OI threshold
        
        if not nearest_exp:
            raise ValueError("No suitable expiration date found")
        
        # Calculate max pain for nearest expiration
        nearest_data = df[df['expiration_date'] == nearest_exp].to_dict('records')
        result = self.calculate_max_pain(nearest_data, current_stock_price)
        result['expiration_date'] = nearest_exp
        result['days_to_expiration'] = (pd.to_datetime(nearest_exp).date() - today).days
        
        return result