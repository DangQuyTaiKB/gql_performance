﻿import asyncio
import time
import statistics
import aiohttp
from concurrent.futures import ProcessPoolExecutor


# Concurrent stress test with optimized request handling
async def stress_test_concurrent(q, token, url, initial_load, step_size, max_limit, recovery_steps):
    async def run_concurrent_load(current_load):
        semaphore = asyncio.Semaphore(current_load)
        async with aiohttp.ClientSession() as session:
            tasks = [make_request_with_semaphore(session, q, token, url, semaphore) for _ in range(current_load)]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
        return responses

    current_load = initial_load
    all_results = []

    # Increase load until the system fails
    while current_load <= max_limit:
        print(f"Testing with {current_load} concurrent requests...")
        responses = await run_concurrent_load(current_load)

        # Analyze the results
        response_statuses = [status for status, _ in responses if status]
        failed_requests = len([status for status in response_statuses if status != 200])
        success_rate = (len(response_statuses) - failed_requests) / len(response_statuses) * 100 if response_statuses else 0

        # Log detailed results
        if responses:
            response_times = [resp_time for _, resp_time in responses if resp_time > 0]
            avg_time = statistics.mean(response_times) if response_times else float('inf')
            min_time = min(response_times) if response_times else float('inf')
            max_time = max(response_times) if response_times else float('inf')

            print(f"Load: {current_load}, Success Rate: {success_rate:.2f}%, Avg Time: {avg_time:.3f}s")
            print(f"Min Time: {min_time:.3f}s, Max Time: {max_time:.3f}s")

            all_results.append({
                "load": current_load,
                "success_rate": success_rate,
                "avg_time": avg_time,
                "min_time": min_time,
                "max_time": max_time,
                "failed_requests": failed_requests
            })

        if failed_requests / current_load > 0.5:
            print("More than 50% of requests failed. Stopping test.")
            break

        # Increase load
        current_load += step_size
        await asyncio.sleep(1)

    # Recovery phase
    while current_load > initial_load:
        current_load -= recovery_steps
        print(f"Testing recovery with {current_load} concurrent requests...")
        responses = await run_concurrent_load(current_load)
        # Log recovery results similarly
        await asyncio.sleep(1)

    return all_results


# Parallel stress test using ProcessPoolExecutor
def run_stress_load_sync(q, token, url, current_load):
    return asyncio.run(run_concurrent_load(q, token, url, current_load))


async def enhanced_stress_test_parallel(q, token, url, initial_load, step_size, max_limit, recovery_steps):
    current_load = initial_load
    all_results = []

    with ProcessPoolExecutor() as executor:
        while current_load <= max_limit:
            print(f"Testing with {current_load} concurrent requests (Parallel)...")
            loop = asyncio.get_event_loop()
            responses = await loop.run_in_executor(executor, run_stress_load_sync, q, token, url, current_load)

            response_statuses = [status for status, _ in responses if status]
            failed_requests = len([status for status in response_statuses if status != 200])
            success_rate = (len(response_statuses) - failed_requests) / len(response_statuses) * 100 if response_statuses else 0

            # Log detailed results
            if responses:
                response_times = [resp_time for _, resp_time in responses if resp_time > 0]
                avg_time = statistics.mean(response_times) if response_times else float('inf')
                min_time = min(response_times) if response_times else float('inf')
                max_time = max(response_times) if response_times else float('inf')

                print(f"Load: {current_load}, Success Rate: {success_rate:.2f}%, Avg Time: {avg_time:.3f}s")
                print(f"Min Time: {min_time:.3f}s, Max Time: {max_time:.3f}s")

                all_results.append({
                    "load": current_load,
                    "success_rate": success_rate,
                    "avg_time": avg_time,
                    "min_time": min_time,
                    "max_time": max_time,
                    "failed_requests": failed_requests
                })

            if failed_requests / current_load > 0.5:
                print("More than 50% of requests failed. Stopping test.")
                break

            current_load += step_size
            await asyncio.sleep(1)

        # Recovery phase
        while current_load > initial_load:
            current_load -= recovery_steps
            print(f"Testing recovery with {current_load} parallel requests...")
            responses = await loop.run_in_executor(executor, run_stress_load_sync, q, token, url, current_load)
            # Log recovery results similarly
            await asyncio.sleep(1)

    return all_results


# Utility function to make requests
async def make_request(session, q, token, url):
    payload = {"query": q, "variables": {}}
    cookies = {'authorization': token}
    try:
        start_time = time.time()
        async with session.post(url, json=payload, cookies=cookies) as resp:
            end_time = time.time()
            return resp.status, end_time - start_time
    except Exception as e:
        print(f"Request error: {e}")
        return None, 0


# Helper function with semaphore to control concurrent requests
async def make_request_with_semaphore(session, q, token, url, semaphore):
    async with semaphore:
        return await make_request(session, q, token, url)


# Function to run load test with concurrency
async def run_concurrent_load(q, token, url, current_load):
    semaphore = asyncio.Semaphore(current_load)
    async with aiohttp.ClientSession() as session:
        tasks = [make_request_with_semaphore(session, q, token, url, semaphore) for _ in range(current_load)]
        return await asyncio.gather(*tasks)
