import conffwk
import confmodel

import re
import socket

def randomize_connectivity_service_port(oksfile, session_name, specified_port=0):
    """Script to set the value of the Connectivity Service port in the specified Session of the
    specified OKS database file to a random available port number"""
    db = conffwk.Configuration("oksconflibs:" + oksfile)
    if session_name == "":
        print(f"Error: the session name needs to be specified")
        return
    else:
        try:
            session = db.get_dal("Session", session_name)
        except:
            print(f"Error could not find Session {session_name} in file {oksfile}")
            return

    schemafiles = [
        "schema/confmodel/dunedaq.schema.xml"
    ]
    dal = conffwk.dal.module("dal", schemafiles)

    if specified_port == 0:
        def find_free_port():
            with socket.socket() as s:
                s.bind(("", 0))
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                port = s.getsockname()[1]
                s.close()
                return port

        new_port = find_free_port()
    else:
        new_port = specified_port

    session.connectivity_service.service.port = new_port
    db.update_dal(session.connectivity_service.service)

    for app in session.infrastructure_applications:
        if app.className() == "ConnectionService":
            index = 0
            for clparam in app.commandline_parameters:
                if "gunicorn" in clparam:
                    pattern = re.compile('(.*0\.0\.0\.0)\:\d+(.*)')
                    app.commandline_parameters[index] = pattern.sub(f'\\1:{new_port}\\2', clparam)
                    #print(f"{app}")
                    db.update_dal(app)
                    break
                index += 1

    db.commit()
