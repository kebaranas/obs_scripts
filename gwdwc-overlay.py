import obspython as obs
import serial, threading, time, os, json
from serial.tools import list_ports
from datetime import datetime

port_name = ""
baud_rate = 9600
depth_val = ""
clock_val = ""
debug_info = ""
t1 = None
t2 = None
t3 = None
port = None
stop_t1 = False
clicked = False
strt_rc_clicked = False
file_name = ""

class TextContent:
    def __init__(self, source_name=None, text_string="NaN"):
        self.source_name = source_name
        self.text_string = text_string
    
    def update_text(self, text):
        source = obs.obs_get_source_by_name(self.source_name)
        settings = obs.obs_data_create()
        self.text_string = text
        obs.obs_data_set_string(settings, "text", self.text_string)
        obs.obs_source_update(source, settings)
        obs.obs_data_release(settings)
        obs.obs_source_release(source)

depth_text = TextContent()
clock_text = TextContent()
debug_text = TextContent()
idf_text = TextContent()
wo_text = TextContent()
wi_text = TextContent()
wcd_text = TextContent()
wcs_text = TextContent()
loc_text = TextContent()
cn_text = TextContent()
cc_text = TextContent()
tech_text = TextContent()
crd_text = TextContent()
alt_text = TextContent()

def script_properties():
    props = obs.obs_properties_create()
    port_source = obs.obs_properties_add_list(
        props,
        "port_source",
        "Port",
        obs.OBS_COMBO_TYPE_LIST,
        obs.OBS_COMBO_FORMAT_STRING
    )
    baud_rate_source = obs.obs_properties_add_list(
        props,
        "baud_rate_source",
        "Baud Rate",
        obs.OBS_COMBO_TYPE_EDITABLE,
        obs.OBS_COMBO_FORMAT_STRING
    )
    depth_text_source = obs.obs_properties_add_list(
        props,
        "depth_text_source",
        "Depth Text",
        obs.OBS_COMBO_TYPE_LIST,
        obs.OBS_COMBO_FORMAT_STRING
    )
    clock_text_source = obs.obs_properties_add_list(
        props,
        "clock_text_source",
        "Clock Text",
        obs.OBS_COMBO_TYPE_LIST,
        obs.OBS_COMBO_FORMAT_STRING
    )
    debug_text_source = obs.obs_properties_add_list(
        props,
        "debug_text_source",
        "Debug Text",
        obs.OBS_COMBO_TYPE_LIST,
        obs.OBS_COMBO_FORMAT_STRING
    )
    
    obs.obs_properties_add_button(props, "start_btn", "Start", start)
    obs.obs_properties_add_button(props, "stop_btn", "Stop", stop)
    
    identifier_tag = obs.obs_properties_add_text(
        props,
        "identifier_tag",
        "Identifier Tag",
        obs.OBS_TEXT_DEFAULT
    )
    well_owner = obs.obs_properties_add_text(
        props,
        "well_owner",
        "Well Owner",
        obs.OBS_TEXT_DEFAULT
    )
    well_id = obs.obs_properties_add_text(
        props,
        "well_id",
        "Well ID",
        obs.OBS_TEXT_DEFAULT
    )
    well_casing_diameter = obs.obs_properties_add_text(
        props,
        "well_casing_diameter",
        "Well Casing Diameter",
        obs.OBS_TEXT_DEFAULT
    )
    well_casing_stickup = obs.obs_properties_add_text(
        props,
        "well_casing_stickup",
        "Well Casing StickUp",
        obs.OBS_TEXT_DEFAULT
    )
    location_info = obs.obs_properties_add_text(
        props,
        "location_info",
        "Location",
        obs.OBS_TEXT_DEFAULT
    )
    client_person = obs.obs_properties_add_text(
        props,
        "client_person",
        "Client Name",
        obs.OBS_TEXT_DEFAULT
    )
    client_company = obs.obs_properties_add_text(
        props,
        "client_company",
        "Company Name",
        obs.OBS_TEXT_DEFAULT
    )
    technicians = obs.obs_properties_add_text(
        props,
        "technicians",
        "Technicians",
        obs.OBS_TEXT_DEFAULT
    )
    coordinates = obs.obs_properties_add_text(
        props,
        "coordinates",
        "Coordinates",
        obs.OBS_TEXT_DEFAULT
    )
    altitude = obs.obs_properties_add_text(
        props,
        "altitude",
        "Altitude",
        obs.OBS_TEXT_DEFAULT
    )

    ports = list_ports.comports()
    if ports is not None:
        for port in ports:
            obs.obs_property_list_add_string(port_source, port.device, port.device)

    baud_rate_tuple = ("9600", "19200", "38400", "57600", "74880", "115200")
    for baud_rate in baud_rate_tuple:
        obs.obs_property_list_add_string(baud_rate_source, str(baud_rate), baud_rate)
    
    sources = obs.obs_enum_sources()
    if sources is not None:
        for source in sources:
            source_id = obs.obs_source_get_unversioned_id(source)
            if source_id == "text_gdiplus" or source_id == "text_ft2_source":
                name = obs.obs_source_get_name(source)
                obs.obs_property_list_add_string(depth_text_source, name, name)
                obs.obs_property_list_add_string(clock_text_source, name, name)
                obs.obs_property_list_add_string(debug_text_source, name, name)

        obs.source_list_release(sources)
    
    obs.obs_properties_add_button(props, "strt_record_btn", "Start Recording", strt_record)
    obs.obs_properties_add_button(props, "stp_record_btn", "Stop Recording", stp_record)
    return props

