from locust import HttpUser, task, between
import uuid 
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
    def user_insert(self):
        """Mutation for inserting a new user"""
        USER_INSERT_MUTATION = """
            mutation UserInsert($id: UUID, $name: String) {
                result: userInsert(user: {id: $id, name: $name}) {
                    id
                    msg
                    result: user {
                        __typename
                        id
                        lastchange
                        name
                    }
                }
            }
        """
        
        mutation_vars = {
            "id": str(uuid.uuid4()),  # Generate random UUID
            "name": f"TestUser_{random.randint(1, 10000)}"
        }

        response = self.client.post(
            "/api/gql",
            json={
                "query": USER_INSERT_MUTATION,
                "variables": mutation_vars
            },
            name="user_insert"
        )

    @task(3)
    def page_query(self):
        """Query for planned lessons page"""
        PAGE_QUERY = """
            query Page($skip: Int, $limit: Int, $where: PlannedLessonInputFilter) {
                result: plannedLessonPage(skip: $skip, limit: $limit, where: $where) {
                    ...Lesson
                }
            }
            
            fragment Lesson on PlannedLessonGQLModel {
                __typename
                id
                name
                lastchange
                rbacObject { id }
                type { id }
                order
                length
                linkedTo { __typename id name }
                linkedWith { __typename id name }
                users { id }
                groups { id }
                facilities { id }
                event { id }
                semester { id }
                plan { __typename id name }
            }
        """
        
        query_vars = {
            "skip": 0,
            "limit": 10,
            "where": None  # You can add filter conditions here if needed
        }

        response = self.client.post(
            "/api/gql",
            json={
                "query": PAGE_QUERY,
                "variables": query_vars
            },
            name="planned_lesson_page"
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