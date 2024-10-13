queryStr_0 = """
{
result: userPage(limit: 100) {
    id
    email
    name
    surname
}

}

"""

queryStr = """
{
result: userPage(
    limit: 1000000, 
    where: {memberships: {group: {name: {_ilike: "%uni%"}}}}
) {
    id
    email
    name
    surname
    presences {
    event {
        id
        name
        startdate
        enddate
        eventType {
        id
        name
        }
    }
    presenceType {
        id
        name
    }

    }

}

}

"""