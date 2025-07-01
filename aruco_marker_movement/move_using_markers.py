from detecting_markers import detect_markers
import robot_movement_new as rbm
import pickle
import os
import time
import sys

if os.path.exists("marker_presets.pkl"):
    with open("marker_presets.pkl","rb") as file:
        marker_presets=pickle.load(file)
else:
    marker_presets={}

def user_def_inputs():
    print("Create presets for markers. Type done when finished")
    while True:
        raw_input=input("Enter marker_id, done if finished, delete, or exit: ").strip()
        if raw_input.lower()=="done":
            break

        if raw_input.lower()=="exit":
            print("Exiting")
            sys.exit()

        elif raw_input.lower()=="delete":
            marker_to_be_deleted=input("Enter id of marker to be deleted: ")
            rbm.delete_marker_preset(marker_to_be_deleted)
            continue
        
        try:
            marker_id = str(int(raw_input))  # Ensure it's numeric
            x = float(input("x: "))
            y = float(input("y: "))
            z = float(input("z: "))
            rx = float(input("rx: "))
            ry = float(input("ry: "))
            rz = float(input("rz: "))
            #gripper = input("Gripper open? (yes/no): ").strip().lower() == "yes"
            rbm.create_marker_preset(marker_id, x, y, z, rx, ry, rz)
        except ValueError:
            print("Invalid input. Try again.")

def on_marker_detected(marker_id,status_holder=None):
    marker_id=str(marker_id)
    if status_holder is not None:
        status_holder["status"]="Picking up object"
    rbm.pick_up_object_gripper_closed()
    time.sleep(2)

    if status_holder is not None:
        status_holder["status"]=f"Moving to marker position {marker_id}"
    rbm.move_to_marker_preset(marker_id)
    time.sleep(1)

    preset=rbm.get_marker_preset(marker_id)
    if preset:
        drop_pose=preset.copy()
        drop_pose["open"]=True
        rbm.movement_api_call("absolute",drop_pose)
        time.sleep(2)
        rbm.pick_up_object_gripper_open()

    if status_holder is not None:
        status_holder["status"]="Returning to initial position"

if __name__=="__main__":
    stream_url="http://127.0.0.1:80/video/0"
    rbm.robot_init()
    time.sleep(1)
    #rbm.starting_position()
    rbm.pick_up_object_gripper_open()
    user_def_inputs()
    status_holder={"status":"idle"}
    detect_markers(stream_url,on_marker_detected,status_holder)
    time.sleep(3)
    rbm.pick_up_object_gripper_open()