def script_update(settings):
    global port_name, baud_rate
    port_name = obs.obs_data_get_string(settings, "port_source")
    baud_rate = obs.obs_data_get_string(settings, "baud_rate_source")
    depth_text.source_name = obs.obs_data_get_string(settings, "depth_text_source")
    clock_text.source_name = obs.obs_data_get_string(settings, "clock_text_source")
    debug_text.source_name = obs.obs_data_get_string(settings, "debug_text_source")
    idf_text.source_name = obs.obs_data_get_string(settings, "identifier_tag")
    wo_text.source_name = obs.obs_data_get_string(settings, "well_owner")
    wi_text.source_name = obs.obs_data_get_string(settings, "well_id")
    wcd_text.source_name = obs.obs_data_get_string(settings, "well_casing_diameter")
    wcs_text.source_name = obs.obs_data_get_string(settings, "well_casing_stickup")
    loc_text.source_name = obs.obs_data_get_string(settings, "location_info")
    cn_text.source_name = obs.obs_data_get_string(settings, "client_person")
    cc_text.source_name = obs.obs_data_get_string(settings, "client_company")
    tech_text.source_name = obs.obs_data_get_string(settings, "technicians")
    crd_text.source_name = obs.obs_data_get_string(settings, "coordinates")
    alt_text.source_name = obs.obs_data_get_string(settings, "altitude")
    
def start(props, prop):
    global port, t1, stop_t1, t2,clicked, strt_rc_clicked
    if clicked:
        return
    try:
        port = serial.Serial(port_name, int(baud_rate))
        if strt_rc_clicked:
            t2 = threading.Thread(target=update_con)
            t2.start()
        else:    
            debug_text.update_text(f"Connected to {port_name}")
        dprint(f"Connected to {port_name}")
        t1 = threading.Thread(target=update_values)
        stop_t1 = False
        t1.start()
        obs.timer_remove(update_ui)
        obs.timer_add(update_ui, 100)
        clicked = True
    except serial.SerialException as e:
        debug_text.update_text(f"{e}")
        dprint(f"{e}")
    except TypeError as e:
        debug_text.update_text(f"{e}")
        dprint(f"{e}")
        port.close()

def update_con():
    debug_text.update_text(f"Connected to {port_name}")
    time.sleep(1)
    debug_text.update_text("")

