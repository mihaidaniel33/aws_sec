import os
import csv
from datetime import date


def export_csv_data(data, service_name, account_name, region_name, config, aditional_names=[]):

    today = date.today()
    date_ = today.strftime("%Y%m%d")

    if not os.path.isdir(config['result_dir']):
        os.mkdir(config['result_dir'])

    filename = f'{service_name}_{account_name}_{region_name}_{"_".join(aditional_names)}_{date_}.csv'
    filename = f'{config["result_dir"]}/{filename}'

    if not os.path.isfile(filename):

        with open(filename, 'w') as f:
            header_counter = 0

            for i in data:

                if header_counter == 0:
                    header_row = '           '.join([key for key in i.keys()])
                    f.write(f'{header_row}\n')
                    header_counter = header_counter + 1

                row = ','.join([str(i[k]) for k in i.keys()])
                f.write(f'{row}\n')  

    elif os.path.isfile(filename):
        with open(filename, 'a') as f:
            for i in data:
                writer_obj = csv.writer(f)
                writer_obj.writerow([str(i[k]) for k in i.keys()])
   