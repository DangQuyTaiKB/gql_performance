queryStr = """
{groupById(id: "2d9dcd22-a4a2-11ed-b9df-0242ac120003")
{
        id
        name
        roles {
        user {
            id
            name
            surname
            email
        }
        roletype {
            id
            name
        }
        }
        subgroups {
        id
        name
        }
        memberships {
        user {
            id
            name

            roles {
            roletype {
                id
                name
            }
            group {
                id
                name
            }
            }

            membership {
            group {
                id
                name
            }
            }
        }
        }
    }
}
"""


