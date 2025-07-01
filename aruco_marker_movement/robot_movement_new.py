import requests
import pickle
import os
import json

pi_ip="127.0.0.1"
pi_port=80

CONFIG_FILE="initial_config.json"
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE,"r") as file:
        config=json.load(file)
else:
    print("[WARNING] config.json not found")
    config={}        

def movement_api_call(endpoint:str,data:dict={}):
    url=f"http://{pi_ip}:{pi_port}/move/{endpoint}"
    try:
        print(f"[DEBUG] Sending data to {url}: {data}")
        response=requests.post(url,json=data)
        print(f"[DEBUG] Response: {response.status_code} - {response.text}")
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] API call failed: {e}")
        return {}
    
def initialize_robot():
    response=movement_api_call("init")

MARKER_PRESET_FILE="marker_presets.pkl"
if os.path.exists(MARKER_PRESET_FILE):
    with open (MARKER_PRESET_FILE,"rb") as file:
        marker_movement_presets=pickle.load(file)

else:
    marker_movement_presets={}

def robot_init():
    response=movement_api_call("init")

def pick_up_object_gripper_open():
    movement_api_call("absolute",config.get("pickup_pos_open",{}))

def pick_up_object_gripper_closed():
    movement_api_call("absolute",config.get("pickup_pos_closed",{}))

def create_marker_preset(marker_id:str,x,y,z,rx,ry,rz):
    if marker_id in marker_movement_presets:
        print(f"[WARNING] Overwriting existing marker {marker_id} preset")
    
    marker_movement_presets[marker_id] = {
        "x": x, 
        "y": y, 
        "z": z,
        "rx": rx, 
        "ry": ry, 
        "rz": rz,
        "open": False
    }
    print(f"[INFO] Preset for marker '{marker_id}' added.")

    with open(MARKER_PRESET_FILE,"wb") as f:
        pickle.dump(marker_movement_presets,f)

def delete_marker_preset(marker_id:str):
    if marker_id in marker_movement_presets:
        del marker_movement_presets[marker_id]
        with open(MARKER_PRESET_FILE,"wb") as file:
            pickle.dump(marker_movement_presets,file)

        print(f"[INFO] Preset for marker {marker_id} was deleted")
    else:
        print(f"[WARNING] Preset for marker {marker_id} not found")

def move_to_marker_preset(name:str):
    if name in marker_movement_presets:
        print(f"[INFO] Moving to {name}")
        movement_api_call("absolute",marker_movement_presets[name])
    elif name not in marker_movement_presets:
        print (f'[WARNING] {name} does not exist')
    else:
        print(f"[ERROR] Unable to move to {name}")

def get_marker_preset(marker_id:str):
    return marker_movement_presets.get(marker_id,None)