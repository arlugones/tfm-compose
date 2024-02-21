import asyncio
import aiohttp
import httpx

class APIClient:
    def __init__(self, url):
        self.url = url

    async def process_data(self, table_name: str):
        async with aiohttp.ClientSession() as session:
            json_table_name = {'table_name': table_name}
            async with session.get(self.url, params=json_table_name) as resp:
                response = await resp.json()
                return response
              
    async def query_api(self, table_name: str):
        tasks = []
        task = asyncio.create_task(self.process_data(table_name))
        tasks.append(task)
        responses = await asyncio.gather(*tasks)
        return responses


class HttpxAPIClient:
    def __init__(self, url):
        self.url = url

    async def process_data(self, table_name: str):
        async with httpx.AsyncClient(timeout=120) as session:
            json_table_name = {'table_name': table_name}
            response = await session.get(self.url, params=json_table_name)
            return response.json()

    async def query_api(self, table_name: str):
        tasks = []
        task = asyncio.create_task(self.process_data(table_name))
        tasks.append(task)
        responses = await asyncio.gather(*tasks)
        return responses
    
async def process_data(url: str, table_name: str):
    async with aiohttp.ClientSession() as session:
        json_table_name = {'table_name': table_name}
        async with session.get(url, params=json_table_name) as resp:
            response = await resp.json()
            return response

# async def query_api(url: str, table_name: str):
#     tasks = []
#     task = asyncio.create_task(process_data(url, table_name))
#     tasks.append(task)
#     responses = await asyncio.gather(*tasks)
#     return responses