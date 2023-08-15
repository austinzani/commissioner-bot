import requests
import json
import os
import time
from typing import Tuple

discord_webhook_url = os.environ['DISCORD_WEBHOOK_URL']

headers = {
    'Content-Type': 'application/json',
}


def send_request_with_retries(url, method='GET', max_retries=3, retry_delay=1, json_body=None, headers=headers, **kwargs) -> Tuple[bool, dict or None]:
    """
    Send an HTTP request with built-in error handling and retry mechanism.

    Args:
        url (str): The URL to send the request to.
        method (str): The HTTP method to use (default is 'GET').
        max_retries (int): The maximum number of retries (default is 3).
        retry_delay (int): The delay between retries in seconds (default is 1).
        json_body (dict): The JSON body to send with the request (default is None).
        headers (dict): The headers to send with the request (default is headers).
        **kwargs: Additional keyword arguments to pass to the request library.

    Returns:
        requests.Response: The response object from the HTTP request.
    """
    for retry in range(max_retries + 1):
        try:
            if json_body:
                kwargs['data'] = json.dumps(json_body)
            if headers:
                kwargs['headers'] = headers
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()  # Raise an exception for 4xx and 5xx status codes
            return True, response.json() if response.text else None
        except requests.exceptions.RequestException as e:
            print(f"Request failed (attempt {retry + 1}/{max_retries + 1}): {e}")
            if retry < max_retries:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("Max retries reached. Giving up.")
                return False, None
