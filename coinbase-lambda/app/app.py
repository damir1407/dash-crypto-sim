import json
import boto3
from websocket import create_connection
import time


def handler(event, context):

    client = boto3.client("kinesis", region_name="us-east-1")

    ws = create_connection("wss://ws-feed.exchange.coinbase.com")
    ws.send(
        '{"type":"subscribe","product_ids":["ETH-USD", "BTC-USD"],"channels":["ticker",{"name":"ticker","product_ids":["ETH-USD"]}]}'
    )

    timeout = 300  # [seconds]
    timeout_start = time.time()
    while time.time() < timeout_start + timeout:
        time.sleep(1)
        message = ws.recv()
        if json.loads(message)["type"] != "subscriptions":
            client.put_record(
                StreamName="dev-coinbase-stream", Data=message, PartitionKey=json.loads(message)["product_id"]
            )

    ws.close()
    
    return "success"
