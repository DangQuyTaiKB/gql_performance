from fastapi import FastAPI
import json
import pandas as pd
import aiohttp
import asyncio
from aiohttp import ClientSession, TCPConnector
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

from query.userPage import queryStr_0, queryStr


@app.get("/query")
async def fullPipe():

    token = await getToken(username, password)
    qfunc = query(queryStr, token)
    response = await qfunc({}) #variables is empty here {}
    outfile(response, 'response')
    return response




@app.get("/loadTest")
async def loadTest():
    token = await getToken(username, password)
    num_requests = 1000  # You can adjust this number
    concurrent_limit = 10  # You can adjust this number
    
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
    num_requests = 1000  # Total number of requests that you want to send to the server in the load test - total workload
    concurrent_limit = 10  # total of TCP connections that you want to open at the same time from the client to the server
    
    # results, response_times = await load_test_1(queryStr_0, token, num_requests, concurrent_limit)
    results, response_times, avg_response_time, min_response_time, max_response_time, median_response_time, successful_requests, failure_count = await load_test_1(queryStr_0, token, num_requests, concurrent_limit)
    # print(response_times)
    # # Process the results if needed
    # successful_requests = [r for r, _ in results if isinstance(r, dict) and 'data' in r]
    
    # # Calculate additional statistics
    # avg_response_time = sum(response_times) / len(response_times)
    # min_response_time = min(response_times)
    # max_response_time = max(response_times)
    # print the nested dictionary of [order, response times, response]
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
    token = await getToken(username, password)
    num_requests = 1000
    concurrent_limit = 10
    
    results = await load_test_2(queryStr_0, token, num_requests, concurrent_limit)
    return results