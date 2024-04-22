import argparse
import requests
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from statistics import mean
import json

# Set up the argument parser
parser = argparse.ArgumentParser(description='Fetch price history for a product.')
parser.add_argument('productId', type=int, nargs='?', default=38955607, help='The ID of the product to fetch price history for.')

# Parse the command-line arguments
args = parser.parse_args()

# URL of the request
url = 'https://www.digitec.ch/api/graphql/pdp-price-history'

# JSON Payload with productId from the command-line argument
payload = {
    "operationName": "PDP_PRICE_HISTORY",
    "variables": {"productId": args.productId},
    "query": "query PDP_PRICE_HISTORY($productId: Int!) {\n  priceHistory(productId: $productId) {\n    points {\n      amountIncl\n      amountExcl\n      type\n      validFrom\n      __typename\n    }\n    __typename\n  }\n}"
}

# Anforderungs-Header
headers = {
    'User-Agent': 'My-Scraper',
}

# Senden der POST-Anfrage
response = requests.post(url, headers=headers, json=payload)

# Überprüfen des Status-Codes und Ausgeben der Antwort
if response.status_code == 200:
    print("Anfrage erfolgreich!")
    print("Content-Type:", response.headers.get('Content-Type'))
    try:
        data = response.json()  
        # print("Antwort (JSON):", data)  # Versucht die JSON-Antwort auszugeben
        with open(f'C:\dev\Python\Digitec\\{args.productId}.json', 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
    except json.decoder.JSONDecodeError:
        print("Die Antwort enthält keinen validen JSON-Inhalt. Antwort-Text:", response.text)
else:
    print(f"Fehler bei der Anfrage: {response.status_code}")
    print("Antwort-Text:", response.text)  # Fehlerantwort ausgeben


dates = []
prices = []
colors = []

last_price = None
for point in data['data']['priceHistory']['points']:
    date = datetime.strptime(point['validFrom'], "%Y-%m-%dT%H:%M:%SZ")
    price = point['amountIncl']
    
    if price is not None:
        if last_price is not None:
            # If there is a price change, insert an intermediate point for a vertical line
            dates.append(date)
            prices.append(last_price)
            colors.append('green')
        
        last_price = price
        color = 'green'
    else:
        if last_price is not None:
            # End the green segment before the 'null' price starts
            dates.append(date)
            prices.append(last_price)
            colors.append('green')
            
            # Start the red segment
            dates.append(date)
            prices.append(price)
            colors.append('red')
        
        last_price = None
        color = 'red'
    
    dates.append(date)
    prices.append(price)
    colors.append(color)

# Plotting the data with color coding
fig, ax = plt.subplots(figsize=(14, 7))

# Find the maximum price to set the upper y-limit such that the max price is at 2/3 of the y-axis height
max_price = max(filter(None, prices))  # filter out None values and find max
ax.set_ylim(0, max_price * 1.5)  # Set the upper limit to 1.5 times the max price

# Plot each segment with the appropriate color
start_idx = 0
for i in range(1, len(dates)):
    if colors[i] != colors[start_idx]:
        ax.plot(dates[start_idx:i+1], prices[start_idx:i+1], 
                linestyle='-', color=colors[start_idx], marker='o')
        start_idx = i

# Make sure to plot the last segment
ax.plot(dates[start_idx:], prices[start_idx:], 
        linestyle='-', color=colors[start_idx], marker='o')

# Date formatting
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
ax.xaxis.set_major_locator(mdates.MonthLocator())
fig.autofmt_xdate()

# Styling to match the provided image
plt.title('3 Monate Preisentwicklung')
plt.xlabel('Datum')
plt.ylabel('Preis in CHF')
plt.grid(True, which='both', linestyle='--', linewidth=0.5)
plt.tight_layout()

# Save the plot to a file
plt.savefig(fr'C:\dev\Python\Digitec\{args.productId}.png')  # Make sure to use raw string for path

# Show the plot
plt.show()

# Extract all data points
all_data_points = data['data']['priceHistory']['points']

# Filter out data points with valid prices
valid_prices = [point['amountIncl'] for point in all_data_points if point['amountIncl'] is not None]

# Calculate the average price if there are valid prices
if valid_prices:
    average_price = mean(valid_prices)

    # Identify dates where the price was at least 30% lower than the average
    dates_lower_than_average = []
    for point in all_data_points:
        if point['amountIncl'] is not None and point['amountIncl'] < 0.7 * average_price:
            dates_lower_than_average.append(datetime.strptime(point['validFrom'], "%Y-%m-%dT%H:%M:%SZ"))

    # Output dates when the price was at least 30% lower than the average
    if dates_lower_than_average:
        print("Dates when the price was at least 30% lower than the average:")
        for date in dates_lower_than_average:
            print(date.strftime("%Y-%m-%d"))
    else:
        print("No dates found where the price was at least 30% lower than the average.")
else:
    print("No valid prices available in the data.")