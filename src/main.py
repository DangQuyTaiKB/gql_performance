from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import json
import os
from utils.send_payload import query
from utils.getToken import getToken
# from utils.auth import username, password
from utils.load_test import load_test_concurrent_1, load_test_concurrent_2, load_test_parallel
from utils.stress_test import stress_test_concurrent, stress_test_parallel
from query.userPage import queryStr_0, queryStr
import subprocess

app = FastAPI()

gqlurl = os.getenv("GQL_PROXY", "http://localhost:33001/api/gql")
login_url = os.getenv("GQL_LOGIN", "http://localhost:33001/oauth/login3")
username = os.getenv("GQL_USERNAME", "john.newbie@world.com")
password = os.getenv("GQL_PASSWORD", "john.newbie@world.com")

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
    token = await getToken(username, password, login_url)
    qfunc = query(queryStr, token)
    response = await qfunc({})
    outfile(response, 'response')
    return response

############# Load Test ###############

@app.get("/load_test_concurrent_1")
async def loadTest1():
    token = await getToken(username, password, login_url)
    num_requests = 100
    concurrent_limit = 5

    results = await load_test_concurrent_1(queryStr_0, token, num_requests, concurrent_limit, gqlurl)
    outfile(results['results'], 'response')
    time_result = {key: value for key, value in results.items() if key != "results"}  #dictionary comprehension
    return time_result


@app.get("/load_test_concurrent_2")
async def loadTest2():
    token = await getToken(username, password, login_url)
    requests_per_user = 20 # number of requests per user
    concurrent_limit = 5 # number of users concurrently

    results = await load_test_concurrent_2(queryStr_0, token, requests_per_user, concurrent_limit, gqlurl)
    time_result = {key: value for key, value in results.items() if key != "results"}
    return time_result

@app.get("/parallel_load_test")
async def parallelLoadTest():
    token = await getToken(username, password, login_url)
    num_requests = 100
    num_workers = 5
    payload = {"query": queryStr_0, "variables": {}}

    # Call the updated parallel_load_test function
    results = await load_test_parallel(gqlurl, payload, token, num_requests, num_workers)
    
    # Exclude the "results" key from the returned dictionary
    time_result = {key: value for key, value in results.items() if key != "results"}
    time_result.update({"num_workers": num_workers})
    return time_result


############# Stress Test ###############

@app.get("/stress_test_concurrent")
async def stress_test_concurrent_endpoint():
    # Get the token
    token = await getToken(username, password, login_url) 
    
    # Query to be used in the stress test
    query = queryStr_0

    # Define test parameters
    initial_requests = 50  # Starting with 50 concurrent requests
    step_size = 40         # Increase by 50 requests each step
    max_limit = 200        # Stop at 200 requests
    recovery_steps = 40     # Decrease by 50 during recovery

    # Run the stress test
    results = await stress_test_concurrent(query, token, gqlurl, initial_requests, step_size, max_limit, recovery_steps)
    return {"results": results}

@app.get("/stress_test_parallel")
async def stress_test_parallel_endpoint():
    # Get the token
    token = await getToken(username, password, login_url)
    
    # Query to be used in the stress test
    query = queryStr_0

    # Define test parameters
    initial_load = 50         # Starting with 10 concurrent requests
    step_size = 40            # Increase load by 10 each step
    max_limit = 200           # Maximum of 100 concurrent requests
    recovery_steps = 40        # Decrease by 5 during recovery
    # Run the enhanced stress test
    results = await stress_test_parallel(query, token, gqlurl, initial_load, step_size, max_limit, recovery_steps)
    return {"results": results}


############# Locust Test ###############

@app.get("/run_locust_concurrent")
async def run_locust_concurrent_test():
    try:
        process = subprocess.Popen(
            ["locust", "-f", "locust/locust_concurrent.py"],
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
            ["locust", "-f", "locust/locust_paralel.py"],
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