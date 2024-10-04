import asyncio
import aiohttp
from aiohttp import ClientSession, TCPConnector

async def load_test(q, token, num_requests, concurrent_limit):
    async def single_request(session):
        gqlurl = "http://localhost:33001/api/gql"
        payload = {"query": q, "variables": {}}
        cookies = {'authorization': token}
        
        async with session.post(gqlurl, json=payload, cookies=cookies) as resp:
            if resp.status != 200:
                return await resp.text()
            return await resp.json()

    async def run_requests():
        connector = TCPConnector(limit=concurrent_limit)
        async with ClientSession(connector=connector) as session:
            tasks = [single_request(session) for _ in range(num_requests)]
            return await asyncio.gather(*tasks)

    results = await run_requests()
    
    success_count = sum(1 for r in results if isinstance(r, dict) and 'data' in r)
    failure_count = num_requests - success_count
    
    print(f"Load Test Results:")
    print(f"Total Requests: {num_requests}")
    print(f"Successful Requests: {success_count}")
    print(f"Failed Requests: {failure_count}")
    print(f"Success Rate: {success_count/num_requests*100:.2f}%")

    return results


import time
import statistics

async def load_test_1(q, token, num_requests, concurrent_limit):
    async def single_request(session):
        gqlurl = "http://localhost:33001/api/gql"
        payload = {"query": q, "variables": {}}
        cookies = {'authorization': token}
        
        start_time = time.time()
        async with session.post(gqlurl, json=payload, cookies=cookies) as resp:
            if resp.status != 200:
                response = await resp.text()
            else:
                response = await resp.json()
        end_time = time.time()
        
        return response, end_time - start_time

    async def run_requests():
        connector = TCPConnector(limit=concurrent_limit)
        async with ClientSession(connector=connector) as session:
            tasks = [single_request(session) for _ in range(num_requests)]
            return await asyncio.gather(*tasks)

    results = await run_requests()
    
    success_count = sum(1 for r, _ in results if isinstance(r, dict) and 'data' in r)
    failure_count = num_requests - success_count
    
    response_times = [t for _, t in results]
    avg_response_time = statistics.mean(response_times)
    min_response_time = min(response_times)
    max_response_time = max(response_times)
    median_response_time = statistics.median(response_times)
    
    print(f"Load Test Results:")
    print(f"Total Requests: {num_requests}")
    print(f"Successful Requests: {success_count}")
    print(f"Failed Requests: {failure_count}")
    print(f"Success Rate: {success_count/num_requests*100:.2f}%")
    print(f"Average Response Time: {avg_response_time:.3f} seconds")
    print(f"Minimum Response Time: {min_response_time:.3f} seconds")
    print(f"Maximum Response Time: {max_response_time:.3f} seconds")
    print(f"Median Response Time: {median_response_time:.3f} seconds")

    return results, response_times, avg_response_time, min_response_time, max_response_time, median_response_time, success_count, failure_count


import aiohttp
import asyncio
import time
import statistics

async def load_test_2(q, token, num_requests, concurrent_limit):
    gqlurl = "http://localhost:33001/api/gql"

    # Function to simulate a single request
    async def runTest():
        payload = {"query": q, "variables": {}}
        cookies = {'authorization': token}
        async with aiohttp.ClientSession() as session:
            try:
                start_time = time.time()
                async with session.post(gqlurl, json=payload, cookies=cookies) as resp:
                    end_time = time.time()
                    return resp.status, end_time - start_time
            except Exception as e:
                print(f"Request error: {e}")
                return None, 0

    # Function to simulate one user sending multiple requests
    async def runSingleModelUser():
        awaitables = [runTest() for _ in range(num_requests)]
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
    return results
