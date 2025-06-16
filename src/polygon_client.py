import os
from datetime import datetime, timedelta
from polygon import RESTClient
from dotenv import load_dotenv
import logging

load_dotenv()

class PolygonOptionsClient:
    def __init__(self):
        self.api_key = os.getenv('POLYGON_API_KEY')
        if not self.api_key:
            raise ValueError("POLYGON_API_KEY not found in environment variables")
        
        self.client = RESTClient(self.api_key)
        self.logger = logging.getLogger(__name__)
    
    def get_options_chain(self, ticker, expiration_date=None):
        """
        Fetch the options chain for a given ticker and expiration date.
        If no expiration date is provided, fetches all available options.
        """
        try:
            contracts = []
            
            # Get options contracts
            options_params = {
                'underlying_ticker': ticker,
                'limit': 1000,
                'sort': 'expiration_date',
                'order': 'asc'
            }
            
            if expiration_date:
                options_params['expiration_date'] = expiration_date
                
            # Fetch options contracts
            for contract in self.client.list_options_contracts(**options_params):
                contracts.append(contract)
            
            self.logger.info(f"Fetched {len(contracts)} option contracts for {ticker}")
            return contracts
            
        except Exception as e:
            self.logger.error(f"Error fetching options chain: {str(e)}")
            raise
    
    def get_options_snapshot_for_date(self, ticker, expiration_date):
        """
        Get current snapshot data for options for a specific expiration date.
        
        Args:
            ticker: The underlying ticker symbol
            expiration_date: The specific expiration date (YYYY-MM-DD format)
        """
        try:
            snapshots = []
            
            # Get all options snapshot data
            # The API returns an iterator of snapshot objects
            for snapshot in self.client.list_snapshot_options_chain(ticker):
                try:
                    # Extract details
                    details = snapshot.details if hasattr(snapshot, 'details') else None
                    if not details:
                        continue
                    
                    # Only get contracts for the specific expiration date
                    if details.expiration_date != expiration_date:
                        continue
                    
                    # Extract day data
                    day = snapshot.day if hasattr(snapshot, 'day') else None
                    
                    snapshot_info = {
                        'contract_ticker': details.ticker,
                        'strike_price': float(details.strike_price),
                        'contract_type': details.contract_type,
                        'expiration_date': details.expiration_date,
                        'open_interest': int(snapshot.open_interest) if hasattr(snapshot, 'open_interest') else 0,
                        'volume': int(day.volume) if day and hasattr(day, 'volume') else 0,
                        'last_price': float(day.close) if day and hasattr(day, 'close') else 0
                    }
                    
                    # Only include contracts with some open interest
                    if snapshot_info['open_interest'] > 0:
                        snapshots.append(snapshot_info)
                        
                except Exception as e:
                    self.logger.debug(f"Error processing snapshot: {str(e)}")
                    continue
            
            self.logger.info(f"Retrieved {len(snapshots)} option snapshots for {ticker} expiring {expiration_date}")
            return snapshots
            
        except Exception as e:
            self.logger.error(f"Error getting options snapshot: {str(e)}")
            raise
    
    def get_options_snapshot_fast(self, ticker):
        """
        Get options data for the nearest expiration in a single efficient call.
        Returns the nearest expiration date and its options data.
        """
        try:
            snapshots = []
            today = datetime.now().date()
            nearest_exp = None
            seen_expirations = set()
            
            # Use the iterator but stop after finding nearest expiration data
            count = 0
            for snapshot in self.client.list_snapshot_options_chain(ticker):
                count += 1
                
                # Stop if we've checked too many contracts (safety limit)
                if count > 500:
                    break
                
                try:
                    details = snapshot.details if hasattr(snapshot, 'details') else None
                    if not details:
                        continue
                    
                    exp_date = details.expiration_date
                    exp_date_obj = datetime.strptime(exp_date, '%Y-%m-%d').date()
                    
                    # Skip past expirations
                    if exp_date_obj < today:
                        continue
                    
                    # Track expiration dates we've seen
                    seen_expirations.add(exp_date)
                    
                    # Set nearest expiration on first valid date
                    if nearest_exp is None:
                        nearest_exp = exp_date
                        self.logger.info(f"Found nearest expiration: {nearest_exp}")
                    
                    # Only collect data for the nearest expiration
                    if exp_date == nearest_exp:
                        day = snapshot.day if hasattr(snapshot, 'day') else None
                        oi = int(snapshot.open_interest) if hasattr(snapshot, 'open_interest') else 0
                        
                        if oi > 0:
                            snapshot_info = {
                                'contract_ticker': details.ticker,
                                'strike_price': float(details.strike_price),
                                'contract_type': details.contract_type,
                                'expiration_date': exp_date,
                                'open_interest': oi,
                                'volume': int(day.volume) if day and hasattr(day, 'volume') else 0,
                                'last_price': float(day.close) if day and hasattr(day, 'close') else 0
                            }
                            snapshots.append(snapshot_info)
                    
                    # If we've seen more than one expiration and have data, we can stop
                    elif len(seen_expirations) > 1 and len(snapshots) > 50:
                        self.logger.info(f"Stopping early - found {len(snapshots)} contracts for nearest expiration")
                        break
                        
                except Exception as e:
                    self.logger.debug(f"Error processing snapshot: {str(e)}")
                    continue
            
            self.logger.info(f"Retrieved {len(snapshots)} contracts for {ticker} expiring {nearest_exp}")
            return nearest_exp, snapshots
            
        except Exception as e:
            self.logger.error(f"Error getting fast options snapshot: {str(e)}")
            raise
    
    def get_current_stock_price(self, ticker):
        """
        Get the current stock price for the underlying ticker.
        """
        try:
            # Get the previous close price
            prev_close = self.client.get_previous_close_agg(ticker)
            if prev_close and len(prev_close) > 0:
                return prev_close[0].close
            
            # Fallback to aggregates
            from datetime import datetime, timedelta
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            
            aggs = self.client.get_aggs(
                ticker=ticker,
                multiplier=1,
                timespan="day",
                from_=yesterday,
                to=yesterday
            )
            
            if aggs and len(aggs) > 0:
                return aggs[0].close
            
            raise ValueError(f"Could not get price for {ticker}")
            
        except Exception as e:
            self.logger.error(f"Error getting stock price: {str(e)}")
            raise