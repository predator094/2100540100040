from fastapi import FastAPI, HTTPException
import requests
from typing import List, Dict

app = FastAPI()

# Configuration
WINDOW_SIZE = 10
TIMEOUT = 0.5  # 500 ms timeout

# In-memory storage for the rolling window of numbers
window_storage = {"p": [], "f": [], "e": [], "r": []}

# Mapping numberid to the corresponding test server API endpoint
api_urls = {
    "p": "http://20.244.56.144/test/primes",
    "f": "http://20.244.56.144/test/fibo",
    "e": "http://20.244.56.144/test/even",
    "r": "http://20.244.56.144/test/rand",
}

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJNYXBDbGFpbXMiOnsiZXhwIjoxNzI0MTY0OTIxLCJpYXQiOjE3MjQxNjQ2MjEsImlzcyI6IkFmZm9yZG1lZCIsImp0aSI6ImQwYWQyMjI5LTZjYTAtNGY2NC1hZDRiLThhMjhhYTY4OGVkMyIsInN1YiI6InByZWRhdG9yYWtraTA5MDZAYmJkbml0bS5hYy5pbiJ9LCJjb21wYW55TmFtZSI6IlByZWRhdG9yIiwiY2xpZW50SUQiOiJkMGFkMjIyOS02Y2EwLTRmNjQtYWQ0Yi04YTI4YWE2ODhlZDMiLCJjbGllbnRTZWNyZXQiOiJCTGdLV1JuWFNMclVTcG9sIiwib3duZXJOYW1lIjoiQW5zaHVsIFlhZGF2Iiwib3duZXJFbWFpbCI6InByZWRhdG9yYWtraTA5MDZAYmJkbml0bS5hYy5pbiIsInJvbGxObyI6IjIxMDA1NDAxMDAwNDAifQ.3rRhgfe9oVuaiRS8jMosbgWCunIXv4JiaYU1yjwyr9Q"


def fetch_numbers(
    api_url: str,
) -> List[int]:
    """Fetch numbers from the test server with authorization."""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(api_url, headers=headers, timeout=TIMEOUT)
        if response.status_code == 200:
            return response.json().get("numbers", [])
        return []
    except (requests.exceptions.Timeout, requests.exceptions.RequestException):
        return []


def update_window(numberid: str, new_numbers: List[int]) -> Dict[str, List[int]]:
    """Update the rolling window with new numbers."""
    global window_storage
    prev_window = window_storage[numberid].copy()

    # Add new numbers to the window, ensuring uniqueness
    unique_numbers = list(set(window_storage[numberid] + new_numbers))

    # Trim the window if it exceeds the WINDOW_SIZE
    if len(unique_numbers) > WINDOW_SIZE:
        unique_numbers = unique_numbers[-WINDOW_SIZE:]

    # Update the window storage
    window_storage[numberid] = unique_numbers
    return {"prev_window": prev_window, "curr_window": unique_numbers}


def calculate_average(numbers: List[int]) -> float:
    """Calculate the average of the numbers in the window."""
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)


@app.get("/numbers/{numberid}")
async def get_numbers(numberid: str):
    # Validate the numberid
    if numberid not in api_urls:
        raise HTTPException(status_code=400, detail="Invalid number ID")

    # Fetch numbers from the corresponding test server API
    fetched_numbers = fetch_numbers(api_urls[numberid])

    # Update the rolling window with the new numbers
    window_states = update_window(numberid, fetched_numbers)

    # Calculate the average of the current window
    avg = calculate_average(window_states["curr_window"])

    # Prepare the response
    response = {
        "numbers": fetched_numbers,
        "windowPrevState": window_states["prev_window"],
        "windowCurrState": window_states["curr_window"],
        "avg": avg,
    }

    return response
