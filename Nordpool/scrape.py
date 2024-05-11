import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
import time
import os
from fake_useragent import UserAgent
import traceback
import json
import paho.mqtt.client as mqtt

# MQTT Configurations
mqtt_broker = "broker.mqttdashboard.com"
mqtt_port = 1883
mqtt_topic = "nordpool/price"

def clean_text(text):
    """Normalize spaces and remove newline characters."""
    return re.sub(r'\s+', ' ', text.strip())

def print_table(data, headers):
    """Prints a dynamic table with headers and rows with proper alignment."""
    col_widths = [max(len(clean_text(str(row[i]))) for row in data + [headers]) for i in range(len(headers))]
    horizontal_line = '+' + '+'.join(['-' * (width + 2) for width in col_widths]) + '+'
    
    print(horizontal_line)
    header_row = '|' + '|'.join(f" {headers[i].center(col_widths[i])} " for i in range(len(headers))) + '|'
    print(header_row)
    print(horizontal_line)
    
    for row in data:
        cleaned_row = [clean_text(str(item)) for item in row]
        row_string = '|' + '|'.join(f" {cleaned_row[i].ljust(col_widths[i])} " for i in range(len(row))) + '|'
        print(row_string)
    print(horizontal_line)

# Configure WebDriver
chrome_options = Options()
chrome_options.headless = True
ua = UserAgent()
chrome_options.add_argument(f"user-agent={ua.random}")
chromedriver_path = "C:\\Users\\meila\\Downloads\\chromedriver.exe"
driver = webdriver.Chrome(executable_path=chromedriver_path, options=chrome_options)

# MQTT Client Setup
client = mqtt.Client()
client.connect(mqtt_broker, mqtt_port)

# Target URL
url = "https://data.nordpoolgroup.com/auction/day-ahead/prices?deliveryDate=latest&currency=EUR&aggregation=Hourly&deliveryAreas=LT,AT"
driver.get(url)

try:
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.dx-datagrid")))

    time_periods = [f"{i:02d}:00 - {i+1:02d}:00" for i in range(24)]
    time_periods[-1] = "23:00 - 00:00"  # Correct the last period manually

    while True:
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.dx-datagrid-rowsview")))
        data_rows = driver.find_elements(By.CSS_SELECTOR, "tr.dx-data-row")
        data_to_display = []
        
        for i, row in enumerate(data_rows):
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 3:
                price_lt = cells[1].text.strip() if len(cells) > 1 else "N/A"
                price_at = cells[2].text.strip() if len(cells) > 2 else "N/A"
                time_period = time_periods[i % 24]
                data_to_display.append((time_period, price_lt, price_at))

        # Fetch Min, Max, Average values dynamically for Price LT
        footer_cells_lt = driver.find_elements(By.CSS_SELECTOR, "tr.dx-footer-row td[aria-colindex='2'] div.dx-datagrid-summary-item.dx-datagrid-text-content")
        min_value_lt = footer_cells_lt[0].text.strip() if len(footer_cells_lt) > 0 else "N/A"
        max_value_lt = footer_cells_lt[1].text.strip() if len(footer_cells_lt) > 1 else "N/A"
        average_value_lt = footer_cells_lt[2].text.strip() if len(footer_cells_lt) > 2 else "N/A"

        # Fetch Min, Max, Average values dynamically for Price AT
        footer_cells_at = driver.find_elements(By.CSS_SELECTOR, "tr.dx-footer-row td[aria-colindex='3'] div.dx-datagrid-summary-item.dx-datagrid-text-content")
        min_value_at = footer_cells_at[0].text.strip() if len(footer_cells_at) > 0 else "N/A"
        max_value_at = footer_cells_at[1].text.strip() if len(footer_cells_at) > 1 else "N/A"
        average_value_at = footer_cells_at[2].text.strip() if len(footer_cells_at) > 2 else "N/A"
        
        # Append summary data for both Price LT and Price AT
        data_to_display.append(("Summary:", "LT (EUR)", "AT (EUR)"))
        data_to_display.append(("Min:", min_value_lt, min_value_at))
        data_to_display.append(("Max:", max_value_lt, max_value_at))
        data_to_display.append(("Average:", average_value_lt, average_value_at))

        # Publish data to MQTT broker
        payload = json.dumps(data_to_display)
        client.publish(mqtt_topic, payload)

        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"Data Refreshed (Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}):")
        print_table(data_to_display, ["Time Period", "Price LT (EUR)", "Price AT (EUR)"])

        time.sleep(60)  # Refresh every minute
        driver.refresh()

except Exception as e:
    print("An error occurred:")
    traceback.print_exc()
finally:
    driver.quit()
    client.disconnect()
