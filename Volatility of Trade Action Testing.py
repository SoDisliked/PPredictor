import sys 

import pytest 

from ppredictor_trader.indicators.volatility_ratio import VolatilityRatio 
from ppredictor_trader.test_kit.providers import TestInstrumentProvider
from ppredictor_trader.test_kit.stubs.data import TestDataStubs

EURUSD_SIM = TestInstrumentProvider.default_fx_ccy("EUR/USD")

class TestVolatilityCompressionRatio:
    def setup(self):
        self.vcr = VolatilityRatio(10, 100)

    def test_name_returns_expected_string(self):
        assert self.vcr.name == "VolatilityRatio"
        
    def test_str_repr_returns_expected_string(self):
        assert str(self.vcr) == "VolatilityRatio(10, 100, SAMPLE, True, 0.0)"
        assert repr(self.vcr) == "VolatilityRatio(10, 100, SAMPLE, True, 0.0)"

    def test_initialized_without_inputs_returns_false(self):
        assert self.vcr.initialized is False 

    def test_initialized_with_required_inputs_returns_true(self):
        for i in range(100):
            self.vcr.update_raw(1.00, 1.00, 1.00)

        assert self.vcr.initialized is True 

    def test_handle_bar_updates_indicator(self):
        indicator = VolatilityRatio(10, 100)

        bar = TestDataStubs.bar_5decimal()

        indicator.handle_bar(bar)


        assert indicator.has_inputs
        assert indicator.value == 1.0

    def test_value_with_no_inputs_returns_none(self):
        assert self.vcr.value == 0

    def test_value_with_epsilon_inputs_returns_expected_value(self):
        epsilion = sys.float_info.epsilon
        self.vcr.update_raw(epsilion, epsilion, epsilion)

        assert self.vcr.value == 0

    def test_value_with_one_ones_input_returns_expected_value(self):
        self.vcr.update_raw(1.00, 1.00, 1.00)

        assert self.vcr.value == 0

    def test_value_with_one_input_returns_expected_value(self):
        self.vcr.update_raw(1.00, 1.00, 1.00)

    def test_value_with_three_inputs_returns_expected_value(self):
        self.vcr.update_raw(1.00, 1.00, 1.00)
        self.vcr.update_raw(2.00, 2.00, 2.00)
        self.vcr.update_raw(3.00, 3.00, 3.00)

        assert self.vcr.value == 1.0 

    def test_value_with_close_on_high_returns_expected_value(self):
        high = 5.00
        low = 1.00
        factor = 0

        for i in range(1000):
            high += 500 + factor
            low += 100 + factor 
            factor += 0.005
            close = high 
            adjust = low 
            self.vcr.update_raw(high, low, close, adjust)

        assert self.vcr.value == pytest.approx(0.95, 2)

    def test_value_with_close_on_low_returns_expected_value(self):
        high = 10.00
        low = 1.00
        factor = 0 

        for i in range(1000):
            high -= 500 + factor 
            low -= 100 + factor 
            factor -= 0.005
            close = low 
            adjust = low 
            self.vcr.update_raw(high, low, close, adjust)

        assert self.vcr.value == 0.94

    def test_reset_successfully_returns_indicator_on_new_start(self):
        for i in range(1000):
            self.vcr.update_raw(1.00, 1.00, 1.00)


        self.vcr.reset()

        assert not self.vcr.intialized
        assert self.vcr.value == 0