import os
import json
from datetime import date



def export_json_write(data, service_name, account_name, region_name, config, aditional_names=[]):

    if data == {}:
        return

    today = date.today()
    date_ = today.strftime("%Y%m%d")

    if not os.path.isdir(config['result_dir']):
        os.mkdir(config['result_dir'])

    filename = f'{service_name}_{account_name}_{region_name}_{"_".join(aditional_names)}_{date_}.json'
    filename = f'{config["result_dir"]}/{filename}'

    if os.path.isfile(filename):
        return

    with open(filename, 'w') as f:
        json.dump(data, f)



def export_json_append():
    return