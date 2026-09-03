import os
import requests


API_BASE_URL = os.getenv(
    "DEBRIX_API_URL",
    "http://127.0.0.1:5000"
)


def get_objects():
    response = requests.get(
        f"{API_BASE_URL}/objects",
        timeout=10,
    )

    response.raise_for_status()

    return response.json()


def get_conjunctions():
    response = requests.get(
        f"{API_BASE_URL}/conjunctions",
        timeout=10,
    )

    response.raise_for_status()

    return response.json()


def get_conjunction(conjunction_id):
    response = requests.get(
        f"{API_BASE_URL}/conjunctions/{conjunction_id}",
        timeout=10,
    )

    response.raise_for_status()

    return response.json()


def get_alerts():
    response = requests.get(
        f"{API_BASE_URL}/alerts",
        timeout=10,
    )

    response.raise_for_status()

    return response.json()


def get_propagation(object_id):
    response = requests.get(
        f"{API_BASE_URL}/objects/{object_id}/propagation",
        timeout=10,
    )

    response.raise_for_status()

    return response.json()


def get_trajectory(
    object_id,
    start=None,
    end=None,
    steps=150,
):
    """
    Request a real SGP4 trajectory from the backend.
    """

    params = {
        "steps": steps,
    }

    if start is not None:
        params["start"] = start

    if end is not None:
        params["end"] = end

    response = requests.get(
        f"{API_BASE_URL}/objects/{object_id}/trajectory",
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()