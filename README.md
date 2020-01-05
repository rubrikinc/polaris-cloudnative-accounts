## :blue_book: Documentation

Requirements:

* Python v3.6.5+
* AWS Python SDK (boto3) v1.7.60+
* AWS Python SDK (botocore) v1.10.60
* Python Requests library v2.18.4+

Export the following environment variables:

* All Scripts
  * `POLARIS_SUBDOMAIN`
  * `POLARIS_USERNAME`
  * `POLARIS_PASSWORD`
  * `AWS_ACCOUNT_NUMBER`
  * `AWS_PROFILE`

* Account add script
  * `AWS_ACCOUNT_NAME`
  * `AWS_REGIONS`

* Account delete script
  * `POLARIS_DELETE_SNAPSHOTS`

The values of `POLARIS_SUBDOMAIN`, `POLARIS_USERNAME`, and `POLARIS_PASSWORD` can also be assigned in each script if you are retrieving from a secret store programmatically somehow. The user in Polaris must have the `Administrator` role.

`POLARIS_DELETE_SNAPSHOTS` must be set to `true` or `false`. This variable controls if the existing snapshots for the account in AWS will be deleted when the account is deleted.

`AWS_ACCOUNT_NUMBER` is the AWS account number that you want to manage in Polaris.

`AWS_ACCOUNT_NAME` is the name that the AWS account will be given in Polaris. This is only needed when adding accounts.

`AWS_REGIONS` are the regions in AWS that Polaris will manage.  
    * List should be comma separated list of regions.
        * Example: `export AWS_REGIONS="us-west-2,us-east-2"

`AWS_PROFILE` is the profile in the local `.aws/credentials` file to use for accessing AWS.

Once configured, run these scripts using Python 3.6+ from an EC2 instance or an external instance. The system that runs this script must have Internet access to Polaris and access to the AWS APIs.

The `polaris-add-aws-cloud-native-account.py` script will add an AWS account to Polaris for Cloud Native protection.

## :muscle: How You Can Help

We glady welcome contributions from the community. From updating the documentation to adding more functions for Python, all ideas are welcome. Thank you in advance for all of your issues, pull requests, and comments! :star:

* [Contributing Guide](CONTRIBUTING.md)
* [Code of Conduct](CODE_OF_CONDUCT.md)

## :pushpin: License

* [MIT License](LICENSE)

## :point_right: About Rubrik Build

We encourage all contributors to become members. We aim to grow an active, healthy community of contributors, reviewers, and code owners. Learn more in our [Welcome to the Rubrik Build Community](https://github.com/rubrikinc/welcome-to-rubrik-build) page.

We'd  love to hear from you! Email us: build@rubrik.com :love_letter:
