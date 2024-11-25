from dataclasses import dataclass
from daqconf.assets import resolve_asset_file
from daqconf.utils import find_oksincludes
import conffwk
import glob
import os
from detdataformats import DetID


'''
Script to generate ND configuration. For now separated from generate.py for readability (need to recombine!)
'''

from daqconf.generate import (
                    generate_dataflow,
                    generate_hsi,
                    generate_fakedata,
                    generate_trigger,
                    generate_session
                )

def generate_readout_nd(
    readoutmap,
    oksfile,
    include,
    generate_segment,
    emulated_file_name="asset://?checksum=e96fd6efd3f98a9a3bfaba32975b476e",
    tpg_enabled=True,
    hosts_to_use=[],
):
    """
        Essentially a copy of generate_readout but with ONLY ND data files

        Simple script to create an OKS configuration file for all
        ReadoutApplications defined in a readout map.

        The file will automatically include the relevant schema files and
        any other OKS files you specify. 

        Example:
            generate_readoutOKS -i hosts \
            -i appmodel/connections.data.xml -i appmodel/moduleconfs \
            config/np04readoutmap.data.xml readoutApps.data.xml

        Will load hosts, connections and moduleconfs data files as well as
        the readoutmap (config/np04readoutmap.data.xml) and write the
        generated apps to readoutApps.data.xml.

            generate_readoutOKS --session --segment \
            -i appmodel/fsm -i hosts \
            -i appmodel/connections.data.xml -i appmodel/moduleconfs  \
            config/np04readoutmap.data.xml np04readout-session.data.xml

        Will do the same but in addition it will generate a containing
        Segment for the apps and a containing Session for the Segment.

        NB: Currently FSM generation is not implemented so you must include
        an fsm file in order to generate a Segment

    """
    

    if not readoutmap.endswith(".data.xml"):
        readoutmap = readoutmap + ".data.xml"

    print(f"Readout map file {readoutmap}")
    includefiles = [
        "schema/confmodel/dunedaq.schema.xml",
        "schema/appmodel/application.schema.xml",
        "schema/appmodel/trigger.schema.xml",
        "schema/appmodel/ndmodules.schema.xml",
        readoutmap,
    ]

    searchdirs = [path for path in os.environ["DUNEDAQ_DB_PATH"].split(":")]
    searchdirs.append(os.path.dirname(oksfile))
    for inc in include:
        # print (f"Searching for {inc}")
        match = False
        inc = inc.removesuffix(".xml")
        if inc.endswith(".data"):
            sub_dirs = ["config", "data"]
        elif inc.endswith(".schema"):
            sub_dirs = ["schema"]
        else:
            sub_dirs = ["*"]
            inc = inc + "*"
        for path in searchdirs:
            # print (f"   {path}/{inc}.xml")
            matches = glob.glob(f"{inc}.xml", root_dir=path)
            if len(matches) == 0:
                for search_dir in sub_dirs:
                    # print (f"   {path}/{search_dir}/{inc}.xml")
                    matches = glob.glob(f"{search_dir}/{inc}.xml", root_dir=path)
                    for filename in matches:
                        if filename not in includefiles:
                            print(f"Adding {filename} to include list")
                            includefiles.append(filename)
                        else:
                            print(f"{filename} already in include list")
                        match = True
                        break
                    if match:
                        break
                if match:
                    break
            else:
                for filename in matches:
                    if filename not in includefiles:
                        print(f"Adding {filename} to include list")
                        includefiles.append(filename)
                    else:
                        print(f"{filename} already in include list")
                    match = True
                    break

        if not match:
            print(f"Error could not find include file for {inc}")
            return
    
    
    dal = conffwk.dal.module("generated", includefiles)
    db = conffwk.Configuration("oksconflibs")
    if not oksfile.endswith(".data.xml"):
        oksfile = oksfile + ".data.xml"
    print(f"Creating OKS database file {oksfile}")
    db.create_db(oksfile, includefiles)
    db.set_active(oksfile)
    
    
    detector_connections = db.get_dals(class_name="DetectorToDaqConnection")

    try:
        rule = db.get_dal(
            class_name="NetworkConnectionRule", uid="data-req-readout-net-rule"
        )
    except:
        print(
            'Expected NetworkConnectionRule "data-req-readout-net-rule" not found in input databases!'
        )
    else:
        netrules = [rule]
        # Assume we have all the other rules we need
        for rule in ["tpset-net-rule", "ts-net-rule", "ta-net-rule"]:
            netrules.append(db.get_dal(class_name="NetworkConnectionRule", uid=rule))

    try:
        rule = db.get_dal(
            class_name="QueueConnectionRule", uid="nd-dlh-data-requests-queue-rule"
        )
    except:
        print(
            'Expected QueueConnectionRule "nd-dlh-data-requests-queue-rule" not found in input databases!'
        )
    else:
        qrules = [rule]
        for rule in [
            "fa-queue-rule",
            "tp-queue-rule",
        ]:
            qrules.append(db.get_dal(class_name="QueueConnectionRule", uid=rule))

    hosts = []
    if len(hosts_to_use) == 0:
        for vhost in db.get_dals(class_name="VirtualHost"):
            if vhost.id == "vlocalhost":
                hosts.append(vhost.id)
        if "vlocalhost" not in hosts:
            cpus = dal.ProcessingResource("cpus", cpu_cores=[0, 1, 2, 3])
            db.update_dal(cpus)
            phdal = dal.PhysicalHost("localhost", contains=[cpus])
            db.update_dal(phdal)
            host = dal.VirtualHost("vlocalhost", runs_on=phdal, uses=[cpus])
            db.update_dal(host)
            hosts.append("vlocalhost")
    else:
        for vhost in db.get_dals(class_name="VirtualHost"):
            if vhost.id in hosts_to_use:
                hosts.append(vhost.id)
    assert len(hosts) > 0

    rohw = dal.RoHwConfig(f"rohw-{detector_connections[0].id}")
    db.update_dal(rohw)

    opmon_conf = db.get_dal(class_name="OpMonConf", uid="slow-all-monitoring")
    appnum = 0

    nd_card = None
    ruapps = []

    for connection in detector_connections:

        det_id = 0
        
        for resource in connection.contains:
            if "ResourceSetAND" in resource.oksTypes():
                for stream in resource.contains:
                    det_id = stream.contains[0].geo_id.detector_id
                    break
                break

        # Dumb way to do this!
        if det_id == 32: #PACMAN
            # fakedata_frag_type = "PACMAN"
            # queue_frag_type = "PACMANFrame"
            linkhandler = db.get_dal(class_name="DataHandlerConf", uid="def-pac-link-handler")
        elif det_id == 33: # MPD
            # fakedata_frag_type="MPD"
            # queue_frag_type = "MPDFrame"
            linkhandler = db.get_dal(class_name="DataHandlerConf", uid="def-mpd-link-handler")
        
        else:
            raise ValueError(f"{det_id} not recognised, can only use 32 (PACMAN) and 33 (MPD)")
        
        # MPD + pacman use same handlers
        det_q = db.get_dal(class_name="QueueConnectionRule", uid="pac-eth-raw-data-rule")
        
        hostnum = appnum % len(hosts)
        # print(f"Looking up host[{hostnum}] ({hosts[hostnum]})")
        host = db.get_dal(class_name="VirtualHost", uid=hosts[hostnum])


        for resource in connection.contains:
            
            if "DetDataReceiver" in resource.oksTypes():
                receiver = resource
                break
        
            
            if type(receiver).__name__ == "PACMANReceiver":
                pass
            
            elif type(receiver).__name__ == "NDFakeReaderModule":
                if nd_card is not None:
                    continue
                
                try:
                    stream_emu = db.get_dal(
                        class_name="StreamEmulationParameters", uid="stream-emu"
                    )
                    stream_emu.data_file_name = resolve_asset_file(emulated_file_name)
                    db.update_dal(stream_emu)
                except:
                    stream_emu = dal.StreamEmulationParameters(
                        "stream-emu",
                        data_file_name=resolve_asset_file(emulated_file_name),
                        input_file_size_limit=5777280,
                        set_t0=True,
                        random_population_size=100000,
                        frame_error_rate_hz=0,
                        generate_periodic_adc_pattern=True,
                        TP_rate_per_channel=1,
                    )
                    db.update_dal(stream_emu)
                    print("Generating fake DataReaderConf")
                    nd_card = dal.PACMANDataReaderConf(
                        f"def-pac-receiver-conf",
                        template_for="NDFakeReaderModule",
                        emulation_mode=1,
                        emulation_conf=stream_emu,
                    )
                    
                    db.update_dal(nd_card)
                    db.commit()

                    # Services
                    dataRequests = db.get_dal(class_name="Service", uid="dataRequests")
                    timeSyncs = db.get_dal(class_name="Service", uid="timeSyncs")
                    # triggerActivities = db.get_dal(class_name="Service", uid="triggerActivities")
                    # triggerPrimitives = db.get_dal(class_name="Service", uid="triggerPrimitives")
                    ru_control = dal.Service(f"ru-{connection.id}_control", protocol="rest", port=0)
                    db.update_dal(ru_control)

                    # Action Plans
                    readout_start = db.get_dal(class_name="ActionPlan", uid="readout-start")
                    readout_stop = db.get_dal(class_name="ActionPlan", uid="readout-stop")

                    ru = dal.ReadoutApplication(
                        f"ru-{connection.id}",
                        application_name="daq_application",
                        runs_on=host,
                        contains=[connection],
                        network_rules=netrules,
                        queue_rules=qrules + [det_q],
                        link_handler=linkhandler,
                        data_reader=datareader,
                        opmon_conf=opmon_conf,
                        tp_generation_enabled=tpg_enabled,
                        ta_generation_enabled=tpg_enabled,
                        uses=rohw,
                        exposes_service=[ru_control, dataRequests, timeSyncs],
                        action_plans=[readout_start, readout_stop],
                    )

                    appnum = appnum + 1
                    print(f"{ru=}")
                    db.update_dal(ru)
                    db.commit()
                    ruapps.append(ru)
                if appnum == 0:
                    print(f"No ReadoutApplications generated\n")
                    return

                db.commit()

                if generate_segment:
                    # fsm = db.get_dal(class_name="FSMconfiguration", uid="fsmConf-test")
                    fsm = db.get_dal(class_name="FSMconfiguration", uid="FSMconfiguration_noAction")
                    controller_service = dal.Service(
                        "ru-controller_control", protocol="grpc", port=0
                    )
                    db.update_dal(controller_service)
                    db.commit()
                    controller = dal.RCApplication(
                        "ru-controller",
                        application_name="drunc-controller",
                        runs_on=host,
                        fsm=fsm,
                        opmon_conf=opmon_conf,
                        exposes_service=[controller_service],
                    )
                    db.update_dal(controller)
                    db.commit()

                    seg = dal.Segment(f"ru-segment", controller=controller, applications=ruapps)
                    db.update_dal(seg)
                    db.commit()

                db.commit()
                return

