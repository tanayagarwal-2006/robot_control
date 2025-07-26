import requests
import pickle
import time
import google.generativeai as genai
from dotenv import load_dotenv
import os
import ast
import robot_movement as rbm

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

pi_ip="127.0.0.1"
pi_port=80

SKILL_FILE="skills.pkl"

def extract_commands_for_skills(skill_transcript: str):
    model = genai.GenerativeModel("gemini-2.0-flash")

    prompt = f"""
You are AI that is responsible for assisting the user in training a robot on skills.
During the skills training process, the user will manually manipulate the robot to various 
positions and say commands like "save this position as pose1" or "save as glass_pose".

Your task is to extract a single dictionary in this exact format:
{{"Save position": "name"}}

For example:
- If the user says: "save current position as glass_pose", your output must be: {{"Save position": "glass_pose"}}
- If the user says: "save as goal_pose", your output must be: {{"Save position": "goal_pose"}}

The user may type done when they are finished giving commands. In that case, return an empty dict

Input command:
"{skill_transcript}"

Output ONLY the dictionary. Do not include explanations or formatting like triple backticks.
"""

    response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(temperature=0.0))

    clean_text = response.text.strip()

    # Clean extra formatting if present
    if clean_text.startswith("```"):
        clean_text = clean_text.strip("`")
        lines = clean_text.splitlines()
        if lines and (lines[0].startswith("json") or lines[0].startswith("python")):
            lines = lines[1:]
        clean_text = "\n".join(lines).strip()

    try:
        return ast.literal_eval(clean_text)
    except Exception as e:
        print("[ERROR] Could not evaluate Python dict from model output:")
        print(clean_text)
        raise e

def skills_training():
    name=input("Enter name of skill: ")
    time.sleep(5)
    print(f"[INFO] Initiating skills training")
    url=f"http://{pi_ip}:{pi_port}/torque/toggle"
    params={
        "robot_id":0
    }
    json_data={
        "torque_status":True
    }
    response_torque=requests.post(url,params=params,json=json_data)
    if response_torque.status_code==200:
        print("[INFO] Torque toggled successfully")
    else:
        print("[ERROR] Failed to toggle torque")

    if os.path.exists(SKILL_FILE):
        with open(SKILL_FILE,"rb") as file:
            all_skills=pickle.load(file)
    else:
        all_skills={}

    current_seuqence=[]

    while True:
        transcript=input("Enter skills training commands. Type done when finished: ")
        skill_data=extract_commands_for_skills(transcript)
        print(skill_data)

        skill_data=extract_commands_for_skills(transcript)

        if "Save position" in skill_data:
            pose_name=skill_data["Save position"]
            joint_angles=rbm.read_joints()
            current_seuqence.append((pose_name,joint_angles))
        
        if current_seuqence:
            all_skills[name]=current_seuqence
            with open(SKILL_FILE,"wb") as file:
                pickle.dump(all_skills,file)
            print(f"[INFO] Skill {name} successfully saved")

        if "done" in transcript:
            url=f"http://{pi_ip}:{pi_port}/torque/toggle"
            params={
                "robot_id":0
            }
            json_data={
                "torque_status":False
            }
            response_torque=requests.post(url,params=params,json=json_data)
            if response_torque.status_code==200:
                print("[INFO] Torque toggled successfully")
            else:
                print("[ERROR] Failed to toggle torque")

            rbm.robot_init()
            break

def execute_skill(name:str):
    with open(SKILL_FILE,"rb") as file:
        skill_data=pickle.load(file)
    
    if name not in skill_data:
        print(f"[ERROR] Skill not found")
    else:
        for skill_name,skill_seq in skill_data.items():
            print(f"[INFO] Executing {skill_name}")
            for pose_name,joint_angles in skill_seq:
                print(f"[INFO] Moving to {pose_name}")
                rbm.rotate_joints([(i+1,joint_angles[i]) for i in range (6)])