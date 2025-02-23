from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import json
import os
from utils.getToken import getToken
from utils.load_test import load_test_concurrent_1, load_test_concurrent_2, load_test_parallel
from utils.stress_test import stress_test_concurrent, stress_test_parallel
import subprocess
import psutil
from pyinstrument import Profiler

q = {
"q0" : "{result: userPage(limit: 100) {id email name surname}}", 
"q1" : "{result: userPage(limit: 100) {id email name }}", 
"q2" : "{result: userPage(limit: 100) {id email}}", 
"q3" : "{result: userPage(limit: 100) {id}}", 
"q4" : "{result: userPage(limit: 1000) {id email name}}"
}
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
@app.post("/load_test_concurrent_1")
async def loadTest1(request: Request):
    description = """
    • This test simulates multiple requests being sent simultaneously by several users but limited by a defined concurrent_limit.
    • Purpose: To measure the system's performance under a large number of concurrent requests.
    • Real-world example: An e-commerce website receiving multiple requests from users browsing product pages.
    """
    body = await request.json()
    num_requests = int(body.get('num_requests', 100))
    concurrent_limit = int(body.get('concurrent_limit', 5))
    token = await getToken(username, password, login_url)
    query = body.get('query', q)  # Use the dictionary of queries
    print(query)

    results = await load_test_concurrent_1(query, token, num_requests, concurrent_limit, gqlurl)
    outfile(results['results'], 'response')
    time_result = {key: value for key, value in results.items() if key != "results"}

    return {"description": description, "query": query, "results": time_result}

@app.post("/load_test_concurrent_2")
async def loadTest2(request: Request):
    description = """
    • This test simulates multiple requests per user with a defined concurrent_limit.
    • Purpose: To evaluate the system's handling of multiple requests per user.
    • Real-world example: Users making multiple API calls in a short period.
    """
    body = await request.json()
    requests_per_user = int(body.get('requests_per_user', 20))
    concurrent_limit = int(body.get('concurrent_limit', 5))
    token = await getToken(username, password, login_url)
    query = body.get('query', q)  # Use the dictionary of queries
    print(query)
    results = await load_test_concurrent_2(query, token, requests_per_user, concurrent_limit, gqlurl)
    time_result = {key: value for key, value in results.items() if key != "results"}
    return {"description": description, "query": query, "results": time_result}

@app.post("/parallel_load_test")
async def parallelLoadTest(request: Request):
    description = """
    • This test uses multiple workers to send requests in parallel.
    • Purpose: To test the system's performance with parallel request handling.
    • Real-world example: A backend service handling requests from multiple microservices.
    """
    body = await request.json()
    num_requests = int(body.get('num_requests', 100))
    num_workers = int(body.get('num_workers', 5))
    token = await getToken(username, password, login_url)
    query = body.get('query', q)  # Use the dictionary of queries
    print(query)
    payload = {"query": query, "variables": {}}

    results = await load_test_parallel(gqlurl, payload, token, num_requests, num_workers)
    time_result = {key: value for key, value in results.items() if key != "results"}
    time_result.update({"num_workers": num_workers})
    return {"description": description, "query": query, "results": time_result}

@app.post("/stress_test_concurrent")
async def stress_test_concurrent_endpoint(request: Request):
    description = """
    • Gradually increasing load to test system limits.
    • Purpose: To identify the maximum load the system can handle before failure.
    • Real-world example: A sudden spike in user activity on a social media platform.
    """
    body = await request.json()
    initial_requests = int(body.get('initial_requests', 50))
    step_size = int(body.get('step_size', 40))
    max_limit = int(body.get('max_limit', 200))
    recovery_steps = int(body.get('recovery_steps', 40))
    token = await getToken(username, password, login_url)
    query = body.get('query', q)  # Use the dictionary of queries
    print(query)

    results = await stress_test_concurrent(query, token, gqlurl, initial_requests, step_size, max_limit, recovery_steps)
    
    if not isinstance(results, list):
        results = [results]

    time_result = {"results": results} if isinstance(results, list) else {key: value for key, value in results.items() if key != "results"}

    return {"description": description, "query": query, "results": time_result}

@app.post("/stress_test_parallel")
async def stress_test_parallel_endpoint(request: Request):
    description = """
    • Using parallel execution to test system limits.
    • Purpose: To evaluate system performance under parallel stress conditions.
    • Real-world example: A distributed system handling requests from multiple sources.
    """
    body = await request.json()
    initial_load = int(body.get('initial_load', 50))
    step_size = int(body.get('step_size', 40))
    max_limit = int(body.get('max_limit', 200))
    recovery_steps = int(body.get('recovery_steps', 40))
    token = await getToken(username, password, login_url)
    query = body.get('query', q)  # Use the dictionary of queries
    print(query)

    results = await stress_test_parallel(query, token, gqlurl, initial_load, step_size, max_limit, recovery_steps)
    
    if not isinstance(results, list):
        results = [results]

    time_result = {"results": results} if isinstance(results, list) else {key: value for key, value in results.items() if key != "results"}
    return {"description": description, "query": query, "results": time_result}

@app.post("/locust_concurrent")
async def run_locust_concurrent_test(request: Request):
    description = """
    • Using Locust to simulate concurrent user load.
    • Purpose: To test system performance with concurrent user simulation.
    • Real-world example: Simulating user traffic on a web application.
    """
    body = await request.json()
    query = body.get('query', q)  # Use the dictionary of queries
    print(query)
    try:
        # Terminate all existing Locust processes
        for proc in psutil.process_iter(['pid', 'name']):
            if 'locust' in proc.info['name']:
                proc.terminate()
                proc.wait()
        with open('locust_queries.json', 'w') as f:
            json.dump(query, f)
        process = subprocess.Popen(
            ["locust", "-f", "locust/locust_con_v2.py"],
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

        results = {
            "locust_version": locust_version,
            "web_interface_url": web_interface_url
        }

        return {"description": description, "results": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/locust_parallel")
async def run_locust_parallel_test(request: Request):
    description = """
    • Using Locust to simulate parallel user load.
    • Purpose: To test system performance with parallel user simulation.
    • Real-world example: Simulating distributed user traffic on a web application.
    """
    # kết thúc tất cả 
    body = await request.json()
    query = body.get('query', {})
    try:
        # Terminate all existing Locust processes
        for proc in psutil.process_iter(['pid', 'name']):
            if 'locust' in proc.info['name']:
                proc.terminate()
                proc.wait()
        with open('locust_queries.json', 'w') as f:
            json.dump(query, f)
        process = subprocess.Popen(
            ["locust", "-f", "locust/locust_par_v2.py"],
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

        results = {
            "locust_version": locust_version,
            "web_interface_url": web_interface_url
        }

        return {"description": description, "results": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}

with open("html/index.html", encoding='utf-8', errors='ignore') as f:
    html = f.read()

@app.get("/ui")
async def web_app() -> HTMLResponse:
    """
    Web App
    """
    return HTMLResponse(html)



