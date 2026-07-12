import asyncio
import json
import os

import boto3
from botocore.config import Config

def create_sqs_client():
    return boto3.client(
        "sqs",
        endpoint_url=os.getenv("SQS_ENDPOINT_URL") or None,
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        config=Config(connect_timeout=3, read_timeout=5, retries={"max_attempts": 2}),
    )

async def send_email_verification_message(sqs_client, user_id: int, email: str, token: str) -> None:
    queue_url = os.getenv("EMAIL_VERIFICATION_QUEUE_URL")
    if not queue_url:
        return
    body = json.dumps({"v": 1, "user_id": user_id, "email": email, "token": token})
    try:
        await asyncio.to_thread(sqs_client.send_message, QueueUrl=queue_url, MessageBody=body)
    except Exception:
        # Registration must not fail because the queue is unavailable.
        pass
