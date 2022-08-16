# Set moo schema search path
from dunedaq.env import get_moo_model_path
import moo.io
moo.io.default_load_path = get_moo_model_path()

# Load configuration types
import moo.otypes

moo.otypes.load_types('trigger/triggeractivitymaker.jsonnet')
moo.otypes.load_types('trigger/triggercandidatemaker.jsonnet')
moo.otypes.load_types('trigger/triggerzipper.jsonnet')
moo.otypes.load_types('trigger/moduleleveltrigger.jsonnet')
moo.otypes.load_types('trigger/timingtriggercandidatemaker.jsonnet')
moo.otypes.load_types('trigger/faketpcreatorheartbeatmaker.jsonnet')
moo.otypes.load_types('trigger/txbuffer.jsonnet')
moo.otypes.load_types('readoutlibs/readoutconfig.jsonnet')
moo.otypes.load_types('trigger/tpchannelfilter.jsonnet')

# Import new types
import dunedaq.trigger.triggeractivitymaker as tam
import dunedaq.trigger.triggercandidatemaker as tcm
import dunedaq.trigger.triggerzipper as tzip
import dunedaq.trigger.moduleleveltrigger as mlt
import dunedaq.trigger.timingtriggercandidatemaker as ttcm
import dunedaq.trigger.faketpcreatorheartbeatmaker as heartbeater
import dunedaq.trigger.txbufferconfig as bufferconf
import dunedaq.readoutlibs.readoutconfig as readoutconf
import dunedaq.trigger.tpchannelfilter as chfilter

from daqconf.core.app import App, ModuleGraph
from daqconf.core.daqmodule import DAQModule
from daqconf.core.conf_utils import Direction, Queue

from dataclasses import dataclass
from rich.console import Console

console = Console()

TP_REGION_ID = 0
TP_ELEMENT_ID = 0

TA_REGION_ID = 1
TA_ELEMENT_ID = 0

TC_REGION_ID = 2
TC_ELEMENT_ID = 0

#FIXME maybe one day, triggeralgs will define schemas... for now allow a dictionary of 4byte int, 4byte floats, and strings
moo.otypes.make_type(schema='number', dtype='i4', name='temp_integer', path='temptypes')
moo.otypes.make_type(schema='number', dtype='f4', name='temp_float', path='temptypes')
moo.otypes.make_type(schema='string', name='temp_string', path='temptypes')
moo.otypes.make_type(schema='boolean', name='temp_boolean', path='temptypes')
def make_moo_record(conf_dict,name,path='temptypes'):
    fields = []
    for pname,pvalue in conf_dict.items():
        typename = None
        if type(pvalue) == int:
            typename = 'temptypes.temp_integer'
        elif type(pvalue) == float:
            typename = 'temptypes.temp_float'
        elif type(pvalue) == str:
            typename = 'temptypes.temp_string'
        elif type(pvalue) == bool:
            typename = 'temptypes.temp_boolean'
        else:
            raise Exception(f'Invalid config argument type: {type(pvalue)}')
        fields.append(dict(name=pname,item=typename))
    moo.otypes.make_type(schema='record', fields=fields, name=name, path=path)


@dataclass
class TPLink:
    region: int
    idx: int
    def get_name(self):
        # TODO 2022-08-15: At time of writing, this name has to match
        # the one given to the TPSet link in readout_gen.py. Hopefully
        # an update to the way endpoints are linked up will fix that
        # in future
        return f"ru{self.region}_link{self.idx}"

