from tracemalloc import start
import obspython, serial, time, os, json
from serial.tools import list_ports
from datetime import datetime

isConnected = False
isRecording = False

attached_source_name_depth = None
attached_source_name_datetime = None
attached_source_name_debug = None

def startup():
    source_text_show(attached_source_name_debug)
    source_update()
    port_connect()
    obspython.remove_current_callback()

def console(*arg):
    print("gwdwc:", *arg)

def debug(*arg):
    source_text_modify(attached_source_name_debug, str(*arg))

def port_list():
    ports = list_ports.comports()
    if ports is not None:
        console("Serial ports:")
        for port in ports:
            console(port.device)
    else:
        console("No serial port found")
        debug("No serial port found")

def port_connect():
    global port_connection, attached_port

    port = obspython.obs_data_get_string(settings, "port")
    baud_rate = obspython.obs_data_get_string(settings, "baud_rate")
    
    try:
        port_connection = serial.Serial(port, int(baud_rate))
    except:
        if not port_connection.is_open:
            console(f"Failed connecting to port {port}")
            debug(f"Failed connecting to port {port}")
    else:
        attached_port = port
        console(f"Connected to port {attached_port}")
        debug(f"Connected to port {attached_port}")
        source_depth_reset()
        obspython.timer_add(event_loop, 125)

def port_disconnect():
    if port_connection.is_open:
        obspython.timer_remove(event_loop)
        port_connection.close()
        source_clear()
        console(f"Disconnected from port {attached_port}")
        debug(f"Disconnected from port {attached_port}")

