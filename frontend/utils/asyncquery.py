import asyncio
import aiohttp
import pandas as pd

class APIClient:
    def __init__(self, url):
        self.url = url

    async def process_data(self, table_name: str):
        async with aiohttp.ClientSession() as session:
            json_table_name = {'table_name': table_name}
            async with session.post(self.url, json=json_table_name) as resp:
                response = await resp.json()
                return response
              
    async def query_api(self, table_name: str):
        tasks = []
        task = asyncio.create_task(self.process_data(table_name))
        tasks.append(task)
        responses = await asyncio.gather(*tasks)
        return responses
