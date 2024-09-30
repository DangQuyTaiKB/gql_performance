queryStr_0 = """
{
result: userPage(limit: 100) {
    id
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


mappers = {
    "id": "id"
}

mappers_0 = {
    "id": "id",
    "name": "name",
    "surname": "surname",
    "email": "email",
    "eventid": "presences.event.id",
    "eventname": "presences.event.name",
    "startdate": "presences.event.startdate",
    "enddate": "presences.event.enddate",
    "eventTypeid": "presences.event.eventType.id",
    "eventTypename": "presences.event.eventType.name",
    "presenceTypeid": "presences.presenceType.id",
    "presenceTypename": "presences.presenceType.name"
}