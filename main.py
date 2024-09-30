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
from utils.load_test import load_test, load_test_1

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
    num_requests = 100  # You can adjust this number
    concurrent_limit = 100  # You can adjust this number
    
    results, response_times = await load_test_1(queryStr_0, token, num_requests, concurrent_limit)
    
    # Process the results if needed
    successful_requests = [r for r, _ in results if isinstance(r, dict) and 'data' in r]
    
    # Calculate additional statistics
    avg_response_time = sum(response_times) / len(response_times)
    min_response_time = min(response_times)
    max_response_time = max(response_times)
    
    return {
        "total_requests": num_requests,
        "successful_requests": len(successful_requests),
        "failed_requests": num_requests - len(successful_requests),
        "average_response_time": avg_response_time,
        "min_response_time": min_response_time,
        "max_response_time": max_response_time
    }