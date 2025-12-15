def emptyProfile(name:str):
    return {
        "name":name,
        "user_settings":"settings.yml"
    }

def emptySettings():
    return {
        "borrowingDuration": 28,
        "renewDuration": 14,
        "maxRenewTimes": 2,
        "maxDelayedBook": 1,
        "maxBooks": 4
    }