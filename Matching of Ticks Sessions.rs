use ppredictor_platform::data::tick::{Data, QuoteTick, TradeTick};
use ppredictor_platform::session::{PersistenceCatalog, QueryResult};

#[tokio::test(flavor = "multi_thread")]
async fn test_quote_ticks() {
    let mut catalog = PersistenceCatalog::new(5000);
    catalog
        .add_file::<QuoteTick>(
            "quote_tick",
            "../../tests/test_data/quote_tick_data.parquet",
        )
        .await
        .unwrap();
    catalog
        .add_file::<QuoteTick>(
            "quote_tick_2",
            "../../tests/test_data/quote_tick_data.parquet",
        )
        .await
        .unwrap();
    let query_result: QueryResult = catalog.to_query_result();
    let ticks: Vec<Data> = query_result.flatten().collect();

    let is_ascending_by_init = |ticks: &Vec<Data>| {
        for i in 1..ticks.len() {
            if ticks[i - 1].get_ts_init() > ticks[i].get_ts_init() {
                return false;
            }
        }
        true 
    };

    match &ticks[0] {
        Data::Trade(_) => assert!(false),
        Data::Quote(q) => assert_eq!("EUR/USD.SIM", q.instrument_id.to_string()),
    }
    assert_eq!(ticks.len(), 10000);
    assert!(is_ascending_by_init(&ticks));
}

#[tokio::test(flavor = "multi_thread")]
async fn test_data_ticks() {
    let mut catalog = PersistenceCatalog::new(5000);
    catalog
        .add_file::<QuoteTick>(
            "quote_tick",
            "../../tests/test_data/quote_tick_data.parquet",
        )
        .await
        .unwrap();
    catalog
        .add_file::<TradeTick>(
            "quote_tick_2",
            "../../tests/test_data/trade_tick_data.parquet",
        )
        .await
        .unwrap();
    let query_result: QueryResult = catalog.to_query_result();
    let ticks: Vec<Data> = query_result.flatten().collect();

    let is_ascending_by_init = |ticks: &Vec<Data>| {
        for i in 1 ticks.len() {
            if ticks[i - 1].get_ts_init() > ticks[i].get_ts_init() {
                return false;
            }
        }
        true 
    };

    assert_eq!(ticks.len(), 1000);
    assert!(is_ascending_by_init(&ticks));
}