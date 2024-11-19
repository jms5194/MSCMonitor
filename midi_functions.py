from pubsub import pub
import mido
import constants
from datetime import datetime
import mido.backends.rtmidi

mido.set_backend('mido.backends.rtmidi')

midi_in = None


def available_midi_ports():
    pub.subscribe(available_midi_ports, 'refreshInterfaces')
    pub.subscribe(open_midi_port, "chosenPort")
    available_ports = list(dict.fromkeys(mido.get_input_names()))
    pub.sendMessage('availablePorts', choices=available_ports)


def open_midi_port(port_to_open):
    # Opens Midi Input Port
    global midi_in
    if midi_in is not None:
        midi_in.close()
    try:
        midi_in = mido.open_input(port_to_open, callback=midi_receive_handler)
        print("opened port")
    except Exception as e:
        print("Failed to open midi port")


def midi_receive_handler(msg):
    # Passes off incoming midi from controller to the relevant Defs
    if msg.type == "sysex":
        MSC_translator(msg)


def MSC_translator(msg):
    incoming_sysex = msg.data
    # Check for MSC:
    if incoming_sysex[0] == 127 and incoming_sysex[2] == 2:
        device_id = str(incoming_sysex[1])
        command_format = incoming_sysex[3]
        if incoming_sysex[3] in constants.COMMAND_FORMATS:
            command_format = constants.COMMAND_FORMATS[incoming_sysex[3]]
        else:
            command_format = "Invalid"
        if incoming_sysex[4] in constants.COMMAND_TYPES:
            command_type = constants.COMMAND_TYPES[incoming_sysex[4]]
        else:
            command_type = "Invalid"
        remaining_data = incoming_sysex[5:]
        size = len(remaining_data)
        # List Comprehension magic that I don't really understand:
        try:
            idx_list = [idx + 1 for idx, val in enumerate(remaining_data) if val == 0]
            res = [remaining_data[i:j] for i, j in
                   zip([0] + idx_list, idx_list + ([size] if idx_list[-1] != size else []))]
            counter = 0
            for i in res:
                if i[-1] == 0:
                    i = i[:-1]
                    res[counter] = i
                counter += 1
        except:
            res = [remaining_data]
        try:
            cue_number_data = res[0]
        except IndexError:
            cue_number_data = ""
        try:
            cue_list_data = res[1]
        except IndexError:
            cue_list_data = ""
        try:
            cue_path_data = res[2]
        except IndexError:
            cue_path_data = ""
        cue_number_hex = ""
        try:
            if cue_number_data != "":
                for i in cue_number_data:
                    cue_number_hex += hex(i)[2:]
                cue_number_bytes = bytes.fromhex(cue_number_hex)
                cue_number = cue_number_bytes.decode("ASCII")
            else:
                cue_number = ""
        except:
            cue_number = ""
        cue_list_hex = ""
        try:
            if cue_list_data != "":
                for i in cue_list_data:
                    cue_list_hex += hex(i)[2:]
                cue_list_bytes = bytes.fromhex(cue_list_hex)
                cue_list = cue_list_bytes.decode("ASCII")
            else:
                cue_list = ""
        except Exception as e:
            print(e)
            cue_list = ""
        cue_path_hex = ""
        try:
            if cue_path_data != "":
                for i in cue_path_data:
                    cue_path_hex += hex(i)[2:]
                cue_path_bytes = bytes.fromhex(cue_path_hex)
                cue_path = cue_path_bytes.decode("ASCII")
            else:
                cue_path = ""
        except:
            cue_path = ""
        current_time = datetime.now()
        timestamp_str = current_time.strftime("%d-%b-%Y (%H:%M:%S)")

        msg_to_snd = [timestamp_str, device_id, command_format, command_type, cue_number, cue_list, cue_path]
        pub.sendMessage('logUpdates', msg=msg_to_snd)
