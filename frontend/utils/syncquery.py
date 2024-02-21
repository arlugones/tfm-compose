import httpx

def process_data(url: str, table_name: str):
    with httpx.Client(timeout=None) as client:
        json_table_name = {'table_name': table_name}
        resp = client.get(url, params=json_table_name)
        response = resp.json()
        return response