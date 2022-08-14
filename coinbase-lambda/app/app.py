import json
import boto3
from websocket import create_connection
import time


def handler(event, context):

    client = boto3.client("kinesis", region_name="us-east-1")

    ws = create_connection("wss://ws-feed.exchange.coinbase.com")
    ws.send(
        '{"type":"subscribe","product_ids":["ETH-EUR", "BTC-EUR"],"channels":["ticker",{"name":"ticker","product_ids":["BTC-EUR", "ETH-EUR"]}]}'
    )

    timeout = 300  # [seconds]
    timeout_start = time.time()
    while time.time() < timeout_start + timeout:
        message = ws.recv()
        if json.loads(message)["type"] != "subscriptions":
            print(message)
            client.put_record(
                StreamName="dev-coinbase-stream", Data=message, PartitionKey=json.loads(message)["product_id"]
            )
            time.sleep(2)
    ws.close()
    
    return "success"
