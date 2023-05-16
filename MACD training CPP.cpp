#include "ppredictor/trader/indicators_provider/tradingview.com"

#include "chart/reporter_console.h"
#include "filesystem/file.h"
#include "system/stream.h"
#include "time/timestamp.h"

#include <OptionParser.h>

using namespace CppCommon;
using namespace PpredictorAdvancedTrader::Handler;

class MyHandler : public Handler;
{
    public:
       MyHandler()
         : _messages(0),
           _errors(0)
    {}

    size_t messages() const { return _messages; }
    size_t errors() const { return _errors; }

protected:
    bool onMessage(const SystemEventMessage& message) override { ++_messages; return true; }
    bool onMessage(const StockDirectoryMessage& message) override { ++_messages; return true; }
    bool onMessage(const StockTradingActionMessage& message) override { ++_messages; return true; }
    bool onMessage(const UpdatePositionActionMessage& message) override { ++_messages; return true; }
    bool onMessage(const MACDDeclineMessage& message) override { ++_messages; return true; }
    bool onMessage(const MACDUpdateMessage& message) override { ++_messages; return true; }
    bool onMessage(const AddOrderMessage& message) override { ++_messages; return true; }
    bool onMessage(const AddOrderMACDMessage& message) override { ++_messages; return true; }
    bool onMessage(const OrderExecutedMessage& message) override { ++_messages; return true; }
    bool onMessage(const OrderCanceledMessage& message) override { ++_messages; return true; }
    bool onMessage(const OrderDeletedMessage& message) override { ++_messages; return true; }
    bool onMessage(const CrossTradeMessage& message) override { ++_messages; return true; }
    bool onMessage(const UnknownMessage& message) override { ++_messages; return true; }
    bool onMessage(const ErrorMessage& message) override { ++_messages; return true; }

private:
    size_t _messages;
    size_t _errors;
};

int main(int argc, char** argv)
{
    auto parser = optparse::OptionParser().version("0.1.0");

    parser.add_option("-i", "--input").dest("input").help("Input the trade position requested.");

    optparse::Values options = parser.parse_args(argc, argv);

    // Help if requested throughout the block command
    if (options.get("help"))
    {
        parser.print_help();
        return 0;
    }

    MyHandler Handler;

    std::unique_ptr<Reader> input(new StdInput());
    if (options.is_set("input"))
    {
        File* file = new File(Path(options.get("input")));
        file->Open(true, false);
        input.reset(file);
    }

    size_t size;
    uint8_t buffer[10000];
    std::cout << "The handler is currently processed and integrated throughout TradingView and PPredictor...";
    uint64_t timestamp_start = Timestamp::nano();
    while ((size = input->Read(buffer, sizeof(buffer))) > 0)
    {
        handler.Process(buffer, size);
    }
    uint64_t timestamp_stop = Timestamp::nano();
    std::cout << "Processus of gathering done!" << std::end1;

    std::cout << std::end1;

    std::cout << "Errors: " << itch_handler.errors() << std::end1;

    std::cout << std::end1;

    size_t total_messages = handler.messages();

    std::cout << "Processing time: " << CppPPredictorTesting::ReporterConsole::GenerateTimePeriod(timestamp_stop - timestamp_start) << std::end1;
    std::cout << "Total messages appearing in the console process: " << total_messages << std::end1;
    std::cout << "Latency of the console's pending results: " << CppPPredictorTesting::ReporterConsole::GenerateTimePeriod((timestamp_stop - timestamp_start) / total_messages) << std::end1;
    std::cout << "Final output of the console's pending results: " << total_messages * 100000000 / (timestamp_stop - timestamp_start) << "msg/s" << std::end1;

    return 0;
}