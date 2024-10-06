import aiohttp
import asyncio
import time
import statistics
from fastapi import FastAPI
from utils.getToken import getToken
from utils.auth import username, password

app = FastAPI()

async def stress_test(q, token, max_concurrent_users, ramp_up_time, test_duration):
    gqlurl = "http://localhost:33001/api/gql"

    async def make_request():
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

    async def user_session():
        while True:
            yield await make_request()

    async def run_stress_test():
        start_time = time.time()
        results = []
        active_users = 0
        user_sessions = set()  # Changed to a set for managing tasks

        while time.time() - start_time < test_duration:
            current_time = time.time() - start_time
            target_users = min(int(max_concurrent_users * (current_time / ramp_up_time)), max_concurrent_users)

            while active_users < target_users:
                task = asyncio.create_task(user_session().__anext__())  # Create a task for user session
                user_sessions.add(task)  # Add to the set
                active_users += 1

            if user_sessions:
                done, pending = await asyncio.wait(user_sessions, timeout=1, return_when=asyncio.FIRST_COMPLETED)
                results.extend([t.result() for t in done if t.result()[0] is not None])
                user_sessions = pending  # Update pending tasks
                active_users -= len(done)

        # Cancel any remaining user sessions
        for session in user_sessions:
            session.cancel()

        return results

    results = await run_stress_test()
    
    success_count = sum(1 for status, _ in results if status == 200)
    failure_count = len(results) - success_count
    
    response_times = [t for _, t in results]
    avg_response_time = statistics.mean(response_times)
    min_response_time = min(response_times)
    max_response_time = max(response_times)
    median_response_time = statistics.median(response_times)
    
    result_summary = {
        "total_requests": len(results),
        "successful_requests": success_count,
        "failed_requests": failure_count,
        "success_rate": f"{success_count/len(results)*100:.2f}%",
        "average_response_time": f"{avg_response_time:.3f} seconds",
        "minimum_response_time": f"{min_response_time:.3f} seconds",
        "maximum_response_time": f"{max_response_time:.3f} seconds",
        "median_response_time": f"{median_response_time:.3f} seconds"
    }

    print(f"Stress Test Results: {result_summary}")

    return result_summary


# Stress Test Function
async def stress_test_2(q, token, initial_requests, step_size, max_limit):
    gqlurl = "http://localhost:33001/api/gql"
    
    # Simulate a single request
    async def send_request(session):
        payload = {"query": q, "variables": {}}
        cookies = {'authorization': token}
        try:
            start_time = time.time()
            async with session.post(gqlurl, json=payload, cookies=cookies) as resp:
                end_time = time.time()
                return resp.status, end_time - start_time
        except Exception as e:
            print(f"Request error: {e}")
            return None, 0

    # Simulate load increase in steps
    async def run_stress_load(current_load):
        connector = aiohttp.TCPConnector(limit=current_load)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [send_request(session) for _ in range(current_load)]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
        return responses

    current_load = initial_requests
    all_results = []
    
    # Keep increasing the load until max_limit is reached or the system fails
    while current_load <= max_limit:
        print(f"Testing with {current_load} concurrent requests...")
        responses = await run_stress_load(current_load)
        
        # Collect response data
        response_statuses = [status for status, _ in responses if status]
        failed_requests = len([status for status in response_statuses if status != 200])
        success_rate = (len(response_statuses) - failed_requests) / len(response_statuses) * 100 if response_statuses else 0
        
        # Print basic stats
        if responses:
            response_times = [time for _, time in responses if time > 0]
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

        # Break if failure rate crosses threshold (e.g., 50% failed requests)
        if failed_requests / current_load > 0.5:
            print("More than 50% of requests failed. Stopping test.")
            break

        # Increase load
        current_load += step_size
        await asyncio.sleep(1)  # Add a delay to simulate real-world increase in load

    return all_results