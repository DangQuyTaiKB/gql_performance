from locust import HttpUser, task, between
from gevent.pool import Pool
import os
import json
# Directory path for GraphQL queries, variables, and expected results
dir_path = os.path.dirname(os.path.realpath(__file__))
location = "./src/gqls"
location = "D:/Documents/Unob_10_Diplomova/Thesis/code/gql_performance_test/src/locust\src_/gqls"

print(f"location: {location}", flush=True)

# Helper Functions
def getQuery(tableName, queryName):
    queryFileName = f"{location}/{tableName}/{queryName}.gql"
    with open(queryFileName, "r", encoding="utf-8") as f:
        query = f.read()
    return query

def getVariables(tableName, queryName):
    variableFileName = f"{location}/{tableName}/{queryName}.var.json"
    if os.path.isfile(variableFileName):
        with open(variableFileName, "r", encoding="utf-8") as f:
            variables = json.load(f)
    else:
        variables = {}
    return variables

def getExpectedResult(tableName, queryName):
    resultFileName = f"{location}/{tableName}/{queryName}.res.json"
    if os.path.isfile(resultFileName):
        with open(resultFileName, "r", encoding="utf-8") as f:
            expectedResult = json.load(f)
    else:
        expectedResult = None
    return expectedResult

def createQueryTask(tableName, queryName="readp", variables=None, expectedResult=None):
    query = getQuery(tableName=tableName, queryName=queryName)
    variables = getVariables(tableName=tableName, queryName=queryName) if variables is None else variables
    expectedResult = getExpectedResult(tableName=tableName, queryName=queryName) if expectedResult is None else expectedResult

    def result(self):
        response = self.client.post(
            "/api/gql",
            json={
                "query": query,
                "variables": variables
            },
            name=f"{queryName}@{tableName}"
        )
        if expectedResult is not None:
            assert expectedResult == response.json(), (
                f"Got unexpected result for {queryName}@{tableName}\n"
                f"Expected: {expectedResult}\n"
                f"Received: {response.json()}"
            )
    result.__name__ = f"{tableName}_{queryName}"
    return result

# Locust Test Class
class ApiAdminUser(HttpUser):
    host = "http://localhost:33001"
    wait_time = between(1, 5)
    parallel_pool = None

    def on_start(self):
        """
        Perform initial login to get the required session or authorization token.
        """
        response = self.client.get("/oauth/login3")
        key_response = response.json()

        # Login with retrieved key
        files = {
            'username': (None, "john.newbie@world.com"),
            'password': (None, "john.newbie@world.com"),
            "key": (None, key_response.get("key", None))
        }
        self.client.post("/oauth/login2", files=files)

        # Initialize the parallel pool
        self.parallel_pool = Pool(100)  # Adjust the pool size for parallelism

    @task
    def graphql_parallel_test(self):
        """
        Perform parallel GraphQL requests.
        """
        # Define table-query pairs for parallel testing
        table_queries = [
            ("users", "readp"),
            ("plans", "readp"),
            ("groups", "readp"),
            ("rolecategories", "readp"),
        ]

        # Function to execute each query task
        def execute_query_task(table_query):
            tableName, queryName = table_query
            query_task = createQueryTask(tableName, queryName)
            query_task(self)

        # Spawn parallel tasks
        for table_query in table_queries:
            self.parallel_pool.spawn(execute_query_task, table_query)

        # Wait for all tasks to complete
        self.parallel_pool.join()

    query_users_page_1 = task(createQueryTask(tableName="users"))
    query_plans_page_2 = task(createQueryTask(tableName="plans"))
    query_group_page_3 = task(createQueryTask(tableName="groups"))
    query_role_page_4 = task(createQueryTask(tableName="rolecategories"))
