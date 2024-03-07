

![image](https://github.com/JuanJ4/AWS-Automation/assets/23548321/0694aa63-390b-40b8-94e6-1ea0a658a102)





Python Environment: Ensure Python is installed on your machine. This script is compatible with Python 3.x versions.

AWS Credentials: The script uses boto3, the AWS SDK for Python. Your environment must be configured with AWS credentials (Access Key ID and Secret Access Key) that have permissions to manage CloudWatch alarms and access EC2 instances. Typically, you can configure credentials using the AWS CLI with aws configure command or by setting the AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and optionally AWS_SESSION_TOKEN environment variables.

Required Python Packages: Install the required Python packages (boto3). If not already installed, you can install them using pip:

Copy code
pip install boto3
CSV File: Ensure you have the CSV file mentioned in your script, which contains the InstanceId and InstanceName columns for the EC2 instances you want to monitor.

Script File: Save the Python script to a file on your machine, for example, create_cloudwatch_alarms.py.

Modify Permissions (Optional): If you're using a Unix-like system (Linux, macOS), you might need to make the script executable. Run:

bash
Copy code
chmod +x create_cloudwatch_alarms.py
Running the Script: Use the following command to run the script, replacing <csv_file_path>, <sns_topic_arn>, and other arguments with your actual values:

css
Copy code
python create_cloudwatch_alarms.py --csv_file <csv_file_path> --sns_topic_arn <sns_topic_arn> --cpu_threshold 80 --failed_status_threshold 1 --network_threshold 25000000
Here is an explanation of the parameters:

--csv_file: The path to your CSV file containing the EC2 instances' information.
--sns_topic_arn: The ARN of the SNS topic to which alerts will be sent.
--cpu_threshold, --failed_status_threshold, --network_threshold: The thresholds for CPU utilization, status check failures, and network input, respectively. These have default values as per your script, so you only need to specify them if you want different thresholds.
Ensure all the prerequisites are met, and replace the placeholder values with actual data relevant to your AWS environment. After that, you can run the script as described above.






