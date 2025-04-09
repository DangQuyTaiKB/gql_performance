from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, FileResponse
import json
import os
from src.utils.getToken import getToken
from src.utils.load_test import load_test
from src.utils.sample_test import sample_test
from src.utils.stress_test import stress_test_concurrent
import subprocess
import psutil
import glob

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
    description = "Scenario: Burst Load (Simulating DDoS Attack)"
    body = await request.json()
    num_requests = int(body.get('num_requests', 100))
    concurrent_limit = int(body.get('concurrent_limit', 5))
    token = await getToken(username, password, login_url)
    
    # Lấy và chuẩn hóa queries từ body
    queries_input = body.get('queries', {})
    processed_queries = {}
    
    for query_name, query_data in queries_input.items():
        query_content = query_data.get('query', '')
        query_variables = query_data.get('variables', {})
        
        # Chuẩn hóa variables thành dictionary
        if isinstance(query_variables, str):
            try:
                query_variables = json.loads(query_variables) if query_variables.strip() else {}
            except json.JSONDecodeError:
                query_variables = {}
        
        processed_queries[query_name] = {
            'query': query_content,
            'variables': query_variables
        }
    
    # Gọi hàm load_test gốc
    test_results = await load_test(
        q=processed_queries,
        token=token,
        num_requests=num_requests,
        concurrent_limit=concurrent_limit,
        url=gqlurl
    )
    
    # Xử lý kết quả phù hợp với output từ hàm load_test gốc
    outfile(test_results.get('results', []), 'response')
    
    return {
        "description": description,
        "queries": queries_input,
        "results": {
            "summary": {
                "total_requests": test_results["num_requests"],
                "successful": test_results["success_count"],
                "failed": test_results["failure_count"],
                "average_response_time": test_results["avg_response_time"],
                "min_response_time": test_results["min_response_time"],
                "max_response_time": test_results["max_response_time"],
                "median_response_time": test_results["median_response_time"],
                "cpu_usage": test_results["cpu_usage"],
                "memory_usage": test_results["memory_usage"]
            },
            # "response_times": test_results["response_times"]
        }
    }

@app.post("/sample_test")
async def sampleTest_endpoint(request: Request):
    description = """
    Sample query test
    """
    body = await request.json()
    print(body)
    token = await getToken(username, password, login_url)
    queries = body.get('queries', {})  # Get the combined queries object
    print(queries)

    results = {}
    for query_name, query_data in queries.items():
        query_content = query_data.get('query')
        query_variables = query_data.get('variables')

        # Ensure variables is a dictionary
        if isinstance(query_variables, str):
            try:
                query_variables = json.loads(query_variables)
            except json.JSONDecodeError:
                query_variables = {}  # Default to an empty dictionary if parsing fails

        # print(f"Executing {query_name} with query: {query_content} and variables: {query_variables}")
        
        # Send query along with variables
        result = await sample_test(query_content, token, gqlurl, query_variables)
        print(f"Result for {query_name}: {result}")
        # print(f"Result for {query_name}: {result}")
        results[query_name] = {
            "status": result["status"],
            "response_time": result["response_time"],
            "response_body": result["response_body"]
        }
        print(results)

    return {"description": description, "queries": queries, "results": results}

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
    
    # Lấy và chuẩn hóa queries từ body
    queries_input = body.get('queries', {})
    processed_queries = {}
    
    for query_name, query_data in queries_input.items():
        query_content = query_data.get('query', '')
        query_variables = query_data.get('variables', {})
        
        # Chuẩn hóa variables thành dictionary
        if isinstance(query_variables, str):
            try:
                query_variables = json.loads(query_variables) if query_variables.strip() else {}
            except json.JSONDecodeError:
                query_variables = {}
        
        processed_queries[query_name] = {
            'query': query_content,
            'variables': query_variables
        }
    
    # Gọi hàm stress_test_concurrent đã được cập nhật
    test_results = await stress_test_concurrent(
        q=processed_queries,
        token=token,
        url=gqlurl,
        initial_load=initial_requests,
        step_size=step_size,
        max_limit=max_limit,
        recovery_steps=recovery_steps
    )
    
    # Chuẩn bị kết quả trả về
    if not isinstance(test_results, list):
        test_results = [test_results]

    return {
        "description": description,
        "queries": queries_input,  # Trả về queries gốc từ frontend
        "results": {
            "phases": test_results,  # Kết quả từng phase test
            "summary": {
                "initial_load": initial_requests,
                "max_reached": max_limit,
                "total_phases": len(test_results),
                "final_success_rate": test_results[-1]["success_rate"] if test_results else 0
            }
        }
    }

