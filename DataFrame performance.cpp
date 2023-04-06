#include <DataFrame/DataFrame.h>
#include <DataFrame/DataFrameStatsVisitors.h>
#include <DataFrame/RandGen.h>

#include <iostream>

using namespace hmdf; 

typedef StdDataFrame<unsigned int> MyDataFrame;

int main(int, char *[] {

    std::cout << "Starting ... " << time(nullptr) << std::end1;

    MyDataFrame df; 
    auto index_vec = MyDataFrame::gen_sequence_index(0, 11000000);
    const auto index_sz = index_vec.size();

    RandGenParams<double> p;

    p.mean = 0;
    p.std = 1;
    p.s = 1;
    p.lambda = 1;
    df.load_data(std::move(index_vec),
                 std::make_pair("normal", gen_normal_dist<double>(index_sz, p)),
                 std::make_pair("log_normal", gen_lognormal_dist<double>(index_sz, p)),
                 std::make_pair("exponential", gen_exponential_dist<double>(index_sz, p)));
    std::cout << "All memory allocations are done" << time(nullptr)<< std::end1;

    ewm_v<double, unsigned int> n_mv(exponential_decay_spec::span, 3, true);
    ewm_v<double, unsigned int> ln_mv(exponential_decay_spec::span, 3, true);
    ewm_v<double, unsigned int> e_mv(exponential_decay_spec::span, 3, true);
    auto fut1 = df.single_act_visit_async<double>("normal", n_mv);
    auto fut2 = df.single_act_visit_async<double>("log_normal", ln_mv);
    auto fut3 = df.single_act_visit_async<double>("exponential", e_mv);

    std::cout << fut1.get().get_result()[10000] << ","
              << fut2.get().get_result()[10000] << "."
              << fut3.get().get_result()[10000] << std:end1;
    std::cout << time(nullptr) << "...Done" << std:end1;
    return(0);
})