def stop(props, prop):
    global port, t1, stop_t1, clicked, t2, strt_rc_clicked, depth_val
    if not port:
        debug_text.update_text("You are not connected to any port.")
        dprint("You are not connected to any port.")
        return     
    if not clicked:
        return
    try:
        stop_t1 = True
        port.close()
        t1.join()
        if strt_rc_clicked:
            t2.join()
        depth_val = ""
        depth_text.update_text("")
        debug_text.update_text(f"Disconnected from {port_name}")
        dprint(f"Disconnected from {port_name}")
        clicked = False
    except serial.SerialException as e:
        debug_text.update_text(f"{e}")
        dprint(f"{e}")

def strt_record(props, prop):
    global strt_rc_clicked, file_name
    if strt_rc_clicked:
        return
    strt_rc_clicked = True
    debug_text.update_text("")
    obs.obs_frontend_recording_start()
    time.sleep(.25)
    for file in os.listdir(obs.obs_frontend_get_current_record_output_path()):
        if file.endswith("gwdwctemp.mkv"):
            file_name = file.rsplit("gwdwctemp.mkv")

    dprint("Recording Started")

def stp_record(props, prop):
    global strt_rc_clicked, file_name, clicked
    if not strt_rc_clicked:
        return
    if clicked:
        debug_text.update_text(f"Connected to {port_name}")
    obs.obs_frontend_recording_stop()
    dprint("Recording Stopped")
    strt_rc_clicked = False
    for file in os.listdir(obs.obs_frontend_get_current_record_output_path()):
        if file.endswith("gwdwctemp.mkv"):
            os.mkdir(os.path.join(obs.obs_frontend_get_current_record_output_path(), file.rstrip("gwdwctemp.mkv") + str(idf_text.source_name).replace(" ", "")))
            old_name = os.path.join(obs.obs_frontend_get_current_record_output_path(), file)
            new_name = os.path.join(obs.obs_frontend_get_current_record_output_path() + "/" + file.rstrip("gwdwctemp.mkv") + str(idf_text.source_name).replace(" ", "") ,file.rstrip("gwdwctemp.mkv") + str(idf_text.source_name).replace(" ", "") + ".mkv")
            time.sleep(1)
            os.rename(old_name, new_name)
            dprint(f"Recording Saved: {new_name}")
            data = {
                "timestamp" : file_name[0],
                "well_owner" : wo_text.source_name,
                "well_id" : wi_text.source_name,
                "well_casing_diameter" : wcd_text.source_name,
                "well_casing_stickup" : wcs_text.source_name,
                "location" : loc_text.source_name,
                "client_person" : cn_text.source_name,
                "client_company" : cc_text.source_name,
                "technicians" : tech_text.source_name,
                "coordinates" : crd_text.source_name,
                "altitude": alt_text.source_name
            }
            json_file_path = os.path.join(obs.obs_frontend_get_current_record_output_path() + "/" + file.rstrip("gwdwctemp.mkv") + str(idf_text.source_name).replace(" ", ""), file.rstrip("gwdwctemp.mkv") + str(idf_text.source_name).replace(" ", "") + ".json" )
            with open(json_file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
    
def update_values():
    global depth_val, clock_val, stop_t1
    while True:
        if port.in_waiting:
            depth_val = str(port.readline())[2:-5]
        if stop_t1:
            break

def update_ui():
    if depth_val != "":
        depth_text.update_text(depth_val)
    

def clock_update():
    clock_val = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    clock_text.update_text(clock_val)

obs.timer_add(clock_update, 100)

def script_description():
    return "Displays the date and time from the computer, and the depth values from the serial port."

def script_load(settings):
    dprint("Script has been started")
    t3 = threading.Thread(target=update_debug)
    t3.start()

def update_debug():
    time.sleep(1)
    debug_text.update_text("")
    depth_text.update_text("")

def script_unload():
    with open (os.path.join(obs.obs_frontend_get_current_record_output_path(), "test.txt"), "w", encoding="utf-8") as f:
        f.write('obs closed')
    clock_text.update_text("")
    debug_text.update_text("")
    depth_text.update_text("")
    obs.timer_remove(update_ui)
    global port, t1, t2
    if not port:
        return     
    try:
        port.close()
        t1.join()
        if strt_rc_clicked:
            t2.join()
        t3.join()
    except serial.SerialException as e:
        debug_text.update_text(f"{e}")

def dprint(*input):
    print(*input)

