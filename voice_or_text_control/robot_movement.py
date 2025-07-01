import requests
import pickle
import os
import time

pi_ip="127.0.0.1"
pi_port=80

last_written_angles = [0] * 6

#API call function to move robot to absolute position  
def movement_api(endpoint:str,data:dict={}):
    url=f"http://{pi_ip}:{pi_port}/move/{endpoint}"
    try:
        print(f"[DEBUG] Sending POST to {url} with data: {data}")
        response = requests.post(url, json=data)
        print(f"[DEBUG] Response: {response.status_code} - {response.text}")
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] API call failed: {e}")
        return {}

#Initializing the robot   
def robot_init():
    movement_api("init")
    
    global last_written_angles
    joint_positions=[0]*6
    last_written_angles=joint_positions.copy()

#Defining preset positions
PRESET_FILE="presets.pkl"
if os.path.exists(PRESET_FILE):
    with open(PRESET_FILE,"rb") as f:
        preset=pickle.load(f)
else:
    preset={}

#Function to set and add new presets
def create_new_preset(name:str, x, y, z, rx, ry, rz, gripper_pos:bool):
    if name in preset:
        print(f"[WARNING] Overwriting existing preset '{name}'.")

    preset[name] = {
        "x": x, 
        "y": y, 
        "z": z,
        "rx": rx, 
        "ry": ry, 
        "rz": rz,
        "open": gripper_pos
    }
    print(f"[INFO] Preset '{name}' added.")

    with open(PRESET_FILE,"wb") as f:
        pickle.dump(preset,f)

#Function to delete existing presets
def delete_preset(name:str):
    if name in preset:
        del preset[name]
        with open(PRESET_FILE,"wb") as file:
            pickle.dump(preset,file)
        print(f"[INFO] {name} was deleted")
    else:
        print(f"[WARNING] Preset {name} does not exist")

#Moving robot to preset positions
def move_to_preset(name:str):
    if name in preset:
        print(f"[INFO] Moving to {name}")
        movement_api("absolute",preset[name])
    elif name not in preset:
        print (f'[WARNING] {name} does not exist')
    else:
        print(f"[ERROR] Unable to move to {name}")

    global last_written_angles
    last_written_angles=read_joints()

#Moving end to position as given by user
def move_end_to_pos(pos_x,pos_y,pos_z,angular_pos_x,angular_pos_y,angular_pos_z,gripper_position:bool):
    movement_api("absolute",{
        "x":pos_x,
        "y":pos_y,
        "z":pos_z,
        "rx":angular_pos_x,
        "ry":angular_pos_y,
        "rz":angular_pos_z,
        "open":gripper_position
    })

    global last_written_angles
    last_written_angles=read_joints()

#Reading current joint positions
def read_joints():
    try:
        url = f"http://{pi_ip}:{pi_port}/joints/read"
        response = requests.post(url)
        response.raise_for_status()
        data = response.json()

        if "angles" in data and isinstance(data["angles"], list):
            pi = 3.14159
            angles_deg = []
            for i, rad in enumerate(data["angles"]):
                if rad is not None:
                    angles_deg.append(round((rad * 180) / pi, 2))
                else:
                    print(f"[WARNING] Joint angle {i} is None. Using 0 as fallback.")
                    angles_deg.append(0.0)
            return angles_deg
        else:
            print("[ERROR] 'angles' key not found or invalid in joint state response.")
            return [0] * 6

    except requests.RequestException as e:
        print(f"[ERROR] Failed to read joint angles: {e}")
        return [0] * 6

#Rotating joints
def rotate_joints(updates):
    global last_written_angles
    joint_position=last_written_angles.copy()

    for joint_id, angular_pos_update in updates:
        idx = joint_id - 1 
        joint_position[idx] = angular_pos_update

    last_written_angles=joint_position.copy()

    angles_rad = [(deg * 3.14159) / 180 for deg in joint_position]

    data = {
        "angles": angles_rad,
        "unit": "rad"
    }
    url = f"http://{pi_ip}:{pi_port}/joints/write"
    print(f"[DEBUG] Direct write: {data}")

    last_written_angles=joint_position.copy()

    return requests.post(url, json=data).json()

#Opening or closing the end gripper
def gripper_open():
    joint_position=read_joints()
    joint_position[5]=90
    return rotate_joints([(i+1,joint_position[i]) for i in range(6)])

def gripper_close():
    joint_position=read_joints()
    joint_position[5]=-10
    return rotate_joints([(i+1,joint_position[i]) for i in range(6)])

#Adjusting roll/pitch/wrist
def adjustment_to_pitch_or_roll_or_wrist(adjustment_type:str,adjustment_value:int):
    joint_positions_prev=read_joints()
    
    if(adjustment_type=='roll'):
        joint_positions_new=joint_positions_prev.copy()
        joint_positions_new[0]+=adjustment_value
        return rotate_joints([(i+1,joint_positions_new[i]) for i in range (6)])
    if(adjustment_type=='pitch'):
        joint_positions_new=joint_positions_prev.copy()
        joint_positions_new[2]+=adjustment_value
        return rotate_joints([(i+1,joint_positions_new[i]) for i in range (6)])
    if(adjustment_type=='wrist'):
        joint_positions_new=joint_positions_prev.copy()
        joint_positions_new[4]+=adjustment_value
        return rotate_joints([(i+1,joint_positions_new[i]) for i in range (6)])

#Adjusting specific joints/incremental joint movements 
def adjustment_to_joint(joint_id:int, value_of_adjustment:int):
    joint_positions_current=read_joints()
    joint_position_new=joint_positions_current.copy()
    joint_position_new[joint_id-1]+=value_of_adjustment
    return rotate_joints([(i+1,joint_position_new[i]) for i in range (6)])