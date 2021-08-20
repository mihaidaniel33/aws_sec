import boto3
import json

from exporter.to_xlsx import export_xlsx_data
from exporter.to_csv import export_csv_data


class GDInterpreter():
    def __init__(self, config):
        self.config = config
        self.findings_next_token = ''
        self.current_account = ''
        self.current_region = ''
        self.current_aws_client = None
        self.current_detector_list = []
        self.statistics = {
            "object_list": [],
            "objects": []
        }


    def process_resource_by_type(self, resource):
        resource_type = resource["ResourceType"]
        resource_id = ''
        if resource_type == 'AccessKey':
            resource_id = resource['AccessKeyDetails']['AccessKeyId']
        elif resource_type == 'S3Bucket':
            resource_id = ', '.join([ bucket['Arn'] for bucket in resource['S3BucketDetails'] ])
        elif resource_type == 'Instance':
            resource_id = resource['InstanceDetails']['InstanceId']
        else:
            raise Exception('Could not match resource type.')
        
        return f'Resource Type: {resource_type}, Resource ID: {resource_id}'


    def get_detectors(self):
        self.current_detector_list = self.current_aws_client.list_detectors()
        print(self.current_detector_list['DetectorIds'])

    
    def get_findings(self):

        f_ids = {
            "Findings": []
        }

        findings = []


        for detector in self.current_detector_list["DetectorIds"]:
            findings_list = self.current_aws_client.list_findings(DetectorId=detector)

            findings_data = self.current_aws_client.get_findings(
                DetectorId=detector,
                FindingIds=findings_list["FindingIds"],
            )

            for finding in findings_data["Findings"]:
                findings.append({
                    "Title": finding["Title"],
                    "Severity": finding["Severity"],
                    "FindingId": finding["Id"],
                    "DetectorId": detector,
                    "Description": finding["Description"],
                    "Resource": self.process_resource_by_type(finding["Resource"])
                })

        export_xlsx_data(
            data=findings, 
            service_name='guard_duty', 
            account_name=self.current_account, 
            region_name=self.current_region,
            config=self.config
            )


    def parse_all_acocunts_and_regions(self):
        for account in self.config["aws_accounts"]:
            for region in self.config["aws_regions"]:
                print(f'GUARD DUTY processing ACCOUNT: {account} and REGION: {region} ...')

                self.current_account = account
                self.current_region = region

                session = boto3.Session(profile_name=account)
                self.current_aws_client = session.client('guardduty', region_name=region)

                self.get_detectors()
                self.get_findings()
