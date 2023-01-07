import sys 
import os 
import csv 
import time 
import datetime 

from ychartspy.client import YChartsClient 

def convert(timestamp):
    return datetime.datetime.fromtimestamp(int(timestamp) / 1e3).strftime('%d-%m-%Y')

def main(symbol_file, parameter_file, output_dir):
    '''
    Params that are used.
    parameter_fils = the path to get the statistical method sampling.
    symbol_file = path to text file with variable outputs that are needed.
    output_dir = output directory.
    '''
    param_fp = open(parameter_file, 'r')

    param_list = []

    count = {}

    for parameter in param_fp:
        param_list.append(parameter.strip())
        count[parameter.strip()] = 0

    client = YChartsClient()

    error_count = False 

    with open(symbol_file, 'r') as sym_fp:
        for symbol in list(csv.reader(sym_fp)):
            row_info = {}
            symbol = symbol[0].strip()

            to_write = []
            to_write.append(['symbol', 'timestamp'])

            non_params = []

            print symbol 

            for parameter in param_list:
                parameter = parameter.strip()
                to_write[0].append(parameter)

            try:
                row = client.get_security_metric(symbol, parameter, start_date="01/01/2020")
            except Exception, e:
                if parameter in error_count:
                    error_count[parameter]+=1
                else:
                    error_count[parameter]=1
                    error_count[parameter]=-1
                non_params.append(parameter)
                continue

            for row_obj in row:
                if row_obj[0] not in row_info:
                    row_info[row_obj[0]] = {}
                row_info[row_obj[0]][str(parameter)]=row_obj[1]

            if count[parameter] == 0:
                count[parameter] = 1

        new_file = open(os.path.join(output_dir, str(symbol) + '.csv'), 'w+')

        for key in sorted(row_info):
            temp = []
            temp.append(str(symbol))
            temp.append(convert(key))

            for parameter in param_list:
                parameter = str(parameter)

                if count[parameter] == 0:
                    param_list.remove(parameter)
                    to_write[0].remove(parameter)
                    continue

                if parameter in row_info[key]:
                    temp.append(row_info[key][parameter])
                else:
                    temp.append('variables')

            to_write.append(temp)

            writer = csv.writer(new_file)
            writer.writerows(to_write)
			
            new_file.close()

'''
	for key in error_count:
		if error_count[key]==7:
			print key
'''
	

if __name__ == '__main__':
  	main(str(sys.argv[1]), str(sys.argv[2]), str(sys.argv[3]))