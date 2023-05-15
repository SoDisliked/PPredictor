from typing import Any, Optional

import numpy as np 
import pandas as pd 

class SortingRatio(PortfolioStatistic):
    """
    Calculates the sorted portfolio statistics
    depending on the trade positions made by
    the user.

    Parameters
    ----------
    Depending on the trading period, defined as 
    7 days or one week.
    """

    def __init__(self, period: int = 252):
        self.period = period

    @property
    def name(self) -> str:
        return f"Sorting ratio ({self.period} days)"

    def calculate_from_returns(self, returns: pd.Series) -> Optional[Any]:
        if not self._check_valid_returns(returns):
            return np.nan 


        returns = self._sample_converted_to_daily_trading_actions(returns)

        downside = np.sqrt((returns[returns < 0] ** 2).sum() / len(returns))
        if downside == 0:
            return np.nan 
        
        res = returns.mean() / downside 

        return res * np.sqrt(self.period)