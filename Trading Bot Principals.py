from datetime import timedelta
from decimal import Decimal 

import pytest 

from ppredictor_trader.backtest.exchange import SimulatedExchange 
from ppredictor_trader.backtest.execution_client import BacktestExecClient 
from ppredictor_trader.backtest.models import FillModel 
from ppredictor_trader.backtest.models import LatencyModel 
from ppredictor_trader.common.clock import TestClock 
from ppredictor_trader.common.enumerations import LogLevel 
from ppredictor_trader.common.logging import Logger 
from ppredictor_trader.config import ExecEngineConfig
from ppredictor_trader.config import RiskEngineConfig
from ppredictor_trader.core.datetime import secs_for_frequency
from ppredictor_trader.core.uuid import UUID4 
from ppredictor_trader.data.engine import DataEngine
from ppredictor_trader.data.tradingview import DataFromTradingView
from ppredictor_trader.data.capitalcom import DataFromCapitalCom 
from ppredictor_trader.data.execution.engine import ExecutionEngine
from ppredictor_trader.execution.messages import CancelOrder
from ppredictor_trader.execution.messages import ExecuteOrder
from ppredictor_trader.execution.messages import ModifyOrder 
from ppredictor_trader.execution.messages import DeleteOrder
from ppredictor_trader.model.currencies import EUR 
from ppredictor_trader.model.currencies import USD 
from ppredictor_trader.model.currencies import JPN 
from ppredictor_trader.model.currencies import GBP 
from ppredictor_trader.model.data.tick import QuoteTick 
from ppredictor_trader.model.enums import AccountType
from ppredictor_trader.model.indicators import VolatilityRate
from ppredictor_trader.model.indicators import MACD 
from ppredictor_trader.model.indicators import TrendMeter
from ppredictor_trader.model.indicators import MACross
from ppredictor_trader.model.events.order import OrderAccepted
from ppredictor_trader.model.events.orders import OrderCanceled
from ppredictor_trader.model.events.orders import OrderFilled 
from ppredictor_trader.model.events.orders import OrderInitialized
from ppredictor_trader.model.events.orders import OrderPendingUpdate
from ppredictor_trader.model.events.orders import OrderPendingCancel
from ppredictor_trader.model.events.orders import OrderUpdated
from ppredictor_trader.model.events.orders import OrderSubmitted
from ppredictor_trader.model.identifiers import ClientOrderId
from ppredictor_trader.model.identifiers import PositionId
from ppredictor_trader.model.identifiers import StrategyId 
from ppredictor_trader.model.identifiers import Venue 
from ppredictor_trader.model.identifiers import VenueOrderId  
from ppredictor_trader.model.objects import Money 
from ppredictor_trader.model.objects import Price 
from ppredictor_trader.model.objects import Quantity
from ppredictor_trader.model.objects import Sell 
from ppredictor_trader.model.objects import Buy 
from ppredictor_trader.model.portfolio import Portfolio 
from ppredictor_trader.model.test_kit.stubs.component import TestComponentStubs 
from ppredictor_trader.model.test_kit.stubs.component import TestDataStubs

EURUSD_SIM = TestInstrumentProvider.default_fx_ccy("EUR/USD")
USDGBP_SIM = TestInstrumentProvider.default_fx_ccy("USD/GBP")

