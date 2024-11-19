from locust import HttpUser, task, between
import os 
import re
import json
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
print("dir_path", dir_path, flush=True)

location = "./src/gqls"
location = "D:/Documents/Unob_10_Diplomova/Thesis/code/gql_performance_test/src/locust\src_/gqls"

# location = re.sub(r"\\.+", r"\\gqls", dir_path)
print(f"location: {location}", flush=True)

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
            assert expectedResult == response, f"got unexpected result for {queryName}@{tableName}\n{result}\nwith{query}\nvariables={variables}"
    result.__name__ = f"{tableName}_{queryName}"
    return result

class ApiAdminUser(HttpUser):
    host = "http://localhost:33001"
    @task
    def query_me(self):
        query = "{me{id email}}"
        self.client.post(
            "/api/gql",
            json={
                "query": query
            }, 
            name="me"
        )

    query_users_page_1 = task(createQueryTask(tableName="users"))
    query_plans_page_2 = task(createQueryTask(tableName="plans"))
    query_group_page_3 = task(createQueryTask(tableName="groups"))
    query_role_page_4 = task(createQueryTask(tableName="rolecategories"))

    def on_start(self):
        response = self.client.get(
            "/oauth/login3", 
            json={},
            # catch_response=True
        )  
        keyresponse = response.json()      

        # self.client.post(
        #     "/oauth/login3", 
        #     json={
        #         **keyresponse,
        #         "username":"john.newbie@world.com", 
        #         "password":"john.newbie@world.com"
        #     }
        # )

        files = {
            'username': (None, "john.newbie@world.com"),
            'password': (None, "john.newbie@world.com"),
            "key": (None, keyresponse.get("key", None))
        }
        self.client.post("/oauth/login2", files=files)