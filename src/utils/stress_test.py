import asyncio
import time
import statistics
import aiohttp
import psutil
import random
import logging
from concurrent.futures import ThreadPoolExecutor
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Tạo logger riêng cho stress_test
logger = logging.getLogger("stress_test")
logger.setLevel(logging.INFO)

# Handler cho file log
file_handler = logging.FileHandler("stress_test.log")
file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
logger.addHandler(file_handler)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError))
)
async def enhanced_request(session, url, query, token):
    """Make request with retry and timeout handling"""
    payload = {"query": query, "variables": {}}
    cookies = {'authorization': token}

    attempt = 1  # Biến đếm số lần thử
    while attempt <= 3:
        try:
            async with session.post(
                    url,
                    json=payload,
                    cookies=cookies,
                    timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                logger.info(f"Attempt {attempt}: Success [{resp.status}]")
                return resp.status, time.time()
        except Exception as e:
            logger.warning(f"Attempt {attempt}: Failed - {str(e)}")
            attempt += 1
            await asyncio.sleep(2 ** attempt)  # Backoff delay

    logger.error(f"Request failed after 3 attempts")
    return None, 0


async def stress_test_concurrent(q, token, url, initial_load, step_size, max_limit, recovery_steps):
    """Concurrent stress test with performance monitoring"""

    async def make_request_with_semaphore(session, semaphore):
        async with semaphore:
            query = random.choice(list(q.values()))
            start_time = time.time()
            try:
                status, end_time = await enhanced_request(session, url, query, token)
                return status, (end_time - start_time)
            except Exception as e:
                logger.error(f"Final failure: {str(e)}")
                return None, 0

    current_load = initial_load
    all_results = []

    logger.info(f"Starting stress test from {initial_load} to {max_limit}")

    while current_load <= max_limit:
        logger.info(f"Testing {current_load} concurrent requests")
        semaphore = asyncio.Semaphore(current_load)

        async with aiohttp.ClientSession() as session:
            tasks = [asyncio.wait_for(make_request_with_semaphore(session, semaphore), timeout=30) for _ in range(current_load)]
            responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Track system metrics
        cpu = psutil.cpu_percent()
        memory = psutil.virtual_memory().percent
        logger.info(f"System Metrics - CPU: {cpu}%, Memory: {memory}%")

        # Process results
        valid_responses = [r for r in responses if not isinstance(r, Exception)]
        response_statuses = [status for status, _ in valid_responses if status]

        failed = len([s for s in response_statuses if s != 200])
        success_rate = ((len(response_statuses) - failed) / len(response_statuses) * 100 if response_statuses else 0)
        if valid_responses:
            times = [t for _, t in valid_responses if t > 0]
            stats = {
                "load": current_load,
                "success_rate": success_rate,
                "avg_time": statistics.mean(times) if times else 0,
                "min_time": min(times) if times else 0,
                "max_time": max(times) if times else 0,
                "cpu": cpu,
                "memory": memory
            }
            all_results.append(stats)
            logger.info(f"Success: {success_rate:.1f}% | Avg: {stats['avg_time']:.5f}s")

        current_load += step_size
        await asyncio.sleep(1)

    # Recovery phase
    while current_load > initial_load:
        current_load -= recovery_steps
        logger.info(f"Testing recovery with {current_load} requests")
        semaphore = asyncio.Semaphore(current_load)
        async with aiohttp.ClientSession() as session:
            tasks = [asyncio.wait_for(make_request_with_semaphore(session, semaphore), timeout=30) for _ in range(current_load)]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
        await asyncio.sleep(1)

    return all_results


async def make_request(session, q, token, url):
    """Wrapper for enhanced request"""
    query = random.choice(list(q.values()))
    start_time = time.time()
    try:
        status, end_time = await enhanced_request(session, url, query, token)
        return status, (time.time() - start_time)  # Đo thời gian đúng
    except Exception as e:
        logger.error(f"Request failed: {str(e)}")
        return None, 0


async def run_concurrent_load(q, token, url, current_load):
    semaphore = asyncio.Semaphore(current_load)
    async with aiohttp.ClientSession() as session:
        tasks = [make_request(session, q, token, url) for _ in range(current_load)]
        return await asyncio.gather(*tasks)


# Function to save results to CSV
def save_results_to_csv(results, filename="stress_test_results.csv"):
    keys = results[0].keys() if results else []
    with open(filename, mode='w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(results)


# Example to run the stress test
# results = await stress_test_concurrent(query_data, token, url, 10, 5, 100, 5)
# save_results_to_csv(results)
