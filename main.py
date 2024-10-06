from fastapi import FastAPI
import json
import pandas as pd
import aiohttp
app = FastAPI()


############ Intro FastAPI ################

@app.get("/")
async def root():
    return {"message": "Hello World"}

def outfile(data, filename):
    with open(filename + '.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)



############ FastAPI ################


from utils.send_payload import query
from utils.getToken import getToken
from utils.auth import username, password
from utils.load_test import load_test, load_test_1, load_test_2
from utils.stress_test import stress_test, stress_test_2
from query.userPage import queryStr_0, queryStr


@app.get("/query")
async def fullPipe():

    token = await getToken(username, password)
    qfunc = query(queryStr, token)
    response = await qfunc({})
    outfile(response, 'response')
    return response




@app.get("/loadTest")
async def loadTest():
    token = await getToken(username, password)
    num_requests = 1000  # You can adjust this number
    concurrent_limit = 100  # You can adjust this number
    
    results = await load_test(queryStr_0, token, num_requests, concurrent_limit)
    
    # Process the results if needed
    successful_requests = [r for r in results if isinstance(r, dict) and 'data' in r]
    
    # You might want to return a summary instead of all results
    return {
        "total_requests": num_requests,
        "successful_requests": len(successful_requests),
        "failed_requests": num_requests - len(successful_requests)
    }


@app.get("/loadTest_time")
async def loadTest1():
    token = await getToken(username, password)
    num_requests = 100  # Total number of requests that you want to send to the server in the load test - total workload
    concurrent_limit = 5  # total of TCP connections that you want to open at the same time from the client to the server
    
    # results, response_times = await load_test_1(queryStr_0, token, num_requests, concurrent_limit)
    results, response_times, avg_response_time, min_response_time, max_response_time, median_response_time, successful_requests, failure_count = await load_test_1(queryStr_0, token, num_requests, concurrent_limit)
    dict_response_times = {}
    for i in range(len(response_times)):
        dict_response_times[i] = response_times[i]

    outfile(results, 'response')
    return {
        "total_requests": num_requests,
        "successful_requests": successful_requests,
        "failed_requests": failure_count,
        "average_response_time": avg_response_time,
        "min_response_time": min_response_time,
        "max_response_time": max_response_time,
        "median_response_time": median_response_time,
        "response_times": dict_response_times
    }

@app.get("/loadTest_time_2")
async def loadTest2():
    try:
        # Step 1: Get the token
        token = await getToken(username, password)
        if not token:
            return {"error": "Failed to retrieve token"}

        # Step 2: Define the number of requests and concurrency limit
        num_requests = 20
        concurrent_limit = 5

        # Step 3: Run the load test
        results = await load_test_2(queryStr_0, token, num_requests, concurrent_limit)

        # Step 4: Check and format the results
        success_count = sum(1 for status, _ in results if status == 200)
        total_requests = len(results)
        avg_time = round(sum(duration for _, duration in results) / total_requests, 3) if total_requests > 0 else 0

        dict_response_times = {}
        for i in range(len(results)):
            dict_response_times[i] = results[i][1]

        # Step 5: Return the results in a structured format
        return {
            "status": "success",
            "total_requests": total_requests,
            "successful_requests": success_count,
            "failed_requests": total_requests - success_count,
            "success_rate": f"{(success_count / total_requests * 100):.2f}%",
            "average_response_time": f"{avg_time:.3f} seconds",
            "response_times": dict_response_times
        }

    except Exception as e:
        # Handle unexpected errors
        print(f"Error in loadTest2: {e}")
        return {"error": "An error occurred during load testing"}


@app.get("/stress_test")
async def run_stress_test_api():
    token = await getToken(username, password)
    query = "{userPage{id name surname email}}"
    max_concurrent_users = 100
    ramp_up_time = 2  # seconds
    test_duration = 30  # seconds

    result = await stress_test(query, token, max_concurrent_users, ramp_up_time, test_duration)
    return result


@app.get("/stress_test_2")
async def stress_test_endpoint():
    token = await getToken(username, password)  # Assuming getToken is implemented elsewhere
    query = "{userPage{id name surname email}}"  # Your GraphQL query
    initial_requests = 50  # Starting with 50 concurrent requests
    step_size = 50  # Increase by 50 requests each step
    max_limit = 200  # Stop at requests
    
    # Run the stress test
    results = await stress_test_2(query, token, initial_requests, step_size, max_limit)
    
    print("\nFinal Stress Test Results:")
    for result in results:
        print(result)

    return {"results": results}

