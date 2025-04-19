from locust import HttpUser, task, between
import random
from locust import events
from jtl_listener import JtlListener

class OptimizedLocustUser(HttpUser):
    host = "http://localhost:33001"
    wait_time = between(1, 5)
    
    def on_start(self):
        """Authentication with automatic lastchange tracking"""
        resp = self.client.get("/oauth/login3")
        key = resp.json().get("key", None)
        
        self.client.post("/oauth/login2", files={
            'username': (None, "john.newbie@world.com"),
            'password': (None, "john.newbie@world.com"),
            "key": (None, key)
        },
        allow_redirects=True, catch_response=True)


    @task
    def update_role(self):
        """Mutation with automatic lastchange handling"""
        test_role_id = "5f0c2596-931f-11ed-9b95-0242ac110002"
        ROLE_TYPE_QUERY = """
            query RoleTypeById($id: UUID!) {
            result: roleTypeById(id: $id) {
                ...RoleType
            }
            }
            fragment RoleType on RoleTypeGQLModel {
            id
            lastchange
            name
            nameEn
            created
            }
        """

        ROLE_UPDATE_MUTATION = """
            mutation RoleTypeUpdate($id: UUID!, $lastchange: DateTime!, $name: String) {
            result: roleTypeUpdate(roleType: {id: $id, lastchange: $lastchange, name: $name}) {
                id
                msg
                result: roleType {
                ...RoleType
                }
            }
            }
            fragment RoleType on RoleTypeGQLModel {
            id
            lastchange
            name
            nameEn
            created
            }
        """
        response = self.client.post(
            "/api/gql",
            json={
                "query": ROLE_TYPE_QUERY,
                "variables": {"id": test_role_id}
            },
            name="get_role_by_id"
        )
        response_data = response.json()
        role_data = response_data.get("data", {}).get("result", {})
        last_change = role_data.get("lastchange", None)


        mutation_vars = {
            "id": test_role_id,
            "name": f"Updated_{random.randint(1, 10000)}",
            "lastchange": last_change
        }

        response = self.client.post(
            "/api/gql",
            json={
                "query": ROLE_UPDATE_MUTATION,
                "variables": mutation_vars
            },
            name="update_role"  # Name for statistics
        )


@events.init.add_listener
def on_locust_init(environment, **_kwargs):
    JtlListener(
        env=environment,
        project_name="tai_projects",
        scenario_name="tai_senario",
        environment="tai_environment_test",
        backend_url="http://localhost"
    )