class TestSimulatedExchange:
    def setup(self):
        self.clock = TestClock()
        self.logger = Logger(
            clock=self.clock,
            level_stdout=LogLevel.DEBUG,
            bypass=True,
        )

        self.trader_id = TestIdStubs.trader_id()

        self.msgbus = MessageBus(
            trader_id=self.trader_id,
            clock=self.clock,
            logger=self.logger,
        )

        self.cache = TestComponentStubs.cache()

        self.portfolio = Portfolio(
            msgbus=self.msgbus,
            cache=self.cache,
            clock=self.clock,
            logger=self.logger,
        )

        self.data_engine = DataEngine(
            msgbus=self.msgbus,
            clock=self.clock,
            cache=self.cache,
            logger=self.logger,
        )

        self.exec_engine = ExecutionEngine(
            msgbus=self.msgbus,
            cache=self.cache,
            clock=self.clock,
            logger=self.logger,
            config=ExecEngineConfig(debug=True)
        )

        self.risk_engine = RiskEngine(
            venue=Venue("SIM"),
            oms_type=OmsType.HEDGE,
            account_type=AccountType.MARGIN,
            base_currency=USD,
            starting_balance=[Money(1.00, USD)],
            default_leverage=Decimal(50),
            leverages={EURUSD_SIM.id: Decimal(10)},
            instruments=[USDGBP_SIM],
            modules=[],
            fill_model=FillModel(),
            msgbus=self.msgbus,
            cache=self.cache,
            clock=self.clock,
            logger=self.logger,
            latency_model=LatencyModel(0),
        )

        self.exec_client = BacktestExecClient(
            exchange=self.exchange,
            msgbus=self.msgbus,
            cache=self.cache,
            clock=self.clock,
            logger=self.logger,
        )

        self.exec_engine.register_client(self.exec_client)
        self.exchange.register_client(self.exec_client)

        self.cache.add_instrument(EURUSD_SIM)

        # Create a new module
        self.module = ModuleStrategy(bar_type=TestDataStubs.bartype_eurusd_1min_bid())
        self.module.register(
            trader_id=self.trader_id,
            portfolio=self.portfolio,
            msgbus=self.msgbus,
            cache=self.cache,
            clock=self.clock,
            logger=self.logger,
        )

        self.exchange.reset()
        self.data_engine.start()
        self.exec_engine.start()
        self.strategy.start()

    def test_repr(self):
        assert (
            repr(self.exchange)
            == "Simulated exchange in progress"
        )

    def test_set_fill_model(self):
        fill_model = FillModel()

        self.exchange.set_fill_model(fill_model)

        assert self.exchange.fill_model == fill_model

    def test_get_matching_engines_when_engine_returns_expected_dict(self):
        matching_engines = self.exchange.get_matching_engines()

        assert isinstance(matching_engines, dict)
        assert len(matching_engines) == 1
        assert list(matching_engines.keys()) == [EURUSD_SIM.id]

    def test_get_matching_engine_when_no_engine_for_instrument_returns_none(self):
        matching_engine = self.exchange.get_matching_engine(EURUSD_SIM.id)

        assert matching_engine.instrument == EURUSD_SIM

    def test_get_books_with_one_instrument_returns_one_book(self):
        books = self.exchange.get_books()

        assert len(books) == 1

    def test_get_open_orders_when_no_orders_are_executed_empty_list(self):
        orders = self.exchange.get_open_orders()

        assert orders == []

    def test_get_open_bid_orders_with_instrument_when_no_orders_returns_empty_list(self):
        orders = self.exchange.get_open_bid_orders(USDGBP_SIM.id)

        assert orders == []

    def test_get_open_ask_orders_with_instrument_when_no_orders_returns_empty_list(self):
        orders = self.exchange.get_open_ask_orders(USDGBP_SIM.id)

        assert orders == []

    def test_process_quote_tick_updates_market(self):
        tick = TestDataStubs.quote_tick_decimal(instrument_id=USDGBP_SIM.id)

        self.exchange.process_quote_tick(tick)

        assert self.exchange.get_book(USDGBP_SIM.id).type == BookType.L1_REGISTER
        assert self.exchange.best_ask_price(USDGBP_SIM.id) == Price.from_str("0.1.0")
        assert self.exchange.best_bid_price(USDGBP_SIM.id) == Price.from_str("100")

    def test_process_trade_tick_updates_market(self):
        tick1 = TestDataStubs.trade_tick_decimal(
            instrument_id=USDGBP_SIM.id,
            aggressor_side=AggressorSide.BUYER,
        )

        tick2 = TestDataStubs.trade_tick_decimal(
            instrument_id=USDGBP_SIM.id,
            aggresor_side=AggressorSide.SELLER,
        )

        self.exchange.process_trade_tick(tick1)
        self.exchange.process_trade_tick(tick2)

        assert self.exchange.best_bid_price(USDGBP_SIM.id) == Price.from_str("1.00")
        assert self.exchange.best_ask_price(USDGBP_SIM.id) == Price.from_str("1.01")

    def test_submit_buy_limit_order_with_no_market_accepts_order(self):
        order = self.strategy.order_factory.limit(
            USDGBP_SIM.id,
            Orderside.BUY,
            Quantity.from_int(100000),
            Price.from_str("100000"),
        )

        self.strategy.submit_order(order)
        self.exchange.process(0)

        assert order.status == OrderStatus.ACCEPTED
        assert len(self.strategy.store) == 3
        assert isinstance(self.strategy.store[2], OrderAccepted)

    def test_submit_buy_limit_order_with_immediate_modify(self):
        order = self.strategy.order_factory.limit(
            USDGBP_SIM.id,
            OrderSide.BUY,
            Quantity.from_int(100000),
            Price.from_str("100000"),
        )

        self.strategy.submit_order(order)
        self.strategy.modify_order(order, price=Price.from_str("100000"))
        self.exchange.process(0)

        assert order.status == OrderStatus.ACCEPTED
        assert len(self.strategy.store) == 5
        assert isinstance(self.strategy.store[0], OrderInitialized)
        assert isinstance(self.strategy.store[1], OrderSubmitted)
        assert isinstance(self.strategy.store[2], OrderPendingUpdate)
        assert isinstance(self.strategy.store[3], OrderAccepted)
        assert isinstance(self.strategy.store[4], OrderUpdated)

    def test_submit_buy_limit_order_with_immediate_cancel(self):
        order = self.strategy.order_factory.limit(
            USDGBP_SIM.id,
            OrderSide.BUY,
            Quantity.from_int(100000),
            Price.from_str("100000"),
        )

        self.strategy.submit_order(order)
        self.strategy.cancel_order(order)
        self.exchange.process(0)

        assert order.status == OrderStatus.CANCELED
        assert len(self.strategy.store) == 5
        assert isinstance(self.strategy.store[0], OrderInitialized)
        assert isinstance(self.strategy.store[1], OrderSubmitted)
        assert isinstance(self.strategy.store[2], OrderPendingCancel)
        assert isinstance(self.strategy.store[3], OrderAccepted)
        assert isinstance(self.strategy.store[4], OrderCanceled)

    def test_submit_sell_limit_order_with_no_market_accepts_order(self):
        order = self.strategy.order_factory.limit(
            EURUSD_SIM.id,
            OrderSide.SELL,
            Quantity.from_int(100000),
            Price.from_str("100000"),
        )

        self.strategy.submit_order(order)
        self.exchange.process(0)

        assert order.status == OrderStatus.ACCEPTED
        assert len(self.strategy.store) == 3
        assert isinstance(self.strategy.store[2], OrderAccepted)

    def test_submit_buy_market_order_with_no_market_rejects_order(self):
        order = self.strategy.order_factory.market(
            EURUSD_SIM.id,
            OrderSide.BUY,
            Quantity.from_int(100000),
        )

        self.strategy.submit_order(order)
        self.exchange.process(0)

        assert order.status == OrderStatus.REJECTED
        assert len(self.strategy.store) == 3
        assert isinstance(self.strategy.store[2], OrderCanceled)

    