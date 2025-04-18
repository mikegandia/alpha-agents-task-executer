# trading_view_extension/queues/sqs_queue_publisher.py

import json
import uuid
from typing import Dict
from config import logger, input_tasks_queue, output_tasks_queue
from trading_view_extension.queue.sqs_queue_publisher_interface import IQueuePublisher

class SQSQueuePublisher(IQueuePublisher):
    def __init__(self):
        """
        Initialize the SQS clients from the SQSQueue dataclass 
        (which were already initialized in config.py).
        """
        try:
            # Use the clients stored in input_tasks_queue and output_tasks_queue
            self.input_sqs_client = input_tasks_queue.client
            self.output_sqs_client = output_tasks_queue.client
            logger.info("SQS clients initialized successfully.")
        except Exception as e:
            logger.exception("Failed to initialize SQS clients.")
            raise

    async def publish_task(self, job: dict) -> None:
        """
        Publish a message to the appropriate SQS FIFO queue based on the action_type.

        Args:
            job (dict): The data to send in the message.
        """
        try:
            if job["status"] == "COMPLETED":
                action_type = job.get("action_type")
                if action_type == "analysis":
                    client = self.input_sqs_client
                    queue_url = input_tasks_queue.url
                    message_group_id = "analysis_tasks"
                elif action_type == "processed":
                    client = self.output_sqs_client
                    queue_url = output_tasks_queue.url
                    message_group_id = "processed_tasks"
                else:
                    logger.warning(f"Unknown action_type '{action_type}'. Defaulting to input_tasks_queue.")
                    client = self.input_sqs_client
                    queue_url = input_tasks_queue.url
                    message_group_id = "analysis_tasks"

                # Ensure 'result' is a LIST by extracting 'results' if present
                # if "result" in job and isinstance(job["result"], dict) and "results" in job["result"]:
                #     job["result"] = job["result"]["results"]  # Extract the list directly
                #     logger.info(f"Successfully extracted trade signal: {job["result"]}")
                
                # if not isinstance(job["result"], list):
                #     logger.error(f"Invalid result format in job: {job}")
                #     job["result"] = []  # Default to an empty list to avoid breaking downstream
                # if "trade_signal" not in job and "result" in job:
                #     job["trade_signal"] = job["result"]  # Assuming 'result' contains the AI response

            elif job["status"] == "RUNNING":
                client = self.output_sqs_client
                queue_url = output_tasks_queue.url
                message_group_id = "analysis_tasks"
                action_type = "running"

            # Generate a unique deduplication ID
            message_deduplication_id = str(uuid.uuid4())

            # Convert the job to a JSON-safe format
            message_body = json.dumps(job, default=str)
            logger.info(f"Message body: {message_body}")
            # Send the message to SQS
            response = client.send_message(
                QueueUrl=queue_url,
                MessageBody=message_body,
                MessageGroupId=message_group_id,
                MessageDeduplicationId=message_deduplication_id
            )

            logger.info(f"Message sent to SQS ({action_type}) with MessageId: {response.get('MessageId')}")

        except Exception as e:
            logger.exception("Failed to publish message to SQS.")
            raise


    # async def publish_task(self, job: dict) -> None:
    #     """
    #     Publish a message to the appropriate SQS FIFO queue based on the action_type.

    #     Args:
    #         job (dict): The data to send in the message.
    #     """
    #     try:
    #         action_type = job.get("action_type")
    #         if action_type == "analysis":
    #             client = self.input_sqs_client
    #             queue_url = input_tasks_queue.url
    #             message_group_id = "analysis_tasks"
    #         elif action_type == "processed":
    #             client = self.output_sqs_client
    #             queue_url = output_tasks_queue.url
    #             message_group_id = "processed_tasks"
    #         else:
    #             logger.warning(f"Unknown action_type '{action_type}'. Defaulting to input_tasks_queue.")
    #             client = self.input_sqs_client
    #             queue_url = input_tasks_queue.url
    #             message_group_id = "analysis_tasks"

    #         message_deduplication_id = str(uuid.uuid4())

    #         if "trade_signal" not in job and "result" in job:
    #             job["trade_signal"] = job["result"]  # Assuming 'result' contains the AI response

    #         # Convert the job dictionary to a JSON string
    #         message_body = json.dumps(job)

    #         response = client.send_message(
    #             QueueUrl=queue_url,
    #             MessageBody=message_body,
    #             MessageGroupId=message_group_id,
    #             MessageDeduplicationId=message_deduplication_id
    #         )

    #         logger.info(f"Message sent to SQS ({action_type}) with MessageId: {response.get('MessageId')}")
    #     except Exception as e:
    #         logger.exception("Failed to publish message to SQS.")
    #         raise
