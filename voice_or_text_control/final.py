import robot_movement as rbm
import transcript_parse as tp
import speech_to_text as stt
import time
import os
import pickle

LOG_FILE="command_log.txt"
last_transcript=None
last_parsed_data={}

def log_command(transcript,parsed_data):
    with open(LOG_FILE,'a') as f:
        f.write(f"[TRANSCRIPT] {transcript}\n")
        f.write(f"[PARSED DATA] {parsed_data}\n")
        f.write("\n")

rbm.robot_init()

print("Choose control mode:")
print("1. Text Input")
print("2. Voice Input")
mode = input("Enter 1 or 2: ").strip()

while True:
    if mode == "1":
        transcript = input("Enter commands : ")
    elif mode == "2":
        print("Say your command")
        transcript = stt.record_and_transcribe()
    else:
        print("Invalid mode selected. Exiting.")
        
    if transcript.lower() in ["repeat", "again"]:
        if last_transcript and last_parsed_data:
            transcript = last_transcript
            movement_data = last_parsed_data
            print(f"[INFO] Repeating last command")
            print(transcript)
            print(movement_data)
        else:
            print("[WARNING] No command to repeat")
            continue
    else:
        movement_data = tp.extract_commands(transcript.lower())
        print(movement_data)
        log_command(transcript, movement_data)
        last_transcript = transcript
        last_parsed_data = movement_data


    if 'Preset' in movement_data and movement_data['Preset']:
        for name,values in movement_data['Preset'].items():
            rbm.create_new_preset(
                name=name,
                x=values['x'],
                y=values['y'],
                z=values['z'],
                rx=values['rx'],
                ry=values['ry'],
                rz=values['rz'],
                gripper_pos=values['gripper_pos']
            )

    if 'Pick and place from preset' in movement_data and movement_data['Pick and place from preset']:
        if os.path.exists("presets.pkl"):
            with open("presets.pkl","rb") as file:
                pick_and_place_presets=pickle.load(file)
            
            first=True

            for key,name in movement_data['Pick and place from preset'].items():
                if name not in pick_and_place_presets:
                    continue

                if first:
                    start_preset_name=name
                    first=False
                
                else:
                    end_preset_name=name

                    rbm.gripper_open()
                    time.sleep(3)
                    rbm.move_to_preset(start_preset_name)
                    time.sleep(3)
                    rbm.gripper_close()
                    time.sleep(3)
                    rbm.move_to_preset(end_preset_name)
                    time.sleep(3)
                    rbm.gripper_open()
                    time.sleep(3)
                    rbm.robot_init()

    if 'deleted_preset' in movement_data and movement_data['deleted_preset']:
        for name_of_preset in movement_data['deleted_preset'].values():
            if name_of_preset is not None:
                rbm.delete_preset(name_of_preset)

    if 'Move to position' in movement_data and movement_data['Move to position']:
        if os.path.exists("presets.pkl"):
            with open("presets.pkl","rb") as file:
                saved_presets=pickle.load(file)

        for _, preset_data in movement_data['Move to position'].items():
            preset_name=preset_data.get("name")
            if preset_name and preset_name in saved_presets:
                print(f"[DEBUG] Moving to : {preset_name}")
                rbm.move_to_preset(preset_name)
            else:
                print(f"[WARNING] {preset_name} not found")

            time.sleep(2)
    
    if 'Move end-effector to position' in movement_data and movement_data['Move end-effector to position']:
        for step,pos in movement_data['Move end-effector to position'].items():
            pos_x=pos['x']
            pos_y=pos['y']
            pos_z=pos['z']
            angular_pos_x=pos['rx']
            angular_pos_y=pos['ry']
            angular_pos_z=pos['rz']
            gripper_position=pos['gripper_position']

            rbm.move_end_to_pos(
                pos_x,
                pos_y,
                pos_z,
                angular_pos_x,
                angular_pos_y,
                angular_pos_z,
                gripper_position
            )
            time.sleep(1.5)

    if 'Rotate' in movement_data and movement_data['Rotate']:
        joint_movement_data=[
            (v['joint_id'],v['rotation'])
            for v in movement_data['Rotate'].values()
        ]
        rbm.rotate_joints(joint_movement_data)

    if "Adjustments" in movement_data and movement_data["Adjustments"]:
        type_of_adjustment=movement_data['Adjustments']['type']
        measure_of_adjustment=movement_data['Adjustments']['rotation']
        rbm.adjustment_to_pitch_or_roll_or_wrist(type_of_adjustment,measure_of_adjustment)

    if "Adjust by joint" in movement_data and movement_data["Adjust by joint"]:
        joint_to_be_adjusted=movement_data['Adjust by joint']['joint_id']
        measure_of_adjustment=movement_data['Adjust by joint']['adjustment']
        rbm.adjustment_to_joint(joint_to_be_adjusted,measure_of_adjustment)

    if movement_data['Gripper state']==True:
        rbm.gripper_open()

    if movement_data['Gripper state']==False:
        rbm.gripper_close()

    if movement_data['Return to initial position']==True:
        rbm.robot_init()

    if "terminate" in transcript or "stop" in transcript or "exit" in transcript:
        rbm.robot_init()
        break

    if "display presets" in transcript or "show presets" in transcript:
        with open("presets.pkl",'rb') as file:
            preset_positions=pickle.load(file)
        print(preset_positions)

    if "show joint positions" in transcript or "show joints" in transcript or "show joint" in transcript:
        print("[INFO] Current joint angles: ")
        print(rbm.read_joints())
        continue

    if "help" in transcript:
        print("""
Available Voice/Text Commands:
- "Create new preset named X with coordinates and orientation"
- "Move to preset X"
- "Move to X, Y, Z and open/close the gripper"
- "Rotate joint X by Y degrees"
- "Open/Close the gripper"
- "Adjust roll/pitch by X degrees"
- "Adjust joint X by Y degrees"
- "Display presets"
- "Return to initial position"
- "Repeat" → Repeat last command
- "Help" → Show this list
- "Exit/Stop/Terminate" → End session
- "Show joint positions/joints/joint" -> display current joint positions
- "Pick and Place from coordinates" -> specify absolute coordinates for pick and place function, 
    both can also be used individually.
- "Pick and Place from preset A to preset B" -> performs pick and place function from one preset position to another
              """)
