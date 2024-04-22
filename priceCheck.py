import argparse
import requests
from datetime import datetime
import json
from statistics import mean
import time

# Set up the argument parser
parser = argparse.ArgumentParser(description='Fetch price history for a product.')
parser.add_argument('productId', type=int, nargs='?', default=38955607, help='The ID of the product to fetch price history for.')

# Function to fetch price data and check for price drops
def check_price_drop(productId):
    # URL of the request
    url = 'https://www.digitec.ch/api/graphql/pdp-price-history'

    # JSON Payload with productId
    payload = {
        "operationName": "PDP_PRICE_HISTORY",
        "variables": {"productId": productId},
        "query": "query PDP_PRICE_HISTORY($productId: Int!) {\n  priceHistory(productId: $productId) {\n    points {\n      amountIncl\n      amountExcl\n      type\n      validFrom\n      __typename\n    }\n    __typename\n  }\n}"
    }

    # Request headers
    headers = {
        'User-Agent': 'My-Scraper',
    }

    # Send the POST request
    response = requests.post(url, headers=headers, json=payload)

    # Check if the request was successful
    if response.status_code == 200:
        print("Request successful!")
        data = response.json()
        # Extract all data points
        all_data_points = data['data']['priceHistory']['points']

        # Filter out data points with valid prices
        valid_prices = [point['amountIncl'] for point in all_data_points if point['amountIncl'] is not None]

        # Calculate the average price if there are valid prices
        if valid_prices:
            average_price = mean(valid_prices)

            # Check for price drops
            for point in all_data_points:
                if point['amountIncl'] is not None and point['amountIncl'] < 0.7 * average_price:
                    date = datetime.strptime(point['validFrom'], "%Y-%m-%dT%H:%M:%SZ")
                    print(f"Price dropped below 70% of the average on {date.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print("No valid prices available in the data.")
    else:
        print(f"Request failed with status code: {response.status_code}")

# Parse the command-line arguments
args = parser.parse_args()

# Run indefinitely
while True:
    # Check price drop
    check_price_drop(args.productId)
    # Wait for 1 hour before checking again
    time.sleep(3600)  # 3600 seconds = 1 hour
