from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import json
import os
import asyncio
from utils.send_payload import query
from utils.getToken import getToken
from utils.auth import username, password
from utils.load_test import load_test_1, load_test_2, parallel_load_test
from utils.stress_test import stress_test_concurrent, enhanced_stress_test_parallel
from query.userPage import queryStr_0, queryStr
import subprocess

app = FastAPI()
gqlurl = os.getenv("GQL_PROXY", "http://localhost:33001/api/gql")

############ Intro FastAPI ################

@app.get("/")
async def root():
    return {"message": "Hello World"}

def outfile(data, filename):
    with open(filename + '.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

############ FastAPI ################

@app.get("/query")
async def fullPipe():
    token = await getToken(username, password)
    qfunc = query(queryStr, token)
    response = await qfunc({})
    outfile(response, 'response')
    return response

############# Load Test ###############

@app.get("/loadTest_time")
async def loadTest1():
    token = await getToken(username, password)
    num_requests = 100
    concurrent_limit = 5
    # gqlurl = os.getenv("GQL_PROXY", "http://localhost:33001/api/gql")

    results = await load_test_1(queryStr_0, token, num_requests, concurrent_limit, gqlurl)
    outfile(results['results'], 'response')
    time_result = {key: value for key, value in results.items() if key != "results"}  #dictionary comprehension
    return time_result


@app.get("/loadTest_time_2")
async def loadTest2():
    token = await getToken(username, password)
    requests_per_user = 20 # number of requests per user
    concurrent_limit = 5 # number of users concurrently
    # gqlurl = os.getenv("GQL_PROXY", "http://localhost:33001/api/gql")

    results = await load_test_2(queryStr_0, token, requests_per_user, concurrent_limit, gqlurl)
    time_result = {key: value for key, value in results.items() if key != "results"}
    return time_result

@app.get("/parallel_load_test")
async def parallelLoadTest():
    token = await getToken(username, password)
    num_requests = 100
    num_workers = 10
    gqlurl = os.getenv("GQL_PROXY", "http://localhost:33001/api/gql")
    payload = {"query": queryStr_0, "variables": {}}

    # Call the updated parallel_load_test function
    results = await parallel_load_test(gqlurl, payload, token, num_requests, num_workers)
    
    # Exclude the "results" key from the returned dictionary
    time_result = {key: value for key, value in results.items() if key != "results"}
    time_result.update({"num_workers": num_workers})
    return time_result


############# Stress Test ###############

@app.get("/stress_test_1")
async def stress_test_1_endpoint():
    # Get the token
    token = await getToken(username, password) 
    
    # Query to be used in the stress test
    query = queryStr_0

    # Define test parameters
    initial_requests = 50  # Starting with 50 concurrent requests
    step_size = 10         # Increase by 50 requests each step
    max_limit = 200        # Stop at 200 requests
    recovery_steps = 10     # Decrease by 50 during recovery

    # Run the stress test
    results = await stress_test_concurrent(query, token, gqlurl, initial_requests, step_size, max_limit, recovery_steps)
    return {"results": results}

@app.get("/enhanced_stress_test")
async def enhanced_stress_test_endpoint():
    # Get the token
    token = await getToken(username, password)
    
    # Query to be used in the stress test
    query = queryStr_0

    # Define test parameters
    initial_load = 10         # Starting with 10 concurrent requests
    step_size = 10            # Increase load by 10 each step
    max_limit = 100           # Maximum of 100 concurrent requests
    recovery_steps = 5        # Decrease by 5 during recovery
    # Run the enhanced stress test
    results = await enhanced_stress_test_parallel(query, token, gqlurl, initial_load, step_size, max_limit, recovery_steps)
    return {"results": results}


############# Locust Test ###############

@app.get("/run_locust")
async def run_locust_test():
    try:
        process = subprocess.Popen(
            ["locust", "-f", "locust_concurrent.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        locust_version = ""
        web_interface_url = ""
        for line in process.stdout:
            if "Starting Locust" in line:
                locust_version = line.split("Starting Locust")[1].strip()
            elif "Starting web interface at" in line:
                web_interface_url = line.split("Starting web interface at")[1].split("(")[0].strip()
                break

        if locust_version and web_interface_url:
            html_content = f"""
            <p>Locust version: {locust_version}</p>
            <p><a href="{web_interface_url}" target="_blank">Click here to run Locust</a></p>
            <p>Click the link above to open the Locust web interface.</p>
            """
            return HTMLResponse(content=html_content, status_code=200)
        else:
            return {"status": "error", "message": "Could not retrieve Locust information"}

    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/run_locust_parallel")
async def run_locust_parallel_test():
    try:
        process = subprocess.Popen(
            ["locust", "-f", "locust_parallel.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )

        locust_version = ""
        web_interface_url = ""
        for line in process.stdout:
            if "Starting Locust" in line:
                locust_version = line.split("Starting Locust")[1].strip()
            elif "Starting web interface at" in line:
                web_interface_url = line.split("Starting web interface at")[1].split("(")[0].strip()
                break

        if locust_version and web_interface_url:
            html_content = f"""
            <p>Locust version: {locust_version}</p>
            <p><a href="{web_interface_url}" target="_blank">Click here to run Parallel Locust Test</a></p>
            <p>Click the link above to open the Locust web interface for parallel testing.</p>
            """
            return HTMLResponse(content=html_content, status_code=200)
        else:
            return {"status": "error", "message": "Could not retrieve Locust information for parallel test"}

    except Exception as e:
        return {"status": "error", "message": str(e)}