
def get_name_by_type_and_uid(package, type, uid):
    return next((x for x in package[type] if x["id"] == uid), None)["name"]
