import asyncio
import aiohttp
from aiohttp import ClientSession, TCPConnector
import time
import statistics
import concurrent.futures
import os

def dict_all_results(results, response_times, success_count, failure_count):
    avg_response_time = statistics.mean(response_times)
    min_response_time = min(response_times)
    max_response_time = max(response_times)
    median_response_time = statistics.median(response_times)
    return {
        "results": results,
        "response_times": response_times,
        "avg_response_time": avg_response_time,
        "min_response_time": min_response_time,
        "max_response_time": max_response_time,
        "median_response_time": median_response_time,
        "success_count": success_count,
        "failure_count": failure_count
    }

def print_dict(dict_all):
    print(f"Total Requests: {dict_all['num_requests']}")
    print(f"Successful Requests: {dict_all['success_count']}")
    print(f"Failed Requests: {dict_all['failure_count']}")
    print(f"Success Rate: {dict_all['success_count']/dict_all['num_requests']*100:.2f}%")
    print(f"Average Response Time: {dict_all['avg_response_time']:.3f} seconds")
    print(f"Minimum Response Time: {dict_all['min_response_time']:.3f} seconds")
    print(f"Maximum Response Time: {dict_all['max_response_time']:.3f} seconds")
    print(f"Median Response Time: {dict_all['median_response_time']:.3f} seconds")
    


async def load_test_concurrent_1(q, token, num_requests, concurrent_limit, url):
    async def single_request(session):
        payload = {"query": q, "variables": {}}
        cookies = {'authorization': token}
        
        start_time = time.time()
        try:
            async with session.post(url, json=payload, cookies=cookies) as resp:
                if resp.status != 200:
                    response = await resp.text()
                else:
                    response = await resp.json()
        except Exception as e:
            print(f"Request error: {e}")
            return None, 0
        end_time = time.time()
        
        return response, end_time - start_time

    async def run_requests():
        connector = TCPConnector(limit=concurrent_limit)
        async with ClientSession(connector=connector) as session:
            tasks = [single_request(session) for _ in range(num_requests)]
            return await asyncio.gather(*tasks)

    results = await run_requests()
    
    # Calculate statistics
    success_count = sum(1 for r, _ in results if isinstance(r, dict) and 'data' in r)
    failure_count = num_requests - success_count
    
    response_times = [t for _, t in results]
    dict_all = dict_all_results(results, response_times, success_count, failure_count)
    dict_all.update({"num_requests": num_requests})
    print_dict(dict_all)
    return dict_all


async def load_test_concurrent_2(q, token, requests_per_user, concurrent_limit, url):
 
    # Function to simulate a single request
    async def runTest():
        payload = {"query": q, "variables": {}}
        cookies = {'authorization': token}
        async with aiohttp.ClientSession() as session:
            try:
                start_time = time.time()
                async with session.post(url, json=payload, cookies=cookies) as resp:
                    end_time = time.time()
                    return resp.status, end_time - start_time
            except Exception as e:
                print(f"Request error: {e}")
                return None, 0

    # Function to simulate one user sending multiple requests
    async def runSingleModelUser():
        awaitables = [runTest() for _ in range(requests_per_user)]
        responses = await asyncio.gather(*awaitables, return_exceptions=True)
        results = [(status, duration) for status, duration in responses if status is not None]
        return results

    # Function to simulate multiple users concurrently
    async def run_high_load_test():
        user_tasks = [runSingleModelUser() for _ in range(concurrent_limit)]
        all_results = await asyncio.gather(*user_tasks, return_exceptions=True)
        all_results_flattened = [result for user_result in all_results for result in user_result]
        return all_results_flattened

    # Start the load test and return the results
    results = await run_high_load_test()
    num_requests = len(results)
    # Calculate statistics
    success_count = sum(1 for status, _ in results if status == 200)
    failure_count = len(results) - success_count

    response_times = [t for _, t in results]
    dict_all = dict_all_results(results, response_times, success_count, failure_count)
    dict_all.update({"num_requests": num_requests})
    print_dict(dict_all)
    return dict_all

async def load_test_parallel(url, payload, token, num_requests, num_workers):
    async def send_request(session, url, payload, token):
        try:
            start_time = time.time()
            cookies = {'authorization': token}
            async with session.post(url, json=payload, cookies=cookies) as response:
                end_time = time.time()
                if response.status != 200:
                    print(f"Request failed with status {response.status}")
                return response.status, end_time - start_time
        except Exception as e:
            print(f"Request error: {e}")
            return None, 0

    async def run_requests(url, payload, token, num_requests):
        async with aiohttp.ClientSession() as session:
            tasks = [send_request(session, url, payload, token) for _ in range(num_requests)]
            return await asyncio.gather(*tasks)

    # Use ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        loop = asyncio.get_event_loop()
        futures = [
            loop.run_in_executor(
                executor, 
                lambda: asyncio.run(run_requests(url, payload, token, num_requests // num_workers))
            ) for _ in range(num_workers)
        ]
        results = await asyncio.gather(*futures)

    # Flatten the results
    flatten_results = [item for sublist in results for item in sublist]
    
    success_count = sum(1 for status, _ in flatten_results if status == 200)
    failure_count = num_requests - success_count
    response_times = [t for _, t in flatten_results]
    dict_all = dict_all_results(flatten_results, response_times, success_count, failure_count)
    dict_all.update({"num_requests": num_requests})
    print_dict(dict_all)
    return dict_all



