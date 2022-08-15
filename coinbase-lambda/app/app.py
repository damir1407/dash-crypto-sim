import json
import boto3
from websocket import create_connection
import time


def handler(event, context):

    client = boto3.client("kinesis", region_name="us-east-1")
    list_of_currencies = ["BTC-USD", "ETH-USD", "DOGE-USD", "XRP-USD", "SHIB-USD", "TRX-USD", "LEO-USD", "ANKR-USD"]
    ws = create_connection("wss://ws-feed.exchange.coinbase.com")
    data = json.loads('{"type":"subscribe","product_ids":[],"channels":["ticker",{"name":"ticker","product_ids":[]}]}')
    data["product_ids"] = list_of_currencies
    data["channels"][1]["product_ids"] = list_of_currencies

    t_end = time.time() + 60 * 14
    while time.time() < t_end:
        message = ws.recv()
        if json.loads(message)["type"] != "subscriptions" and json.loads(message)["type"] != "error":
            print(message)
            client.put_record(
                StreamName="dev-coinbase-stream",
                Data=message,
                PartitionKey=json.loads(message)["product_id"],
            )
    ws.close()

    return "success"
