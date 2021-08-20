import boto3
import json
import os
from datetime import date

from exporter.to_csv import export_csv_data
from exporter.to_json import export_json_write



class SHInterpreter():
    def __init__(self, config):
        self.config = config
        self.findings_next_token = ''
        self.current_account = ''
        self.current_region = ''
        self.aws_client = None
        self.statistics = {
            "object_list": [],
            "objects": []
        }


    def get_finding_statistics(self, finding):
        if finding['Title'] not in self.statistics["object_list"]:
            self.statistics["object_list"].append(finding['Title'])

            statistic_object = {}
            statistic_object['title'] = finding['Title']

            if 'COUNT' in self.config['statistics']:
                statistic_object['count'] = 1
            if 'RESOURCES' in self.config['statistics']:
                statistic_object['resources'] = [r['Id'] for r in finding['Resources']]

            self.statistics["objects"].append(statistic_object)

        else:
            object_index = self.statistics['object_list'].index(finding['Title'])

            if 'COUNT' in self.config['statistics']:
                self.statistics['objects'][object_index]['count'] = self.statistics['objects'][object_index]['count'] + 1

            if 'RESOURCES' in self.config['statistics']:
                for r in finding['Resources']:
                    if r['Id'] not in self.statistics['objects'][object_index]['resources']:
                        self.statistics['objects'][object_index]['resources'].append(r['Id'])


    def get_findings(self):

        findings = []

        findings_data = self.aws_client.get_findings(
            MaxResults=100, 
            NextToken=self.findings_next_token, 
            Filters=self.config["filters"]
            )


        for finding in findings_data["Findings"]:
            findings.append({
                "Title": finding['Title'],
                "Description": finding['Description'],
                "FindingId": finding['Id'],
                "GeneratorId": finding['GeneratorId'],
                "Severity": finding['Severity']['Label']
            })
            self.get_finding_statistics(finding)

        
        if "NextToken" in findings_data:
            self.findings_next_token = findings_data["NextToken"]
        else:
            self.findings_next_token = None

        export_csv_data(
            data=findings, 
            service_name='securityhub', 
            account_name=self.current_account, 
            region_name=self.current_region,
            config=self.config,
            aditional_names=[self.config['filters']['SeverityLabel'][0]['Value']]
            )


    def export_statistics(self):
        today = date.today()
        date_ = today.strftime("%Y%m%d")

        if not os.path.isdir(self.config['results_dir']):
            os.mkdir(self.config['results_dir'])
        
        filename = f'security_hub_statistics_{self.current_account}_{self.current_region}_{date_}.json'

        with open(filename, 'w') as f:
            self.statistics.pop('object_list', None)
            json.dump(self.statistics, f)


    def parse_all_acocunts_and_regions(self):
        for account in self.config["aws_accounts"]:
            for region in self.config["aws_regions"]:
                print(f'SECURITY HUB processing ACCOUNT: {account} and REGION: {region} ...')

                self.current_account = account
                self.current_region = region

                session = boto3.Session(profile_name=account)
                self.aws_client = session.client('securityhub', region_name=region)

                while self.findings_next_token != None:
                    self.get_findings()
            
                self.statistics.pop('object_list', None)
                export_json_write(
                    data=self.statistics,
                    service_name='securityhub',
                    account_name=self.current_account,
                    region_name=self.current_region,
                    config=self.config,
                    aditional_names=[
                        'statistics',
                        self.config['filters']['SeverityLabel'][0]['Value']
                        ]
                )
                self.statistics = {}
