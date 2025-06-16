import schedule
import time
import logging
from datetime import datetime
import pytz
import os
from dotenv import load_dotenv
from polygon_client import PolygonOptionsClient
from max_pain_calculator import MaxPainCalculator
from data_manager import DataManager

load_dotenv()

class MaxPainScheduler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ticker = os.getenv('TICKER', 'SPY')
        self.market_timezone = pytz.timezone(os.getenv('MARKET_TIMEZONE', 'America/New_York'))
        self.polygon_client = PolygonOptionsClient()
        self.calculator = MaxPainCalculator()
        self.data_manager = DataManager()
        
    def is_market_day(self):
        """
        Check if today is a market day (Monday-Friday, excluding holidays).
        Note: This is a simple check. For production, use a market calendar API.
        """
        now = datetime.now(self.market_timezone)
        # Monday = 0, Sunday = 6
        return now.weekday() < 5
    
    def calculate_and_save_max_pain(self):
        """
        Main function to calculate max pain and save results.
        """
        try:
            if not self.is_market_day():
                self.logger.info("Not a market day, skipping calculation")
                return
            
            self.logger.info(f"Starting max pain calculation for {self.ticker}")
            
            # Get current stock price
            current_price = self.polygon_client.get_current_stock_price(self.ticker)
            self.logger.info(f"Current {self.ticker} price: ${current_price:.2f}")
            
            # Get options data for nearest expiration in one fast call
            nearest_exp, options_data = self.polygon_client.get_options_snapshot_fast(self.ticker)
            
            if not options_data:
                self.logger.warning("No options data retrieved")
                return
            
            # Calculate max pain for this specific expiration
            result = self.calculator.calculate_max_pain(options_data, current_price)
            result['expiration_date'] = nearest_exp
            result['days_to_expiration'] = (datetime.strptime(nearest_exp, '%Y-%m-%d').date() - datetime.now().date()).days
            
            # Save results
            self.data_manager.save_calculation_results(self.ticker, result)
            
            # Log summary
            self.logger.info(
                f"Max Pain for {result['expiration_date']} ({result['days_to_expiration']} days): "
                f"${result['max_pain_price']:.2f}, "
                f"P/C Ratio: {result['put_call_ratio']}, "
                f"Distance from current: {result['percentage_from_current']:.2f}%"
            )
            
            # Save daily summary
            self.data_manager.save_daily_summary(self.ticker, result, current_price)
            
            self.logger.info("Max pain calculation completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error in max pain calculation: {str(e)}")
            raise
    
    def run_scheduler(self):
        """
        Run the scheduler to execute calculations at market open.
        """
        # Schedule to run at 9:31 AM ET (1 minute after market open)
        schedule.every().day.at("09:31").do(self.calculate_and_save_max_pain)
        
        self.logger.info("Scheduler started. Will run daily at 9:31 AM ET on market days.")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def run_once(self):
        """
        Run the calculation once (for testing or manual execution).
        """
        self.calculate_and_save_max_pain()