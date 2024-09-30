# queryStr = """
# {
#   result: groupById(id: "2d9dcd22-a4a2-11ed-b9df-0242ac120003") {
#     name
#     id
#     memberships {
#       user {
#         id
#         fullname
#         classifications {
#           level {
#             id
#             name
#           }
#           id
#           order
#           semester {
#             id
#             order
#             subject {
#               id
#               name
#             }
#           }
#         }
#       }
#     }
#   }
# }
# """
# mappers = {
#     "id": "id",
#     "name": "name",
#     "user_id": "memberships.user.id",
#     "user_name": "memberships.user.fullname",
#     "level_order": "memberships.user.classifications.order"
# }

mappers = {
    "id": "id",
    "name": "name"
}

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


