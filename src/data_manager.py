import json
import csv
import os
from datetime import datetime, timedelta
import logging
import numpy as np

class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle numpy types."""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        return super(NumpyEncoder, self).default(obj)

class DataManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.data_dir = "data"
        self.ensure_directories()
    
    def ensure_directories(self):
        """Create necessary directories if they don't exist."""
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(os.path.join(self.data_dir, "daily"), exist_ok=True)
        os.makedirs(os.path.join(self.data_dir, "summaries"), exist_ok=True)
    
    def save_calculation_results(self, ticker, results):
        """
        Save detailed calculation results to JSON file.
        """
        try:
            date_str = datetime.now().strftime("%Y-%m-%d")
            filename = os.path.join(
                self.data_dir, 
                "daily", 
                f"{ticker}_{date_str}_max_pain.json"
            )
            
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, cls=NumpyEncoder)
            
            self.logger.info(f"Saved calculation results to {filename}")
            
        except Exception as e:
            self.logger.error(f"Error saving calculation results: {str(e)}")
            raise
    
    def save_daily_summary(self, ticker, result, current_price):
        """
        Save daily summary to CSV for tracking over time.
        """
        try:
            csv_file = os.path.join(
                self.data_dir, 
                "summaries", 
                f"{ticker}_max_pain_history.csv"
            )
            
            # Check if file exists to determine if we need headers
            file_exists = os.path.exists(csv_file)
            
            with open(csv_file, 'a', newline='') as f:
                writer = csv.writer(f)
                
                # Write headers if new file
                if not file_exists:
                    headers = [
                        'date', 'ticker', 'current_price', 'expiration_date',
                        'days_to_expiration', 'max_pain_price', 'distance_dollars', 
                        'distance_percent', 'put_call_ratio', 'total_put_oi', 
                        'total_call_oi', 'contracts_analyzed'
                    ]
                    writer.writerow(headers)
                
                # Write data
                date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                row = [
                    date_str,
                    ticker,
                    current_price,
                    result['expiration_date'],
                    result.get('days_to_expiration', 0),
                    result['max_pain_price'],
                    result['distance_from_current'],
                    result['percentage_from_current'],
                    result['put_call_ratio'],
                    result['total_put_oi'],
                    result['total_call_oi'],
                    result['total_contracts_analyzed']
                ]
                writer.writerow(row)
            
            self.logger.info(f"Saved daily summary to {csv_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving daily summary: {str(e)}")
            raise
    
    def load_historical_data(self, ticker, days=30):
        """
        Load historical max pain data for analysis.
        """
        try:
            csv_file = os.path.join(
                self.data_dir, 
                "summaries", 
                f"{ticker}_max_pain_history.csv"
            )
            
            if not os.path.exists(csv_file):
                return []
            
            data = []
            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Convert string values to appropriate types
                    row['current_price'] = float(row['current_price'])
                    row['max_pain_price'] = float(row['max_pain_price'])
                    row['distance_dollars'] = float(row['distance_dollars']) if row['distance_dollars'] else None
                    row['distance_percent'] = float(row['distance_percent']) if row['distance_percent'] else None
                    row['put_call_ratio'] = float(row['put_call_ratio'])
                    row['total_put_oi'] = int(row['total_put_oi'])
                    row['total_call_oi'] = int(row['total_call_oi'])
                    data.append(row)
            
            # Filter by days if specified
            if days:
                cutoff_date = datetime.now() - timedelta(days=days)
                data = [
                    row for row in data 
                    if datetime.strptime(row['date'], "%Y-%m-%d %H:%M:%S") >= cutoff_date
                ]
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error loading historical data: {str(e)}")
            return []
    
    def generate_report(self, ticker, result, current_price):
        """
        Generate a human-readable report of the max pain calculation.
        """
        try:
            report_lines = [
                f"MAX PAIN REPORT - {ticker}",
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"Current Price: ${current_price:.2f}",
                "=" * 60,
                "",
                f"EXPIRATION: {result['expiration_date']} ({result.get('days_to_expiration', 'N/A')} days)",
                f"Max Pain Price: ${result['max_pain_price']:.2f}",
                f"Distance from Current: ${abs(result['distance_from_current']):.2f} "
                f"({result['percentage_from_current']:+.2f}%)",
                f"Put/Call Ratio: {result['put_call_ratio']}",
                f"Total Put OI: {result['total_put_oi']:,}",
                f"Total Call OI: {result['total_call_oi']:,}",
                f"Contracts Analyzed: {result['total_contracts_analyzed']}",
                "",
                "Nearby Strike Analysis:",
            ]
            
            for strike_info in result['nearby_strikes']:
                marker = " <- MAX PAIN" if strike_info['is_max_pain'] else ""
                report_lines.append(
                    f"  ${strike_info['strike']:.2f}: "
                    f"Pain Value = ${strike_info['pain']:,.0f}{marker}"
                )
            
            report = "\n".join(report_lines)
            
            # Save report
            report_file = os.path.join(
                self.data_dir,
                "daily",
                f"{ticker}_{datetime.now().strftime('%Y-%m-%d')}_report.txt"
            )
            
            with open(report_file, 'w') as f:
                f.write(report)
            
            self.logger.info(f"Generated report: {report_file}")
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating report: {str(e)}")
            return ""