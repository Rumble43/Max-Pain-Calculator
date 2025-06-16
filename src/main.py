#!/usr/bin/env python3
import logging
import sys
import argparse
from scheduler import MaxPainScheduler

def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/max_pain_calculator.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main entry point for the max pain calculator."""
    parser = argparse.ArgumentParser(description='Max Pain Calculator')
    parser.add_argument(
        '--once', 
        action='store_true', 
        help='Run calculation once instead of scheduling'
    )
    parser.add_argument(
        '--daemon',
        action='store_true',
        help='Run as daemon with daily scheduling'
    )
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        scheduler = MaxPainScheduler()
        
        if args.once:
            logger.info("Running max pain calculation once...")
            scheduler.run_once()
            logger.info("Calculation complete.")
        elif args.daemon:
            logger.info("Starting max pain calculator daemon...")
            scheduler.run_scheduler()
        else:
            # Default: run once
            logger.info("Running max pain calculation...")
            scheduler.run_once()
            
            # Print the report
            from data_manager import DataManager
            dm = DataManager()
            ticker = scheduler.ticker
            
            # Load today's results
            from datetime import datetime
            import json
            import os
            
            date_str = datetime.now().strftime("%Y-%m-%d")
            results_file = os.path.join(
                "data", "daily", f"{ticker}_{date_str}_max_pain.json"
            )
            
            if os.path.exists(results_file):
                with open(results_file, 'r') as f:
                    result = json.load(f)
                
                report = dm.generate_report(
                    ticker, 
                    result, 
                    scheduler.polygon_client.get_current_stock_price(ticker)
                )
                print("\n" + report)
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Application error: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()