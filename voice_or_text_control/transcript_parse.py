import google.generativeai as genai
from dotenv import load_dotenv
import os
import ast

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def extract_commands(transcript:str):
    model=genai.GenerativeModel("gemini-2.0-flash")
    prompt= f"""
You are an AI that is responsible for extracting struct robot movement commands from natual language transcripts.
The commands can be as follows:
- create new preset named X with x equal to X, y equal to Y, z equal to Z, rx equal to RX, ry equal to RY, rz equal to RZ,
and gripper position as either true or false
- move to position/preset X
- move/go to x,y,z/x equal to X, y equal to Y, z equal to Z and open/close the gripper
- rotate joint-1, joint-2, joint-3, joint-4, joint-5, joint-6 by X degrees
- open/close gripper/end effector

Return the extracted data in the form of a usable python dictionary with following format:
-Preset: The data should be in this format
         {{"name": name
        "x": x, "y": y, "z": z,
        "rx": rx, "ry": ry, "rz": rz,
        "gripper_pos": gripper_pos
    }}

-Move to position:
{{
        "name":name of preset moving to
        "x":x,"y":y,"z":z,
        "rx":0,"ry":0,"rz":0,
        "open":gripper_position
    }}
When moving to a preset:
- If x/y/z are not mentioned, use values from the preset.
- If gripper state is not mentioned, use the preset's gripper_pos as "open".
Reserve this only for moving to presets if they are created otherwise default to "Move end-effector to position"
- If move to preset is not required, output empty dictionary.
- If there are multiple presets and movement is requested to both sequentially, output in the form where the preset to which
movement hsa been requested first has the key 1, the second to which movement has been requested has key 2 etc. If movement
to only 1 preset has been requested, keep key 1


-Rotate:
{{
    "joint_id": joint id,
    "rotation": rotation in degrees
}}
If there are multiple rotate commands, put them in a single dictionary, with keys naming them as 1,2,3 etc.
If there a rotate wrist command, rotate joint 5 by X degrees.
If there is a command to open gripper by X degrees, rotate joint 6 by X degrees.

- Adjustments:
If there is a command to rotate about z-axis by X degrees or to change yaw by X degrees, rotate joint 1 by X degrees
If there is a command to rotate about x-axis by X degrees or to change roll by X degrees, rotate joint 3 by X degrees
If there is a command to rotate wrist by X degrees, rotate joint 5 by X degrees
The format should be:
{{
    "type": yaw/roll/wrist,
    "rotation": rotation in degrees
}}

- Adjust by joint: if this is called, return the data in this format
{{"joint_id": joint to be adjusted,"adjustment":  degrees of adjustment}}

-Move end-effector to position: 
{{
        "x":pos_x,"y":pos_y,"z":pos_z,
        "rx":angular_pos_x,"ry":angular_pos_y,"rz":angular_pos_z,
        "gripper_position":gripper_position
}}
If no command is given with regards to Move end-effector,
the dictionary 'Move end-effector to position' should be empty, not x:0,y:0,z:0
with gripper_position as the variable representing whether the gripper is open or close, with True for open or False for close
If move end-effector command is called multiple times, output them inside a single 'Move end-effector to' dictionary
with keys "1","2","3" etc. If only a single command is passed in the move end-effector, the key should always be 1.
If the instruction is to move forward, sideways or up by X, put this into the move end-effector to position key, adjusting
x for forward, y for sideways, and z for up. 
If the user tells to grab something, open the gripper i.e. set gripper position to true, then reset it to false while keeping 
the other parameters same. You can label them as "1" and "2" like you do with multiple move end-effector commands but only change
the gripper position, nothing else.

- Adjust position: if adjust position is called, put the data in this key. Follow the same format as given in 
"Move end-effector to position". Give only the values given by the user in this key. Do NOT add them to the values stored
in "Move end-effector to position"
If the user says to move forward by X, put 'x' as X in the key while keeping rest of the parameters as 0.0.
If the user says to move back by X, put 'x' as -X in the key while keeping rest of the parameters as 0.0.
If the user says to move left by Y, put 'y' as Y in the key while keeping rest of the parameters as 0.0.
If the user says to move right by Y, put 'y' as _Y in the key while keeping rest of the parameters as 0.0.
If the user says to move up by Z, put 'z' as Z in the key while keeping rest of the parameters as 0.0.
If the user says to move down by Z, put 'z' as -Z in the key while keeping rest of the parameters as 0.0.
If two commands reagarding adjustment are called back to back, put them in a single 'Adjust position' dictionary 
with keys "1","2","3" etc. If only a single command is passed in the move end-effector, the key should always be 1.

-Gripper state: either opening or closing the gripper, return True for open and False for close.
Return None for gripper state if it is not explicitly called

- Return to initial position - return this as a boolean containing true or false. do the same if the user calls for return 
to starting/rest position
- Adjust by joint: if this is called, return the data in this format
{{"joint_id: ,"adjustment: "}}

If there is a preset, suppose Preset X to be deleted give an output in string "{{name of preset}}", 
with key as deleted_preset. Still include the contents of the deleted preset in the "Preset" dictionary.
if multiple presets are being deleted show both their names so that first preset to be deleted is labelled as 1 in the dict,
the second is labelled 2 and so on.
If only one delete command is given, label it 1 regardless of the number of commands given, like this:
{{{{'deleted_preset': {{'1': 'position 1'}}}}}},

If user gives a command such as "move to X,Y,Z. mark this as position X.", create a new preset and also 
include these coordinates in the move to preset section.

Return the extracted data as a single, flat Python dictionary. 
If there are multiple preset commands, include them inside a single "Preset" dictionary, 
where the keys are the preset names (e.g., "position-1", "position-2"), and the values are dictionaries with the structure:
{{
  "x": float,
  "y": float,
  "z": float,
  "rx": float,
  "ry": float,
  "rz": float,
  "gripper_pos": bool
}}

- Pick and place from preset:
If the user calls pick and place from one position to another, add them sequentially in this
eg. 1:"position 1",2:"position 2" and so on.
If the user gives direct coordinates, do not include them in this.
If the user says pick and place, place them in this only. Do NOT put them in 'Move to position'

If the user says to only move from one preset to another, only include it in "Move to position". Do NOT include it in 
"Pick and place from preset"

If the user says pick and place from a particular position, write it automatically so that the robot goes to 0,0,0,0,0,0 
with gripper open in '1' of Move end-effector to position. Then, in '2', it moves to the given pick position keeping gripper open,
followed by closing the gripper and keeping the rest of the coordinates same in '3'. In '4', robot should move to 
coordinates 0,0,0,0,0,0 keeping the gripper closed. In '5', the robot should move to given place position keeping gripper closed. 
In '6', open the gripper while keeping the place coordinates same. 

If only pick is given, move to posiiton and open the gripper. After that close the gripper in the '2' of Move end-effector to position, 
keeping the rest of the coordinates same.

If only place is given, close gripper by putting everything in '1' of move end-effector to None, except gripper_position
which should be False. After that, move to place position by putting the coordinates in '2' of move end-effector
while keeping gripper closed by putting gripper_position as False. After that, open gripper in the '3' 
of Move end-effector to position, keeping the rest of the coordinates same.

If pick and place is called for a set preset for example position 1, put the data in the Move to position key instead of 
Move end-effector to. Open gripper after moving to first given position, then close gripper, move to second given position and
then open the gripper

Do NOT use a list or an array in case of multiple commands

Do NOT include triple backticks, 'json', 'python' or any other formatting. 
Do not include changes or explanations.
In the dictionary, return all keys at all times even if there are no values attatched to them.

If only deleted command is given, keep every other dictionary empty they should have no values only a bracket pair

The default units of output should be centimetres and degrees only.

If move to X,Y,Z is called, then that data should go in the section 'Move end-effector to position' section only.
Do NOT add to the preset section and do NOT add it to move to position section.

In cases of boolean, always ensure that the first letter of the words true and false are capitalized. They should 
always be True and False

In cases where a particular key, integer or boolean has no value, NEVER return null, always None

Here is the transcript:
\"\"\"
{transcript}
\"\"\"

"""
    
    response=model.generate_content(prompt,generation_config=genai.types.GenerationConfig(temperature=0.0))
    clean_text = response.text.strip()

    if clean_text.startswith("```"):
        clean_text = clean_text.strip("`")
        lines = clean_text.splitlines()
        if lines[0].startswith("json") or lines[0].startswith("python"):
            lines = lines[1:]
        clean_text = "\n".join(lines).strip()

    try:
        return ast.literal_eval(clean_text)
    except Exception as e:
        print("[ERROR] Could not evaluate Python dict from model output:")
        print(clean_text)
        raise e