# ---------------------- Locust Endpoints ----------------------

@app.post("/locust_concurrent")
async def run_locust_concurrent_test(request: Request):
    description = "Locust is an open source performance/load testing tool for HTTP and other protocols. " \
                "Its developer-friendly approach lets you define your tests in regular Python code."

    body = await request.json()
    queries = body.get('queries', {})
    
    try:
        # Dừng các tiến trình Locust cũ
        for proc in psutil.process_iter(['pid', 'name']):
            if 'locust' in proc.info['name'].lower():
                proc.terminate()
                proc.wait()
        
        # Chuẩn hóa queries và variables
        processed_queries = {}
        for q_name, q_data in queries.items():
            if isinstance(q_data, str):
                # Nếu chỉ là query string
                processed_queries[q_name] = {"query": q_data, "variables": {}}
            else:
                # Nếu có cả query và variables
                variables = q_data.get("variables", {})
                if isinstance(variables, str):
                    try:
                        variables = json.loads(variables) if variables.strip() else {}
                    except json.JSONDecodeError:
                        variables = {}
                
                processed_queries[q_name] = {
                    "query": q_data.get("query", ""),
                    "variables": variables
                }
        
        # Lưu queries vào file
        with open('locust_queries.json', 'w') as f:
            json.dump(processed_queries, f)

        # Khởi chạy Locust
        subprocess.Popen(
            [
                "locust", 
                "-f", "src/locust/locust_concurrent.py",
                "--logfile", "locust_concurrent.log"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )

        return {
            "description": description,
            "queries": queries,
            "results": {
                "status": "success",
                "report_url": "http://localhost:8089"
            }
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "description": description
        }

@app.post("/locust_parallel")
async def run_locust_parallel_test(request: Request):
    description = "Locust is an open source performance/load testing tool for HTTP and other protocols. " \
                "Its developer-friendly approach lets you define your tests in regular Python code."

    body = await request.json()
    queries = body.get('queries', {})
    num_parallel_requests = int(body.get('num_parallel_requests', 5))
    
    try:
        # Terminate existing Locust processes
        for proc in psutil.process_iter(['pid', 'name']):
            if 'locust' in proc.info['name'].lower():
                proc.terminate()
                proc.wait()

        # Process queries and variables
        processed_queries = {}
        for q_name, q_data in queries.items():
            if isinstance(q_data, str):
                # Old format: just query string
                processed_queries[q_name] = {"query": q_data, "variables": {}}
            else:
                # New format: query + variables
                variables = q_data.get("variables", {})
                if isinstance(variables, str):
                    try:
                        variables = json.loads(variables) if variables.strip() else {}
                    except json.JSONDecodeError:
                        variables = {}
                
                processed_queries[q_name] = {
                    "query": q_data.get("query", ""),
                    "variables": variables
                }

        # Save configuration
        with open('locust_queries.json', 'w') as f:
            json.dump(processed_queries, f)

        with open('locust_parallel_requests.txt', 'w') as f:
            f.write(str(num_parallel_requests))

        # Start Locust
        subprocess.Popen(
            [
                "locust",
                "-f", "src/locust/locust_parallel.py",
                "--logfile", "locust_parallel.log"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )

        return {
            "description": description,
            "queries": queries,
            "results": {
                "status": "success",
                "report_url": "http://localhost:8089",
                "num_parallel_requests": num_parallel_requests
            }
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "description": description
        }

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
        if (test_type == "load"):
            log_file = "load_test.log"
        elif (test_type == "stress"):
            log_file = "stress_test.log"
        elif (test_type == "locust_concurrent"):
            log_file = "locust_concurrent.log"
        elif (test_type == "locust_parallel"):
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

@app.get("/download-latest-log")
async def download_latest_log():
    log_files = glob.glob('logs/results_*.csv')
    if not log_files:
        return {"error": "No log files found"}
    latest_log = max(log_files, key=os.path.getctime)  # Lấy file mới nhất
    return FileResponse(latest_log, media_type='text/csv', filename=os.path.basename(latest_log))



