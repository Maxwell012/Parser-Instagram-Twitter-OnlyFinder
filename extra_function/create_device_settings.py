

def create_device_settings(user_agent) -> dict | None:
    """
    ONLY USER AGENT FOR ANDROID

    if the user agent has a non-working app version of Instagram then return None
    else return device settings
    """

    try:
        slices = user_agent.strip(")").split("(")
        android_settings = slices[1].split("; ")
        app_version = slices[0].split(" ")[1]
        int(android_settings[-1])
    except IndexError:
        pass
    except Exception as ex:
        pass
    else:
        if "269.0.0.18.75" in app_version:
            device_settings = {
             "device_settings": {
                 "app_version": app_version,
                 "android_version": android_settings[0].split("/")[0],
                 "android_release": android_settings[0].split("/")[1],
                 "dpi": android_settings[1],
                 "resolution": android_settings[2],
                 "manufacturer": android_settings[3],
                 "device": android_settings[5],
                 "model": android_settings[4],
                 "cpu": android_settings[6],
                 "version_code": android_settings[-1]},
             "user_agent": user_agent}
            return device_settings
