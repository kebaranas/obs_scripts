import obspython as obs
import serial
from serial.tools import list_ports
import datetime

debug = True
parity_dict = {
    "None": serial.PARITY_NONE, 
    "Odd": serial.PARITY_ODD, 
    "Even": serial.PARITY_EVEN, 
    "Mark": serial.PARITY_MARK, 
    "Space": serial.PARITY_SPACE
}
port_name = ""
baud_rate = 9600
byte_size = 8
parity = "None"
stop_bits = 1
port = None
timeout = 1
thread = None

class TextContent:
    def __init__(self, source_name=None, text_string="NaN"):
        self.source_name = source_name
        self.text_string = text_string

    def update_text(self):
        source = obs.obs_get_source_by_name(self.source_name)
        settings = obs.obs_data_create()
        # self.text_string = f"{counter_text}{self.counter}"

        obs.obs_data_set_string(settings, "text", "shit")
        obs.obs_source_update(source, settings)
        obs.obs_data_release(settings)
        obs.obs_source_release(source)

depth_text = TextContent()
clock_text = TextContent()

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
    byte_size_source = obs.obs_properties_add_list(
        props,
        "byte_size_source",
        "Byte Size",
        obs.OBS_COMBO_TYPE_LIST,
        obs.OBS_COMBO_FORMAT_INT
    )
    parity_source = obs.obs_properties_add_list(
        props,
        "parity_source",
        "Byte Parity",
        obs.OBS_COMBO_TYPE_LIST,
        obs.OBS_COMBO_FORMAT_STRING
    )
    stop_bits_source = obs.obs_properties_add_list(
        props,
        "stop_bits_source",
        "Stop Bits",
        obs.OBS_COMBO_TYPE_LIST,
        obs.OBS_COMBO_FORMAT_FLOAT
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

    ports = list_ports.comports()
    if ports is not None:
        for port in ports:
            obs.obs_property_list_add_string(port_source, port.device, port.device)
    
    baud_rate_tuple = ("9600", "19200", "38400", "57600", "74880", "115200")
    for baud_rate in baud_rate_tuple:
        obs.obs_property_list_add_string(baud_rate_source, str(baud_rate), baud_rate)
    
    byte_size_tuple = (8, 7, 6, 5)
    for byte_size in byte_size_tuple:
        obs.obs_property_list_add_int(byte_size_source, str(byte_size), byte_size)

    for parity_key in parity_dict.keys():
        obs.obs_property_list_add_string(parity_source, parity_key, parity_key)
    
    stop_bits_tuple = (1, 1.5, 2)
    for stop_bits in stop_bits_tuple:
        obs.obs_property_list_add_float(stop_bits_source, str(stop_bits), stop_bits)
    
    sources = obs.obs_enum_sources()
    if sources is not None:
        for source in sources:
            source_id = obs.obs_source_get_unversioned_id(source)
            if source_id == "text_gdiplus" or source_id == "text_ft2_source":
                name = obs.obs_source_get_name(source)
                obs.obs_property_list_add_string(depth_text_source, name, name)
                # obs.obs_property_list_add_string(clock_text_source, name, name)

        obs.source_list_release(sources)
    
    obs.obs_properties_add_button(props, "start_btn", "Start", start)
    obs.obs_properties_add_button(props, "stop_btn", "Stop", stop)

    return props

def script_update(settings):
    global port_name, baud_rate, byte_size, parity, stop_bits
    port_name = obs.obs_data_get_string(settings, "port_source")
    baud_rate = obs.obs_data_get_string(settings, "baud_rate_source")
    byte_size = obs.obs_data_get_int(settings, "byte_size_source")
    parity = obs.obs_data_get_string(settings, "parity_source")
    stop_bits = obs.obs_data_get_int(settings, "stop_bits_source")
    hotkeys_counter_1.source_name = obs.obs_data_get_string(settings, "depth_text_source")

def start(props, prop):
    global port
    global thread
    try:
        port = serial.Serial(
            port_name, 
            int(baud_rate),
            bytesize=byte_size, 
            parity=parity_dict[parity],
            stopbits=stop_bits,
            timeout=timeout
        )
        obs.timer_add(update_depth_text, 1000)
        dprint(f"SUCCESS: Opened serial port {port_name}. Baud Rate = {baud_rate} Byte Size = {byte_size} Parity = {parity} Stop Bits = {stop_bits}")
    except serial.serialutil.SerialException:
        dprint(f"ERROR: Could not open serial port {port_name}.")
    
def stop(props, prop):
    global port
    if not port:
        return
    try:
        port.close()
        port = None
        obs.timer_remove(update_depth_text)
        dprint(f"SUCCESS: Closed serial port {port_name}.")
    except serial.serialutil.SerialException:
        dprint(f"ERROR: Could not close the serial port {port_name}.")

def update_depth_text():
    print(port.readline())
    hotkeys_counter_1.update_text("shit", 0)

def update_clock_text():
    pass

def script_description():
    return "Displays the date and time from the computer, and the depth values from the serial port."

def dprint(*input):
    if debug == True:
        print(*input)