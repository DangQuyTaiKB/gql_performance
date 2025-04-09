import asyncio
import time
import statistics
import aiohttp
import psutil
import random
import logging
import json

logger = logging.getLogger("stress_test")
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler("stress_test.log")
file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
logger.addHandler(file_handler)

async def stress_test_concurrent(q, token, url, initial_load, step_size, max_limit, recovery_steps):
    """Concurrent stress test with variables support"""
    
    async def make_request_with_semaphore(session, semaphore):
        async with semaphore:
            query_name = random.choice(list(q.keys()))
            query_data = q[query_name]
            query_text = query_data['query']
            variables = query_data.get('variables', {})
            
            if isinstance(variables, str):
                try:
                    variables = json.loads(variables) if variables.strip() else {}
                except json.JSONDecodeError:
                    variables = {}

            payload = {
                "query": query_text,
                "variables": variables
            }
            
            cookies = {'authorization': token}
            start_time = time.time()
            
            try:
                async with session.post(
                    url,
                    json=payload,
                    cookies=cookies,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    response_json = await resp.json()
                    end_time = time.time()
                    logger.info(f"Request to {query_name} - Status: {resp.status}")
                    return resp.status, (end_time - start_time)
            except Exception as e:
                logger.error(f"Request failed: {str(e)}")
                return None, 0

    current_load = initial_load
    all_results = []
    
    # Stress phase
    while current_load <= max_limit:
        logger.info(f"Testing with {current_load} concurrent requests")
        semaphore = asyncio.Semaphore(current_load)
        
        async with aiohttp.ClientSession() as session:
            tasks = [asyncio.wait_for(make_request_with_semaphore(session, semaphore), timeout=30)
                    for _ in range(current_load)]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        valid_responses = [r for r in responses if not isinstance(r, Exception)]
        success_count = sum(1 for status, _ in valid_responses if status == 200)
        success_rate = (success_count / current_load * 100) if current_load > 0 else 0
        
        response_times = [t for _, t in valid_responses]
        stats = {
            "load": current_load,
            "success_rate": success_rate,
            "avg_time": statistics.mean(response_times) if response_times else 0,
            "min_time": min(response_times) if response_times else 0,
            "max_time": max(response_times) if response_times else 0,
            "cpu": psutil.cpu_percent(),
            "memory": psutil.virtual_memory().percent
        }
        all_results.append(stats)
        
        current_load += step_size
        await asyncio.sleep(1)
    
    # Recovery phase
    while current_load > initial_load:
        current_load -= recovery_steps
        logger.info(f"Recovery testing with {current_load} requests")
        semaphore = asyncio.Semaphore(current_load)
        
        async with aiohttp.ClientSession() as session:
            tasks = [asyncio.wait_for(make_request_with_semaphore(session, semaphore), timeout=30)
                    for _ in range(current_load)]
            await asyncio.gather(*tasks, return_exceptions=True)
        
        await asyncio.sleep(1)
    
    return all_results