#Voice/Text control
Uses Whisper run locally to transcribe speech to text and Gemini to parse through the transcript to extract relevant data. Uses Phosphobot control API to actually control and move the robot. Can pick between controlling through speech or typed command

Phosphobot - https://phospho.ai/
Phosphobot documentation - https://docs.phospho.ai/

#Requirements
1) Initialize a virtual environment with Python 3.11.9 and install the dependencies
2) Install Whisper from here: https://github.com/openai/whisper
3) Create Gemini API key and put it into .env file
   https://aistudio.google.com/apikey
4) Install the following libraries
   1) https://ai.google.dev/gemini-api/docs/quickstart
   2) dotenv
   3) ast
   4) requests
   5) pickle
   6) sounddevice
   7) numpy
   8) time
  
#Available commands
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
- "Pick and Place from coordinates" -> specify absolute coordinates for pick and place function, both can also be used individually.
- "Pick and Place from preset A to preset B" -> performs pick and place function from one preset position to another, saved in pickle file.
- Sequences - the system has the ability to store and execute complex, multi-step commands in the form of "sequences".
  This feature is ideal for repeated tasks which require a higher degree of control of the robot position in terms of both cartesian coordinates and joint angles,
  which might not be achievable with just cartesian movements. The specific commands under this are:-
  - Save sequences
  - Execute sequences
  - delete sequences
- Save current position as preset: the current position/orientation of the robot can be saved
