import boto3
import os
import json
import logging

from WebSite import WebSite

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    Check the status of a list of websites.  The current state is recorded to
    a dynamodb table.  For any websites where the reachable/unreachable state
    has changed since the last time it was checked, post the URL to an SQS queue.

    Parameters
    ----------
    event: dict
        The event payload.
    context : dict
        The context payload.

    Returns
    -------
    string:
        A json string containing the http status of the lambda call.
    """

    # input from SQS queue
    content = event['Records'][0]['body']
    urls = json.loads(content).get('urls')

    # Initialize the DynamoDB client
    dynamodb = boto3.resource('dynamodb')
    tbl_name = os.environ['TABLE_NAME']
    websites_tbl = dynamodb.Table(tbl_name)
    changed_sites = []

    try:
        response_limit = os.environ['RESPONSE_LIMIT']
        for url in urls:
            try:
                item = websites_tbl.get_item(Key={'url': url})['Item']
                web_site = WebSite(item)
                logger.info(f"Checking website '{web_site.url}'")
                updated_site_dict = web_site.check_website(SlowResponseSeconds=int(response_limit))
                updated_site = WebSite(updated_site_dict)

                if updated_site.is_changed:
                    changed_sites.append(updated_site)

                websites_tbl.put_item(Item=updated_site_dict)
            except Exception as e:
                logger.error(f"Unable to process url {url}:{str(e)}")

        publish_changes(changed_sites)
    except Exception as e:
        logger.error(f"Error scanning DynamoDB: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps("Error scanning DynamoDB")
        }

    return {
        'statusCode': 200,
        'body': json.dumps("Website processed")
    }


def publish_changes(changed_sites: list):
    """
    Publish the changed sites to the SQS queue.

    Parameters
    ----------
    changed_sites: list
        A list of website dictionary objects

    Returns
    -------
        None
    """
    topic_arn = os.environ['SNS_TOPIC']
    status_url = os.environ['STATUS_PAGE_URL']
    topic_name = topic_arn.split(':')[-1]

    if len(changed_sites) > 0:
        logger.info(f"Publishing changes to topic '{topic_name}'")
        try:
            sns = boto3.client('sns')
            msg = "The following websites are reporting a status change:\n\n"
            for site in changed_sites:
                msg += f"{site.url}: status: {site.http_status} - {site.http_reason}\n"

            msg += f"\nYou can view the full website status here: {status_url}"

            sns.publish(TopicArn=topic_arn, Subject='Notification of Website Status Change', Message=msg)

        except Exception as e:
            logger.error(f"Failed publishing change website notifications to {topic_name}: {str(e)}")

