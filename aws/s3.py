import boto3
import json
from datetime import date

from exporter.to_csv import export_csv_data
from exporter.to_json import export_json_write



class S3Interpreter():
    def __init__(self, config):
        self.config = config
        self.findings_next_token = ''
        self.current_account = ''
        self.current_region = ''
        self.current_aws_client = None
        self.current_bucket = {}
        self.return_data = {
            "Buckets": []
        }


    def get_bucket_list(self):
        resp = self.current_aws_client.list_buckets()

        return [bucket['Name'] for bucket in resp['Buckets']]


    def parse_bucket_access(self):

        pass_acl_check = False
        pass_public_access_check = False
        pass_policy_check = False

        for bucket in self.get_bucket_list():
            self.current_bucket['Name'] = bucket

            try:
                response = self.current_aws_client.get_public_access_block(
                    Bucket=bucket,
                    )
                resp_data = response["PublicAccessBlockConfiguration"]
                if resp_data['BlockPublicAcls'] or resp_data['IgnorePublicAcls'] or resp_data['BlockPublicPolicy'] or resp_data['RestrictPublicBuckets']:
                    self.current_bucket['PublicAccessBlockConfiguration'] = resp_data
                    pass_public_access_check =  True
            except Exception as e:
                self.current_bucket['PublicAccessBlockConfiguration'] = f'MISSING'
                pass_public_access_check = True
            
            try:
                response = self.current_aws_client.get_bucket_acl(
                    Bucket=bucket,
                    )
                for grant in response['Grants']:
                   if 'URI' in grant['Grantee']:
                       if grant['Grantee']['URI'] == 'http://acs.amazonaws.com/groups/global/AllUsers':
                           self.current_bucket['Grant'] = grant
                           pass_acl_check = True
            except Exception as e:
                print(f'Could not process bucket acl {bucket}. ERROR: {e}')
                self.current_bucket['Grant'] = str(e)
                pass_acl_check = True

            try:
                response = self.current_aws_client.get_bucket_policy(
                        Bucket=bucket,
                    )
            except Exception as e:
                if 'NoSuchBucketPolicy' in str(e):
                    pass_policy_check = True


            if pass_acl_check or (pass_public_access_check and pass_policy_check):
                self.return_data['Buckets'].append(self.current_bucket)

            self.current_bucket = {}
            pass_acl_check = False
            pass_public_access_check = False
            pass_policy_check = False
        
        export_json_write(
            data=self.return_data,
            service_name='s3',
            account_name=self.current_account,
            region_name=self.current_region,
            config=self.config
        )



    def parse_all_acocunts_and_regions(self):
        for account in self.config["aws_accounts"]:
            for region in self.config["aws_regions"]:
                print(f'S3 processing ACCOUNT: {account} and REGION: {region} ...')

                self.current_account = account
                self.current_region = region

                session = boto3.Session(profile_name=account)
                self.current_aws_client = session.client('s3', region_name=region)

                self.parse_bucket_access()
