import os
import json

def load_gql_queries(container):
    queries = {}
    container_path = os.path.join('gqls', container)
    for operation in ['create', 'read', 'update', 'delete']:
        file_path = os.path.join(container_path, f'{operation}.gql')
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                queries[operation] = f.read().strip()
    return queries







def test_load_gql_queries():
    container = 'user'
    queries = load_gql_queries(container)
    assert 'create' in queries
    assert 'read' in queries
    assert 'update' in queries
    assert 'delete' in queries
    assert queries['create'] == 'mutation { createUser { id } }'
    assert queries['read'] == 'query { user { id } }'
    assert queries['update'] == 'mutation { updateUser { id } }'
    assert queries['delete'] == 'mutation { deleteUser { id } }'
    print(queries)
    print('Success')