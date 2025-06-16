#!/usr/bin/env python3
import os
import sys
sys.path.append('src')

from polygon_client import PolygonOptionsClient
from max_pain_calculator import MaxPainCalculator
from data_manager import DataManager
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_max_pain_calculation():
    """Test the max pain calculation with real data."""
    try:
        # Initialize components
        ticker = os.getenv('TICKER', 'SPY')
        polygon_client = PolygonOptionsClient()
        calculator = MaxPainCalculator()
        data_manager = DataManager()
        
        print(f"\nTesting Max Pain Calculator for {ticker}")
        print("=" * 50)
        
        # Get current stock price
        current_price = polygon_client.get_current_stock_price(ticker)
        print(f"Current {ticker} price: ${current_price:.2f}")
        
        # Get options data for nearest expiration in one fast call
        print("\nFetching options data for nearest expiration...")
        nearest_exp, options_data = polygon_client.get_options_snapshot_fast(ticker)
        
        if not options_data:
            print("No options data retrieved")
            return
        
        print(f"Retrieved {len(options_data)} option contracts for {nearest_exp}")
        
        # Calculate max pain
        print("\nCalculating max pain...")
        result = calculator.calculate_max_pain(options_data, current_price)
        result['expiration_date'] = nearest_exp
        result['days_to_expiration'] = (datetime.strptime(nearest_exp, '%Y-%m-%d').date() - datetime.now().date()).days
        
        # Save results
        data_manager.save_calculation_results(ticker, result)
        data_manager.save_daily_summary(ticker, result, current_price)
        
        # Generate and print report
        report = data_manager.generate_report(ticker, result, current_price)
        print("\n" + report)
        
        print("\nTest completed successfully!")
        
    except Exception as e:
        print(f"\nError during test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    test_max_pain_calculation()