def event_loop():
    if (port_connection.in_waiting > 0):
        text = port_connection.readline()
        text = str(text)[2:-5]
        source_text_modify(attached_source_name_depth, text)
    source_text_modify(attached_source_name_datetime, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

def source_text_modify(source_name, text):
    if source_name is None:
        return

    source = obspython.obs_get_source_by_name(source_name)
    settings = obspython.obs_data_create()

    obspython.obs_data_set_string(settings, "text", text)
    obspython.obs_source_update(source, settings)
    obspython.obs_data_release(settings)
    obspython.obs_source_release(source)

def source_text_hide(source_name):
    if source_name is None:
        return
        
    source = obspython.obs_get_source_by_name(source_name)
    
    obspython.obs_source_set_enabled(source, False)

def source_text_show(source_name):
    if source_name is None:
        return
        
    source = obspython.obs_get_source_by_name(source_name)
    
    obspython.obs_source_set_enabled(source, True)

def source_update():
    global attached_source_name_depth, attached_source_name_datetime, attached_source_name_debug

    attached_source_name_depth = obspython.obs_data_get_string(settings, "depth_text_source")
    attached_source_name_datetime = obspython.obs_data_get_string(settings, "datetime_text_source")
    attached_source_name_debug = obspython.obs_data_get_string(settings, "debug_text_source")

    source_text_modify(attached_source_name_depth, "Depth: ---.--m ----.--ft")
    source_text_modify(attached_source_name_datetime, "0000-00-00 00:00:00")
    source_text_modify(attached_source_name_debug, "Geowork Deep Well Camera")

def source_clear():
    global attached_source_name_depth, attached_source_name_datetime

    attached_source_name_depth = obspython.obs_data_get_string(settings, "depth_text_source")
    attached_source_name_datetime = obspython.obs_data_get_string(settings, "datetime_text_source")

    source_text_modify(attached_source_name_depth, "Depth: ---.--m ----.--ft")
    source_text_modify(attached_source_name_datetime, "0000-00-00 00:00:00")

def source_debug_hide():
    global attached_source_name_debug

    attached_source_name_debug = obspython.obs_data_get_string(settings, "debug_text_source")

    source_text_modify(attached_source_name_debug, "")

def source_depth_reset():
    global attached_source_name_depth

    attached_source_name_depth = obspython.obs_data_get_string(settings, "depth_text_source")

    source_text_modify(attached_source_name_depth, "Depth: 0.00m 0.00ft")

def json_write():
    #   Create project folder
    #   Create json file in the project folder
    #   Rename temp recording
    #   Move recording
    output_dir_path =  obspython.obs_frontend_get_current_record_output_path()
    for file in os.listdir(output_dir_path):
        output_file_path = os.path.join(output_dir_path, file)
        if not os.path.isdir(output_file_path):
            file_partition = file.partition('-')
            #   file_partition[0]   timestamp
            #   file_partition[1]   '-'
            #   file_partition[2]   gwdwctemp.mkv
            if file_partition[2] == "gwdwctemp.mkv":
                identifier = obspython.obs_data_get_string(settings, "identifier")

                if identifier == "":
                    identifier = "gwdwcproject"

                output_subdir_path = os.path.join(output_dir_path, file_partition[0] + '-' + identifier)

                #   Create project directory
                os.mkdir(output_subdir_path)

                #   Create metadata json file
                metadata = {
                    "timestamp": file_partition[0],
                    "identifier": obspython.obs_data_get_string(settings, "identifier"),
                    "well_owner": obspython.obs_data_get_string(settings, "well_owner"),
                    "well_id": obspython.obs_data_get_string(settings, "well_id"),
                    "well_casing_diameter": obspython.obs_data_get_string(settings, "well_casing_diameter"),
                    "well_casing_stickup": obspython.obs_data_get_string(settings, "well_casing_stickup"),
                    "location": obspython.obs_data_get_string(settings, "location"),
                    "client_person": obspython.obs_data_get_string(settings, "client_person"),
                    "client_company": obspython.obs_data_get_string(settings, "client_company"),
                    "technicians": obspython.obs_data_get_string(settings, "technicians"),
                    "coordinates": obspython.obs_data_get_string(settings, "coordinates"),
                    "altitude": obspython.obs_data_get_string(settings, "altitude")
                }
                
                metadata_file_path = os.path.join(output_subdir_path, file_partition[0] + '-' + identifier + ".json")

                metadata_file = open(metadata_file_path, "w", encoding="utf-8")
    
                json.dump(metadata, metadata_file, ensure_ascii=False, indent=4)
                
                # Rename and move output file to respective project directory
                new_output_file_path = os.path.join(output_subdir_path, file_partition[0] + '-' + identifier + ".mkv")
                
                os.rename(output_file_path, new_output_file_path)

# BUTTONS
def button_port_list(props, prop):
    port_list()
    debug("Open script log for available ports")
    
def button_port_connect(props, prop):
    port_connect()

def button_port_disconnect(props, prop):
    port_disconnect()
    
def button_source_update(props, prop):
    json_write()
    if not port_connection.is_open and not obspython.obs_frontend_recording_active():
        source_update()

def button_record_start(props, prop):
    if not obspython.obs_frontend_recording_active():
        obspython.obs_frontend_recording_start()
        source_text_hide(attached_source_name_debug)

def button_record_stop(props, prop):
    if obspython.obs_frontend_recording_active():
        obspython.obs_frontend_recording_stop()
        source_text_show(attached_source_name_debug)


# OBS SCRIPT FUNCTIONS
def script_load(settings):
    console("Geowork Deep Well Camera, Geowork Enterprise")
    obspython.timer_add(startup, 1000)
    
def script_unload():
    pass

def script_save(settings):
    pass

def script_defaults(settings):
    pass

def script_update(_settings):
    global settings
    settings = _settings

def script_properties():
    global prop_port

    props = obspython.obs_properties_create()

    #   OBS SOURCES
    prop_depth_text_source = obspython.obs_properties_add_text(
        props,
        "depth_text_source",
        "Depth Text Source:",
        obspython.OBS_TEXT_DEFAULT
    )

    prop_datetime_text_source = obspython.obs_properties_add_text(
        props,
        "datetime_text_source",
        "Date & Time Text Source:",
        obspython.OBS_TEXT_DEFAULT
    )

    prop_debug_text_source = obspython.obs_properties_add_text(
        props,
        "debug_text_source",
        "Debug Text Source",
        obspython.OBS_TEXT_DEFAULT
    )

    obspython.obs_properties_add_button(props, "sources_update", "Update", button_source_update)

    #   SERIAL PORT CONFIGURATION
    prop_port = obspython.obs_properties_add_text(
        props,
        "port",
        "Port:",
        obspython.OBS_TEXT_DEFAULT
    )

    prop_baud_rate = obspython.obs_properties_add_text(
        props,
        "baud_rate",
        "Baud Rate:",
        obspython.OBS_TEXT_DEFAULT
    )

    obspython.obs_properties_add_button(props, "port_list", "List Ports", button_port_list)
    obspython.obs_properties_add_button(props, "port_connect", "Connect", button_port_connect)
    obspython.obs_properties_add_button(props, "port_disconnect", "Disconnect", button_port_disconnect)

    #   WELL DETAILS
    prop_identifier_tag = obspython.obs_properties_add_text(
        props,
        "identifier",
        "Identifier",
        obspython.OBS_TEXT_DEFAULT
    )

    prop_well_owner = obspython.obs_properties_add_text(
        props,
        "well_owner",
        "Well Owner",
        obspython.OBS_TEXT_DEFAULT
    )

    prop_well_id = obspython.obs_properties_add_text(
        props,
        "well_id",
        "Well ID",
        obspython.OBS_TEXT_DEFAULT
    )

    prop_well_casing_diameter = obspython.obs_properties_add_text(
        props,
        "well_casing_diameter",
        "Well Casing Diameter",
        obspython.OBS_TEXT_DEFAULT
    )

    prop_well_casing_stickup = obspython.obs_properties_add_text(
        props,
        "well_casing_stickup",
        "Well Casing Stick-up",
        obspython.OBS_TEXT_DEFAULT
    )

    prop_location = obspython.obs_properties_add_text(
        props,
        "location",
        "Location",
        obspython.OBS_TEXT_DEFAULT
    )

    prop_client_person = obspython.obs_properties_add_text(
        props,
        "client_person",
        "Client Name",
        obspython.OBS_TEXT_DEFAULT
    )

    prop_client_company = obspython.obs_properties_add_text(
        props,
        "client_company",
        "Company Name",
        obspython.OBS_TEXT_DEFAULT
    )

    prop_technicians = obspython.obs_properties_add_text(
        props,
        "technicians",
        "Technician/s",
        obspython.OBS_TEXT_DEFAULT
    )

    prop_coordinates = obspython.obs_properties_add_text(
        props,
        "coordinates",
        "Coordinates",
        obspython.OBS_TEXT_DEFAULT
    )

    prop_altitude = obspython.obs_properties_add_text(
        props,
        "altitude",
        "Altitude",
        obspython.OBS_TEXT_DEFAULT
    )

    obspython.obs_properties_add_button(props, "record_start", "Start Recording", button_record_start)
    obspython.obs_properties_add_button(props, "record_stop", "Stop Recording", button_record_stop)

    return props