#===============================================================================
def make_ta_chain_modules(all_tp_links, tp_links_by_region, activity_plugin, activity_config, use_channel_filter, channel_map_name, ticks_per_wall_clock_s):
    '''Make the modules needed for a set of TA makers which read the TPs
       from `all_tp_links`. Aggregate them according to
       `tp_links_by_region`. Use the TA maker plugin specified by
       `activity_plugin`, with configuration `activity_config`'''
    import temptypes
    modules = []
    # Make one heartbeatmaker per link
    for tp_link in all_tp_links:
        link_id = tp_link.get_name()
        if use_channel_filter:
            modules += [DAQModule(name = f'channelfilter_{link_id}',
                                  plugin = 'TPChannelFilter',
                                  conf = chfilter.Conf(channel_map_name=channel_map_name,
                                                       keep_collection=True,
                                                       keep_induction=False))]
        modules += [DAQModule(name = f'tpsettee_{link_id}',
                              plugin = 'TPSetTee'),
                    DAQModule(name = f'heartbeatmaker_{link_id}',
                              plugin = 'FakeTPCreatorHeartbeatMaker',
                              conf = heartbeater.Conf(heartbeat_interval=ticks_per_wall_clock_s//100))]

    for region_id, tp_links in tp_links_by_region.items():
        ## 1 zipper/TAM per region id
        # (PAR 2022-06-09) The max_latency_ms here should be
        # kept smaller than the corresponding value in the
        # downstream TAZipper. The reason is to avoid tardy
        # sets at run stop, which are caused as follows:
        #
        # 1. The TPZipper receives its last input TPSets from
        # multiple links. In general, the last time received
        # from each link will be different (because the
        # upstream readout senders don't all stop
        # simultaneously). So there will be sets on one link
        # that don't have time-matched sets on the other
        # links. TPZipper sends these unmatched sets out after
        # TPZipper's max_latency_ms milliseconds have passed,
        # so these sets are delayed by
        # "tpzipper.max_latency_ms"
        #
        # 2. Meanwhile, the TAZipper has also stopped
        # receiving data from all but one of the readout units
        # (which are stopped sequentially), and so is in a
        # similar situation. Once tazipper.max_latency_ms has
        # passed, it sends out the sets from the remaining
        # live input, and "catches up" with the current time
        #
        # So, if tpzipper.max_latency_ms >
        # tazipper.max_latency_ms, the TA inputs made from the
        # delayed TPSets will certainly arrive at the TAZipper
        # after it has caught up to the current time, and be
        # tardy. If the tpzipper.max_latency_ms ==
        # tazipper.max_latency_ms, then depending on scheduler
        # delays etc, the delayed TPSets's TAs _may_ arrive at
        # the TAZipper tardily. With tpzipper.max_latency_ms <
        # tazipper.max_latency_ms, everything should be fine.
        modules += [DAQModule(name   = f'zip_{region_id}',
                              plugin = 'TPZipper',
                              conf   = tzip.ConfParams(cardinality=len(tp_links),
                                                       max_latency_ms=100,
                                                       region_id=region_id,
                                                       element_id=TA_ELEMENT_ID)),

                    DAQModule(name   = f'tam_{region_id}',
                              plugin = 'TriggerActivityMaker',
                              conf   = tam.Conf(activity_maker=activity_plugin,
                                                geoid_region=region_id,
                                                geoid_element=0,
                                                window_time=10000,  # should match whatever makes TPSets, in principle
                                                buffer_time=10*ticks_per_wall_clock_s//1000, # 10 wall-clock ms
                                                activity_maker_config=temptypes.ActivityConf(**activity_config))),

                    DAQModule(name   = f'tasettee_region_{region_id}',
                              plugin = "TASetTee"),
                    ]
    return modules

#===============================================================================
def connect_ta_chain_modules(mgraph, all_tp_links, tp_links_by_region, use_channel_filter):
    '''Connect up the TA chain modules in mgraph. Return the list of
       endpoints that should be connected to a downstream TC maker'''
    
    for tp_link in all_tp_links:
        link_id = tp_link.get_name()

        if use_channel_filter:
            mgraph.connect_modules(f'channelfilter_{link_id}.tpset_sink', f'tpsettee_{link_id}.input', size_hint=1000)

        mgraph.connect_modules(f'tpsettee_{link_id}.output1', f'heartbeatmaker_{link_id}.tpset_source', size_hint=1000)
        mgraph.connect_modules(f'tpsettee_{link_id}.output2', f'tp_buf_zipper.input', 'tps_to_buf', size_hint=1000)

        mgraph.connect_modules(f'heartbeatmaker_{link_id}.tpset_sink', f"zip_{tp_link.region}.input", f"{tp_link.region}_tpset_q", size_hint=1000)

    downstream_outputs = []
    for region_id in tp_links_by_region.keys():
        mgraph.connect_modules(f'zip_{region_id}.output',              f'tam_{region_id}.input',             size_hint=1000)
        mgraph.connect_modules(f'tam_{region_id}.output',              f'tasettee_region_{region_id}.input', size_hint=1000)
        # output1 is connected to the downstream TC maker in connect_tc_maker()
        downstream_outputs.append(f'tasettee_region_{region_id}.output1')
        mgraph.connect_modules(f'tasettee_region_{region_id}.output2', f'ta_buf_zipper.input', "tas_to_buf", size_hint=1000)


    for tp_link in all_tp_links:
        link_id=tp_link.get_name()

        if use_channel_filter:
            mgraph.add_endpoint(f"tpsets_{link_id}_sub", f"channelfilter_{link_id}.tpset_source", Direction.IN, topic=["TPSets"])
        else:
            mgraph.add_endpoint(f"tpsets_{link_id}_sub", f'tpsettee_{link_id}.input',             Direction.IN, topic=["TPSets"])

    return downstream_outputs

#===============================================================================
def create_tc_maker(mgraph, module_name, plugin, conf, zipper_inputs: list):
    '''Create the modules for a TC maker that reads TAs from the list of
       endpoints specified by `zipper_inputs`'''
    import temptypes

    # (PAR 2022-06-09) The max_latency_ms here should be kept
    # larger than the corresponding value in the upstream
    # TPZippers. See comment below for more details
    mgraph.add_module(name = 'tazipper',
                      plugin = 'TAZipper',
                      conf = tzip.ConfParams(cardinality=len(zipper_inputs),
                                                 max_latency_ms=1000,
                                                 region_id=TC_REGION_ID,
                                                 element_id=TC_ELEMENT_ID))

    config_tcm =  tcm.Conf(candidate_maker = plugin,
                           candidate_maker_config = temptypes.CandidateConf(**conf))
    mgraph.add_module(name = f'tcm_{module_name}',
                      plugin = 'TriggerCandidateMaker',
                      conf = config_tcm)
    
#===============================================================================
def connect_tc_maker(mgraph, module_name, zipper_inputs: list):
    '''Connect up a TC maker as created by create_tc_maker() to its
       upstream TA inputs (from `zipper_inputs`) and downstream to the TC
       buffer and MLT.'''
    mgraph.add_module(name   = f'tctee_{module_name}',
                      plugin = 'TCTee')

    if zipper_inputs:
        for zipper_input in zipper_inputs:
            mgraph.connect_modules(zipper_input, f'tazipper.input', "tas_to_tazipper",      size_hint=1000)
        mgraph.connect_modules("tazipper.output", f"tcm_{module_name}.input", size_hint=1000)
        
    mgraph.connect_modules(f"tcm_{module_name}.output",    f"tctee_{module_name}.input",    f"{module_name}_input", size_hint=1000)
    mgraph.connect_modules(f"tctee_{module_name}.output1",  "mlt.trigger_candidate_source",  "tcs_to_mlt",          size_hint=1000)
    mgraph.connect_modules(f"tctee_{module_name}.output2",  "tc_buf.tc_source",              "tcs_to_buf",          size_hint=1000)


#===============================================================================
def get_buffer_conf(region_id, element_id, data_request_timeout):
    return bufferconf.Conf(latencybufferconf = readoutconf.LatencyBufferConf(latency_buffer_size = 100_000,
                                                                             region_id = region_id,
                                                                             element_id = element_id),
                           requesthandlerconf = readoutconf.RequestHandlerConf(latency_buffer_size = 100_000,
                                                                               pop_limit_pct = 0.8,
                                                                               pop_size_pct = 0.1,
                                                                               region_id = region_id,
                                                                               element_id = element_id,
                                                                               # output_file = f"output_{idx + MIN_LINK}.out",
                                                                               stream_buffer_size = 8388608,
                                                                               request_timeout_ms = data_request_timeout,
                                                                               warn_on_timeout = False,
                                                                               enable_raw_recording = False))
    
#===============================================================================
def get_trigger_app(SOFTWARE_TPG_ENABLED: bool = False,
                    FIRMWARE_TPG_ENABLED: bool = False,
                    CLOCK_SPEED_HZ: int = 50_000_000,
                    DATA_RATE_SLOWDOWN_FACTOR: float = 1,
                    RU_CONFIG: list = [],

                    ACTIVITY_PLUGIN: str = 'TriggerActivityMakerPrescalePlugin',
                    ACTIVITY_CONFIG: dict = dict(prescale=10000),

                    CANDIDATE_PLUGIN: str = 'TriggerCandidateMakerPrescalePlugin',
                    CANDIDATE_CONFIG: int = dict(prescale=10),

                    SYSTEM_TYPE = 'wib',
                    USE_HSI_INPUT = True,
                    TTCM_S1: int = 1,
                    TTCM_S2: int = 2,
                    TRIGGER_WINDOW_BEFORE_TICKS: int = 1000,
                    TRIGGER_WINDOW_AFTER_TICKS: int = 1000,
                    HSI_TRIGGER_TYPE_PASSTHROUGH: bool = False,

		    MLT_BUFFER_TIMEOUT: int = 100,
                    MLT_SEND_TIMED_OUT_TDS: bool = False,
                    MLT_MAX_TD_LENGTH_MS: int = 1000,

                    USE_CHANNEL_FILTER: bool = True,

                    CHANNEL_MAP_NAME = "ProtoDUNESP1ChannelMap",
                    DATA_REQUEST_TIMEOUT = 1000,
                    HOST="localhost",
                    DEBUG=False):
    
    # Generate schema for the maker plugins on the fly in the temptypes module
    make_moo_record(ACTIVITY_CONFIG , 'ActivityConf' , 'temptypes')
    make_moo_record(CANDIDATE_CONFIG, 'CandidateConf', 'temptypes')
    import temptypes

    # How many clock ticks are there in a _wall clock_ second?
    ticks_per_wall_clock_s = CLOCK_SPEED_HZ / DATA_RATE_SLOWDOWN_FACTOR
    
    max_td_length_ticks = MLT_MAX_TD_LENGTH_MS * CLOCK_SPEED_HZ / 1000
    
    modules = []

    # This modifies RU_CONFIG, which we probably shouldn't do, but meh
    for ru in RU_CONFIG:
        if FIRMWARE_TPG_ENABLED:
            if ru["channel_count"] > 5:
                tp_links = 2
            else:
                tp_links = 1
        elif SOFTWARE_TPG_ENABLED:
            tp_links = ru["channel_count"]
        else:
            tp_links = 0
        ru["tp_link_count"] = tp_links

    all_tp_links = []
    tp_links_by_region = {}
    if SOFTWARE_TPG_ENABLED or FIRMWARE_TPG_ENABLED:
        for ru in RU_CONFIG:
            this_tp_links = [ TPLink(region = ru["region_id"], idx = i) for i in range(ru["tp_link_count"]) ]
            tp_links_by_region[ ru["region_id"] ] = this_tp_links
            all_tp_links += this_tp_links

    console.log(f"all_tp_links: {all_tp_links}")
    console.log(f"tp_links_by_region: {tp_links_by_region}")
    
    # The total number of TP links in the system
    n_tp_links = len(all_tp_links)
        
    region_ids_set = set([ru["region_id"] for ru in RU_CONFIG])
    assert len(region_ids_set) == len(RU_CONFIG), "There are duplicate region IDs for RUs. Trigger can't handle this case. Please use --region-id to set distinct region IDs for each RU"

    # We always have a TC buffer even when there are no TPs, because we want to put the timing TC in the output file
    modules += [DAQModule(name = 'tc_buf',
                          plugin = 'TCBuffer',
                          conf = get_buffer_conf(TC_REGION_ID, TC_ELEMENT_ID, DATA_REQUEST_TIMEOUT))]
    if USE_HSI_INPUT:
        modules += [DAQModule(name   = 'tctee_ttcm',
                              plugin = 'TCTee')]

    
    if SOFTWARE_TPG_ENABLED or FIRMWARE_TPG_ENABLED:
        # Make the TP and TA buffers and their respective zippers
        modules += [DAQModule(name   = 'tp_buf_zipper',
                              plugin = 'TPZipper',
                              conf   = tzip.ConfParams(cardinality=n_tp_links,
                                                       max_latency_ms=100,
                                                       region_id=TP_REGION_ID,
                                                       element_id=TP_ELEMENT_ID)),
                    DAQModule(name   = 'tp_buf',
                              plugin = 'TPBuffer',
                              conf   = get_buffer_conf(TP_REGION_ID, TP_ELEMENT_ID, DATA_REQUEST_TIMEOUT)),
                    DAQModule(name   = 'ta_buf_zipper',
                              plugin = 'TAZipper',
                              conf   = tzip.ConfParams(cardinality=len(region_ids_set),
                                                       max_latency_ms=100,
                                                       region_id=TA_REGION_ID,
                                                       element_id=TA_ELEMENT_ID)),
                    DAQModule(name   = 'ta_buf',
                              plugin = 'TABuffer',
                              conf   = get_buffer_conf(TA_REGION_ID, TA_ELEMENT_ID, DATA_REQUEST_TIMEOUT))]

        modules += make_ta_chain_modules(all_tp_links, tp_links_by_region, ACTIVITY_PLUGIN, ACTIVITY_CONFIG, USE_CHANNEL_FILTER, CHANNEL_MAP_NAME, ticks_per_wall_clock_s)

    if USE_HSI_INPUT:
        modules += [DAQModule(name = 'ttcm',
                              plugin = 'TimingTriggerCandidateMaker',
                              conf=ttcm.Conf(s0=ttcm.map_t(signal_type=0,
                                                           time_before=TRIGGER_WINDOW_BEFORE_TICKS,
                                                           time_after=TRIGGER_WINDOW_AFTER_TICKS),
                                             s1=ttcm.map_t(signal_type=TTCM_S1,
                                                           time_before=TRIGGER_WINDOW_BEFORE_TICKS,
                                                           time_after=TRIGGER_WINDOW_AFTER_TICKS),
                                             s2=ttcm.map_t(signal_type=TTCM_S2,
                                                           time_before=TRIGGER_WINDOW_BEFORE_TICKS,
                                                           time_after=TRIGGER_WINDOW_AFTER_TICKS),
                                             hsievent_connection_name = "hsievents",
                                             hsi_trigger_type_passthrough=HSI_TRIGGER_TYPE_PASSTHROUGH))]
    
    # We need to populate the list of links based on the fragment
    # producers available in the system. This is a bit of a
    # chicken-and-egg problem, because the trigger app itself creates
    # fragment producers (see below). Eventually when the MLT is its
    # own process, this problem will probably go away, but for now, we
    # leave the list of links here blank, and replace it in
    # util.connect_fragment_producers
    modules += [DAQModule(name = 'mlt',
                          plugin = 'ModuleLevelTrigger',
                          conf=mlt.ConfParams(links=[],  # To be updated later - see comment above
					      dfo_connection=f"td_to_dfo",
                                              dfo_busy_connection=f"df_busy_signal",
                                              hsi_trigger_type_passthrough=HSI_TRIGGER_TYPE_PASSTHROUGH,
					      buffer_timeout=MLT_BUFFER_TIMEOUT,
                                              td_out_of_timeout=MLT_SEND_TIMED_OUT_TDS,
                                              td_readout_limit=max_td_length_ticks))]

    mgraph = ModuleGraph(modules)

    if USE_HSI_INPUT:
        mgraph.connect_modules("ttcm.output",         "tctee_ttcm.input",             "ttcm_input", size_hint=1000)
        mgraph.connect_modules("tctee_ttcm.output1",  "mlt.trigger_candidate_source", "tcs_to_mlt", size_hint=1000)
        mgraph.connect_modules("tctee_ttcm.output2",  "tc_buf.tc_source",             "tcs_to_buf", size_hint=1000)

    if SOFTWARE_TPG_ENABLED or FIRMWARE_TPG_ENABLED:

        ta_chain_outputs = connect_ta_chain_modules(mgraph, all_tp_links, tp_links_by_region, USE_CHANNEL_FILTER)

        create_tc_maker(mgraph, "chain", CANDIDATE_PLUGIN, CANDIDATE_CONFIG, len(ta_chain_outputs))
        connect_tc_maker(mgraph, "chain", ta_chain_outputs)

        mgraph.connect_modules("tp_buf_zipper.output", "tp_buf.tpset_source", size_hint=1000)
        mgraph.connect_modules("ta_buf_zipper.output", "ta_buf.taset_source", size_hint=1000)
        
    if USE_HSI_INPUT:
        mgraph.add_endpoint("hsievents", None, Direction.IN)
        
    mgraph.add_endpoint("td_to_dfo", None, Direction.OUT, toposort=True)
    mgraph.add_endpoint("df_busy_signal", None, Direction.IN)

    mgraph.add_fragment_producer(region=TC_REGION_ID, element=TC_ELEMENT_ID, system="DataSelection",
                                 requests_in="tc_buf.data_request_source",
                                 fragments_out="tc_buf.fragment_sink")

    if SOFTWARE_TPG_ENABLED or FIRMWARE_TPG_ENABLED:
        mgraph.add_fragment_producer(region=TP_REGION_ID, element=TP_ELEMENT_ID, system="DataSelection",
                                     requests_in="tp_buf.data_request_source",
                                     fragments_out="tp_buf.fragment_sink")
        mgraph.add_fragment_producer(region=TA_REGION_ID, element=TA_ELEMENT_ID, system="DataSelection",
                                     requests_in="ta_buf.data_request_source",
                                     fragments_out="ta_buf.fragment_sink")
                    

    trigger_app = App(modulegraph=mgraph, host=HOST, name='TriggerApp')
    
    if DEBUG:
        trigger_app.export("trigger_app.dot")

    return trigger_app

