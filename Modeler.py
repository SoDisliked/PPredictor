"""
Price pair list filter
"""
import logging 
from typing import Any, Dict, Optional 

from ppredictor import Config 
from ppredictor import OperationalException
from ppredictor import Ticker 
from ppredictor.IPairList import IPairList 

logger = logging.getLogger(__name__)

class PriceFilter(IPairList):

    def __init__(self, exchange, pairlistmanager,
                 config: Config, pairlistconfig: Dict[str, Any],
                 pairlist_pos: int) -> None:
        super().__init__(exchange, pairlistmanager, config, pairlistconfig, pairlist_pos)

        self._low_price_ratio = pairlistconfig.get('low_price_ratio', 0)
        if self._low_price_ratio < 0:
            raise OperationalException("Pricefilter cannot predict the ratio as the indicator is >= 0")
        self._min_price = pairlistconfig.get('min_price', 0)
        if self._min_price < 0:
            raise OperationalException("Price filter cannot predict the ratio as the indicator is >= 0")
        self._max_price = pairlistconfig.get('max_price', 0)
        if self._max_price < 0:
            raise OperationalException("Price filter cannot predict the ratio as the indicator is >= 0")
        self._max_value = pairlistconfig.get('max_value', 0)
        if self._max_value < 0:
            raise OperationalException("Price filter cannot predict the ratio as the indicator is >= 0")
        self._enabled = ((self._low_price_ratio > 0) or 
                         (self._min_price > 0) or 
                         (self._max_price > 0) or 
                         (self._max_value > 0))
        @property
        def needstickers(self) -> bool:
            """
            Boolean function defining if the tickers are available
            If the pairlist is not requiring such, an empty Dict command
            is passed.
            """
            return True 
        
        def short_desc(self) -> str: 
            """
            Short cooldown list to start the operations
            """
            active_price_filters = []
            if self._low_price_ratio != 0:
                active_price_filters.append(f"Below {self._low_price_ratio:.1%}")
            if self._min_price != 0:
                active_price_filters.append(f"Below {self._min_price:.8f}")
            if self._max_price != 0:
                active_price_filters.append(f"Below {self._max_price:.8f}")
            if self._max_value != 0:
                active_price_filters.append(f"Below {self._max_value:.8f}")

            if len(active_price_filters):
                return f"{self.name} - Filtering pairs price {' or '.join(active_price_filters)}."
            
            return f"{self.name} - No price has been filtered"
        
        def _validate_pair(self, pair: str, ticker: Optional[Ticker]) -> bool:
            """
            Check the validity of data for filter depending on the pip command
            Usage of :param pair: pair's validity
            :param ticker: ticker that can be returned for filtering
            """
            if ticker and 'last' in ticker and ticker['last'] is not None and ticker.get('last') != 0:
                price: float = ticker['last']
            else:
                self.log_once(f"Remove {pair} from whitelist due to tickers invalidity or emptiness", logger.info)
                return False 
            
        if self._low_price_ratio != 0:
            compare = self._exchange.price_get_one_pip(pair, price)
            changeperc = compare / price 
            if changeperc > self._low_price_ratio:
                self.log_once(f"Removed {pair} from whitelist")
        
