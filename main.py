from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
import json
import os
from src.utils.getToken import getToken
from src.utils.load_test import load_test
from src.utils.sample_test import sample_test
from src.utils.stress_test import stress_test_concurrent
import subprocess
import psutil

app = FastAPI()

# gqlurl = os.getenv("GQL_PROXY", "http://frontend:8000/api/gql")
# login_url = os.getenv("GQL_LOGIN", "http://frontend:8000/oauth/login3")

gqlurl = os.getenv("GQL_PROXY", "http://localhost:33001/api/gql")
login_url = os.getenv("GQL_LOGIN", "http://localhost:33001/oauth/login3")
username = os.getenv("GQL_USERNAME", "john.newbie@world.com")
password = os.getenv("GQL_PASSWORD", "john.newbie@world.com")

print(gqlurl)
print(login_url)
print(username)
print(password)

q = {
"q0": "{result: userPage(limit: 100) {id email name surname}}",
"q1": "{userPage {id email}}"
}
############ Intro FastAPI ################
@app.get("/")
async def root():
    return {"message": "Hello World"}

def outfile(data, filename):
    with open(filename + '.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
############ FastAPI ################
@app.post("/load_test_1")
async def loadTest1(request: Request):
    description = """
    Scenario: "Burst Load (Simulating DDoS Attack)"
    """
    body = await request.json()
    num_requests = int(body.get('num_requests', 100))
    concurrent_limit = int(body.get('concurrent_limit', 5))
    token = await getToken(username, password, login_url)
    query = body.get('query', q)  # Use the dictionary of queries
    print(query)

    results = await load_test(query, token, num_requests, concurrent_limit, gqlurl)
    outfile(results['results'], 'response')
    time_result = {key: value for key, value in results.items() if key != "results"}

    return {"description": description, "query": query, "results": time_result}

@app.post("/sample_test")
async def sampleTest_endpoint(request: Request):
    description = """
    Sample query test
    """
    body = await request.json()
    token = await getToken(username, password, login_url)
    query = body.get('query', q)  # Use the dictionary of queries
    print(query)

    results = []
    for query_name, query_content in query.items():
        result = await sample_test(query_content, token, gqlurl)
        results.append({
            "query_name": query_name,
            "status": result["status"],
            "response_time": result["response_time"],
            "response_body": result["response_body"]
        })

    return {"description": description, "query": query, "results": results}



@app.post("/stress_test")
async def stress_test_endpoint(request: Request):
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
# ---------------------- Locust Endpoints ----------------------
@app.post("/locust_concurrent")
async def run_locust_concurrent_test(request: Request):

    description = "Locust is an open source performance/load testing tool for HTTP and other protocols. " \
    "Its developer-friendly approach lets you define your tests in regular Python code."

    body = await request.json()
    query = body.get('query', {})
    try:
        # Terminate existing Locust processes
        for proc in psutil.process_iter(['pid', 'name']):
            if 'locust' in proc.info['name'].lower():
                proc.terminate()
                proc.wait()
        
        with open('locust_queries.json', 'w') as f:
            json.dump(query, f)

        subprocess.Popen(
            [
                "locust", 
                "-f", "src/locust/locust_concurrent.py",
                "--logfile", "locust_concurrent.log"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )

        results = {
            "status": "success",
            "report_url": "http://localhost:8089",
        }

        # return {
        #     "status": "success",
        #     "report_url": "http://localhost:8089",
        # }
        return {"query": query, "results": results, "description": description}

    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/locust_parallel")
async def run_locust_parallel_test(request: Request):
    description = "Locust is an open source performance/load testing tool for HTTP and other protocols. " \
    "Its developer-friendly approach lets you define your tests in regular Python code."
    body = await request.json()
    query = body.get('query', {})
    try:
        # Terminate existing Locust processes
        for proc in psutil.process_iter(['pid', 'name']):
            if 'locust' in proc.info['name'].lower():
                proc.terminate()
                proc.wait()

        # Save queries to JSON
        with open('locust_queries.json', 'w') as f:
            json.dump(query, f)

        # Start Locust web UI
        subprocess.Popen(
            [
                "locust", 
                "-f", "src/locust/locust_parallel.py",
                "--logfile", "locust_parallel.log"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )

        # return {
        #     "status": "success",
        #     "report_url": "http://localhost:8089",
        # }
        results = {
            "status": "success",
            "report_url": "http://localhost:8089",
        }

        return {"query": query, "results": results, "description": description}

    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/get_logs")
async def get_logs(request: Request):
    try:
        test_type = request.query_params.get("type", "load")
        
        # Determine log file
        log_file = {
            "load": "load_test.log",
            "stress": "stress_test.log",
            "locust_concurrent": "locust_concurrent.log",
            "locust_parallel": "locust_parallel.log"
        }.get(test_type, "load_test.log")

        with open(log_file, "r") as f:
            content = f.read()
        
        return Response(
            content=f"=== {test_type.upper()} LOG ===\n{content}",
            media_type="text/plain"
        )

    except FileNotFoundError:
        return Response(content="No logs found yet. Run a test first.", status_code=404)
    
    except Exception as e:
        return Response(content=f"Error reading logs: {str(e)}", status_code=500)

# ---------------------- Other Endpoints ----------------------
@app.post("/clear_locust")
async def clear_locust():
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            if 'locust' in proc.info['name'].lower():
                proc.terminate()
                proc.wait()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}   

@app.get("/get_logs")
async def get_logs(request: Request):
    try:
        test_type = request.query_params.get("type", "load")  # Mặc định là "load"
        
        # Xác định file log dựa trên test type
        if test_type == "load":
            log_file = "load_test.log"
        elif test_type == "stress":
            log_file = "stress_test.log"
        elif test_type == "locust_concurrent":
            log_file = "locust_concurrent.log"
        elif test_type == "locust_parallel":
            log_file = "locust_parallel.log"
        else:
            return Response(content="Invalid test type.", status_code=400)
        
        with open(log_file, "r") as f:
            content = f.read()
            
        return Response(
            content=f"=== {test_type.upper()} TEST LOG ===\n{content}",
            media_type="text/plain"
        )
    except FileNotFoundError:
        return Response(content="No logs found yet. Run a test first.", status_code=404)
    except Exception as e:
        return Response(content=f"Error reading logs: {str(e)}", status_code=500)

with open("src/html/index.html", encoding='utf-8', errors='ignore') as f:
    html = f.read()

@app.get("/ui")
async def web_app() -> HTMLResponse:
    """
    Web App
    """
    return HTMLResponse(html)



