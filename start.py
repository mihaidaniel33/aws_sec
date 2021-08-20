from aws.guardduty import GDInterpreter
from aws.securityhub import SHInterpreter
from aws.s3 import S3Interpreter
import yaml



if __name__ == '__main__':
    with open('./config/config.yaml', 'r') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    
    sh = SHInterpreter(config["security_hub"])
    sh.parse_all_acocunts_and_regions()

    # gd = GDInterpreter(config["guard_duty"])
    # gd.parse_all_acocunts_and_regions()

    s3 = S3Interpreter(config=config["s3"])
    s3.parse_all_acocunts_and_regions()
