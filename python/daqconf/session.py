import conffwk

def get_segment_apps(segment):
    """
    Gather the list of applications in the segment and its sub-segments
    """
    apps = []

    for ss in segment.segments:
        apps += get_segment_apps(ss)

    for aa in segment.applications:
        apps.append(aa)
    
    apps.append(segment.controller)

    return apps


def get_session_apps(confdb, session_name=""):
    """
    Gather the apps defined used in a session.
    """
    if session_name == "":
        session_dals = confdb.get_dals(class_name="Session")
        if len(session_dals) == 0:
            print(f"Error could not find any Session in file {confdb.databases}")
            return
        session = session_dals[0]
    else:
        try:
            session = confdb.get_dal("Session", session_name)
        except:
            print(f"Error could not find Session {session_name} in file {confdb.databases}")
            return

    segment = session.segment

    return get_segment_apps(segment)


def get_apps_in_any_session(confdb):
    """
    Gather the applications used in any session present in the database
    """

    output = {}
    session_dals = confdb.get_dals(class_name="Session")
    if len(session_dals) == 0:
        print(f"Error could not find any Session in file {confdb.databases}")
        return {}

    for session in session_dals:
        segment = session.segment
        output[session.id] = get_segment_apps(segment)

    return output


#------------------------------------------------------------------------------
def enable_resource_in_session(confdb, session_name: str, resource: list[str], enable: bool):
    """
    Enables / disables resources from the first Session of the
    specified OKS database file
    """
    if session_name == "":
        session_dals = confdb.get_dals(class_name="Session")
        if len(session_dals) == 0:
            print(f"Error could not find any Session in file {confdb.databases}")
            return
        session = session_dals[0]
    else:
        try:
            session = confdb.get_dal("Session", session_name)
        except:
            print(f"Error could not find Session {session_name} in file {confdb.databases}")
            return
        
    disabled = session.disabled
    for res in resource:
        try:
            res_dal = confdb.get_dal("ResourceBase", res)
        except:
            print(f"Error could not find Resource {res} in file {confdb.databases}")
            continue

        if not enable:
            if res_dal in disabled:
                print(
                    f"{res} is already in disabled relationship of Session {session.id}"
                )
            else:
                # Add to the Segment's disabled list
                print(f"Adding {res} to disabled relationship of Session {session.id}")
                disabled.append(res_dal)
        else:
            if res_dal not in disabled:
                print(f"{res} is not in disabled relationship of Session {session.id}")
            else:
                # Remove from the Segments disabled list
                print(
                    f"Removing {res} from disabled relationship of Session {session.id}"
                )
                disabled.remove(res_dal)
    session.disabled = disabled
    confdb.update_dal(session)
    confdb.commit()




#------------------------------------------------------------------------------
def set_session_env_var(confdb, session_name, env_var_name: str, env_var_value:str ):
    """
    Sets the value of an environment variable in the specified Session of the
    specified configuratiion database file
    """
    if session_name == "":
        print(f"Error: the session name needs to be specified")
        return
    else:
        try:
            session = confdb.get_dal("Session", session_name)
        except:
            print(f"Error could not find Session {session_name} in file {oksfile}")
            return

    dal_name = "session-env-" + env_var_name
    dal_name = dal_name.lower()
    dal_name = dal_name.replace("_", "-")

    schemafiles = [
        "schema/confmodel/dunedaq.schema.xml"
    ]
    dal = conffwk.dal.module("dal", schemafiles)
    new_or_updated_env = dal.Variable(dal_name, name=env_var_name, value=env_var_value)
    confdb.update_dal(new_or_updated_env)

    if not new_or_updated_env in session.environment:
        session.environment.append(new_or_updated_env)
        confdb.update_dal(session)

    confdb.commit()