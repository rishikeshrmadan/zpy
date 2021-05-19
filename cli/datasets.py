from cli.utils import download_url, fetch_auth, parse_filter
from zpy.files import to_pathlib_path
import json
import requests


@fetch_auth
def create_dataset(name, files, url, auth_headers):
    """create dataset

    Create dataset on ZumoLabs backend which groups files.

    Args:
        name (str): name of dataset
        files (list): list of file obj to associate with dataset
        url (str): backend endpoint
        auth_headers: authentication for backend
    """
    endpoint = f"{url}/api/v1/datasets/"
    data = {"name": name, "files": files}
    r = requests.post(
        endpoint,
        data=data,
        headers=auth_headers,
    )
    if r.status_code != 201:
        r.raise_for_status()


@fetch_auth
def generate_dataset(dataset_name, sim_name, count, config, url, auth_headers):
    """generate dataset

    Generate files for a dataset on ZumoLabs backend which will launch
    a generation job with specified params.

    Args:
        dataset_name (str): name of dataset
        sim_name (str): name of sim to generate from
        count (int): number of times to run the sim
        config (dict): configration of sim for this dataset
        url (str): backend endpoint
        auth_headers: authentication for backend
    """
    from cli.sims import fetch_sim

    dataset = fetch_dataset(dataset_name)
    fetch_sim(sim_name)
    endpoint = f"{url}/api/v1/datasets/{dataset['id']}/generate/"
    data = {"sim": sim_name, "amount": count, "config": json.dumps(config)}
    r = requests.post(
        endpoint,
        data=data,
        headers=auth_headers,
    )
    if r.status_code != 200:
        r.raise_for_status()


@fetch_auth
def download_dataset(name, path, format, url, auth_headers):
    """download dataset

    Download dataset object from S3 through ZumoLabs backend.

    Args:
        name (str): name of dataset to download
        path (str): output directory
        format (str): type of packaged version to download
        url (str): backend endpoint
        auth_headers: authentication for backend

    Returns:
        str: output file path
    """
    dataset = fetch_dataset(name)
    endpoint = f"{url}/api/v1/datasets/{dataset['id']}/download/"
    r = requests.get(endpoint, params={"format": format}, headers=auth_headers)
    if r.status_code != 200:
        r.raise_for_status()
    response = json.loads(r.text)
    name_slug = f"{dataset['name'].replace(' ', '_')}-{dataset['id'][:8]}.zip"
    output_path = to_pathlib_path(path) / name_slug
    download_url(response["redirect_link"], output_path)
    return output_path


@fetch_auth
def fetch_datasets(url, auth_headers):
    """fetch datasets

    Fetch dataset names from backend. This is done through tags.

    Returns:
        list: paginated sorted datasets for all types
    """
    endpoint = f"{url}/api/v1/datasets/"
    r = requests.get(endpoint, headers=auth_headers)
    if r.status_code != 200:
        r.raise_for_status()
    return json.loads(r.text)["results"]


@fetch_auth
def fetch_dataset(name, url, auth_headers):
    """fetch dataset

    Fetch info on a dataset by name from backend.

    Args:
        name (str): name of dataset
        url (str): backend endpoint
        auth_headers: authentication for backend
    """
    endpoint = f"{url}/api/v1/datasets/"
    r = requests.get(endpoint, params={"name": name}, headers=auth_headers)
    if r.status_code != 200:
        r.raise_for_status()
    response = json.loads(r.text)
    if response["count"] != 1:
        raise NameError(f"found {response['count']} datasets for name {name}")
    return response["results"][0]


@fetch_auth
def filter_datasets(dfilter, url, auth_headers):
    """filter datasets

    Filter dataset objects on ZumoLabs backend by given dfilter.
    Parse dfilter using parse_filter.

    Args:
        dfilter (str): filter query for datasets
        url (str): backend endpoint
        auth_headers: authentication for backend

    Return:
        dict: filtered datasets by dfilter {'name': 'id'}
    """
    filtered_datasets = {}
    field, pattern, regex = parse_filter(dfilter)
    endpoint = f"{url}/api/v1/datasets/?{field}__{pattern}={regex}"
    while endpoint is not None:
        r = requests.get(endpoint, headers=auth_headers)
        if r.status_code != 200:
            r.raise_for_status()
        response = json.loads(r.text)
        for r in response["results"]:
            filtered_datasets[r["name"]] = r["id"]
        endpoint = response["next"]
    return filtered_datasets
