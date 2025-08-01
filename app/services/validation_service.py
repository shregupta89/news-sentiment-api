import json
import os
from typing import Dict, List, Optional

class StockValidationService:
    """Service to validate Indian stock symbols"""
    
    def __init__(self):
        self.valid_stocks = self._load_stock_symbols()
        self.valid_symbols = {stock["symbol"].upper() for stock in self.valid_stocks}
        print(f"✅ Loaded {len(self.valid_symbols)} valid stock symbols")
    
    def _load_stock_symbols(self) -> List[Dict]:
        """Load valid stock symbols from JSON file"""
        try:
            # Get the path to the JSON file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            json_path = os.path.join(current_dir, "..", "utils", "stock_symbols.json")
            json_path = os.path.normpath(json_path)
            
            with open(json_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            print("⚠️ stock_symbols.json not found, using empty list")
            return []
        except json.JSONDecodeError:
            print("⚠️ Error parsing stock_symbols.json, using empty list")
            return []
    
    def is_valid_symbol(self, symbol: str) -> bool:
        """Check if the given symbol is a valid Indian stock symbol"""
        if not symbol:
            return False
        return symbol.upper().strip() in self.valid_symbols
    
    def get_stock_info(self, symbol: str) -> Optional[Dict]:
        """Get detailed information about a stock symbol"""
        symbol_upper = symbol.upper().strip()
        for stock in self.valid_stocks:
            if stock["symbol"].upper() == symbol_upper:
                return stock
        return None
    
    def get_suggestions(self, partial_symbol: str, limit: int = 5) -> List[Dict]:
        """Get stock suggestions based on partial symbol match"""
        partial_upper = partial_symbol.upper().strip()
        suggestions = []
        
        for stock in self.valid_stocks:
            if partial_upper in stock["symbol"].upper() or partial_upper in stock["name"].upper():
                suggestions.append(stock)
                if len(suggestions) >= limit:
                    break
        
        return suggestions
    
    def validate_and_format_symbol(self, symbol: str) -> str:
        """Validate and return properly formatted symbol"""
        if not self.is_valid_symbol(symbol):
            raise ValueError(f"Invalid stock symbol: {symbol}")
        return symbol.upper().strip()

# Create a singleton instance
stock_validator = StockValidationService()