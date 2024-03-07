import argparse
import boto3
import csv
import logging
import os
from botocore.exceptions import ClientError

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')

# Boto3 client
cw_client = boto3.client("cloudwatch")

def check_for_existing_composite_alarm(instance_name, sns_topic):
    """Check if a composite alarm already exists for the given instance name and SNS topic."""
    try:
        alarms = cw_client.describe_alarms(AlarmNamePrefix=instance_name, ActionPrefix=sns_topic)
        for alarm in alarms.get("CompositeAlarms", []):
            if alarm["AlarmName"] == f"{instance_name}--composite-alarm":
                return True
    except ClientError as e:
        logging.error(f"Error checking for existing composite alarms: {e}")
    return False

def list_existing_metric_alarms(instance_id, metric_name):
    """List existing metric alarms for a given EC2 instance and metric."""
    try:
        response = cw_client.describe_alarms_for_metric(
            MetricName=metric_name,
            Namespace="AWS/EC2",
            Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
        )
        return [alarm["AlarmName"] for alarm in response.get("MetricAlarms", [])]
    except ClientError as e:
        logging.error(f"Error listing metric alarms for {instance_id} and metric {metric_name}: {e}")
        return []

def create_metric_alarm(instance_id, alarm_name, alarm_description, metric_name, threshold, evaluation_periods, datapoints_to_alarm, comparison_operator):
    """Create a CloudWatch metric alarm."""
    try:
        cw_client.put_metric_alarm(
            AlarmName=alarm_name,
            AlarmDescription=alarm_description,
            ActionsEnabled=False,
            MetricName=metric_name,
            Namespace="AWS/EC2",
            Statistic="Average",
            Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
            Period=300,
            EvaluationPeriods=evaluation_periods,
            DatapointsToAlarm=datapoints_to_alarm,
            Threshold=threshold,
            ComparisonOperator=comparison_operator,
            TreatMissingData="missing",
        )
        logging.info(f"Metric alarm created for {alarm_name}")
    except ClientError as e:
        logging.error(f"Error creating the metric alarm {alarm_name}: {e}")

def create_composite_alarm(instance_name, sns_topic, alarm_rule):
    """Create a composite CloudWatch alarm."""
    try:
        cw_client.put_composite_alarm(
            AlarmName=f"{instance_name}--composite-alarm",
            AlarmRule=alarm_rule,
            ActionsEnabled=True,
            AlarmActions=[sns_topic],
            OKActions=[sns_topic],
            InsufficientDataActions=[],
        )
        logging.info(f"Composite alarm created with name {instance_name}--composite-alarm")
    except ClientError as e:
        logging.error(f"Error creating the composite alarm for {instance_name}: {e}")

def validate_file_exists(file_path):
    """Check if the specified file exists."""
    if not os.path.exists(file_path):
        logging.error(f"The file {file_path} does not exist.")
        raise FileNotFoundError

def main(csv_file, sns_topic_arn, cpu_threshold, failed_status_threshold, network_threshold):
    validate_file_exists(csv_file)

    with open(csv_file, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            instance_id = row['InstanceId']
            instance_name = row['InstanceName']

            if check_for_existing_composite_alarm(instance_name, sns_topic_arn):
                logging.info(f"Composite alarm already exists for {instance_name}. Skipping...")
                continue

            # Creating individual metric alarms
            cpu_alarm_name = f"{instance_name}--CPUUtilization"
            if cpu_alarm_name not in list_existing_metric_alarms(instance_id, "CPUUtilization"):
                create_metric_alarm(instance_id, cpu_alarm_name, "CPU Utilization alarm", "CPUUtilization", cpu_threshold, 5, 3, "GreaterThanOrEqualToThreshold")

            status_check_alarm_name = f"{instance_name}--StatusCheckFailed"
            if status_check_alarm_name not in list_existing_metric_alarms(instance_id, "StatusCheckFailed"):
                create_metric_alarm(instance_id, status_check_alarm_name, "Status Check Failed alarm", "StatusCheckFailed", failed_status_threshold, 3, 1, "GreaterThanOrEqualToThreshold")

            network_in_alarm_name = f"{instance_name}--NetworkIn"
            if network_in_alarm_name not in list_existing_metric_alarms(instance_id, "NetworkIn"):
                create_metric_alarm(instance_id, network_in_alarm_name, "Network In alarm", "NetworkIn", network_threshold, 5, 1, "GreaterThanOrEqualToThreshold")

            # Creating composite alarm
            alarm_rule = f"ALARM(\"{cpu_alarm_name}\") OR ALARM(\"{status_check_alarm_name}\") OR ALARM(\"{network_in_alarm_name}\")"
            create_composite_alarm(instance_name, sns_topic_arn, alarm_rule)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create composite alarms in CloudWatch for EC2 instances")
    parser.add_argument("--csv_file", required=True, help="Path to CSV file containing instance IDs and names")
    parser.add_argument("--sns_topic_arn", required=True, help="ARN of the SNS topic to use for notifications")
    parser.add_argument("--cpu_threshold", type=float, default=80, help="CPU utilization threshold (default: 80%)")
    parser.add_argument("--failed_status_threshold", type=int, default=1, help="Failed status checks threshold (default: 1)")
    parser.add_argument("--network_threshold", type=float, default=25000000, help="Network In threshold in bytes (default: 25MB)")

    args = parser.parse_args()

    try:
        main(args.csv_file, args.sns_topic_arn, args.cpu_threshold, args.failed_status_threshold, args.network_threshold)
    except Exception as e:
        logging.error(f"Failed to execute script: {e}")
