import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests


api_url = os.getenv("API_URL", "http://localhost:8080")


def send_request(number):
    url = f"{api_url}/estimate_pi"
    data = {"total_points": 10000000}

    try:
        response = requests.post(url, json=data, timeout=30)
        return number, response.status_code, response.text
    except Exception as e:
        return number, "ERROR", str(e)


def main():
    accepted = 0

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(send_request, i + 1) for i in range(50)]

        for future in as_completed(futures):
            number, status, text = future.result()
            print(f"Request {number}: {status}")

            if status == 202:
                accepted += 1
            else:
                print(text)

    print(f"\nAccepted: {accepted}/50")


if __name__ == "__main__":
    main()
