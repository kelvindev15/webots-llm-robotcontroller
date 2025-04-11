import os

from common.llm.chats import LLMChat
from common.utils.experiments import get_next_experiment_number, getExperimentFolderById
from common.utils.images import saveImage, toBase64Image
from common.utils.llm import create_message
from common.robot.RobotController import RobotController
import json
import re


class LLMRobotController:

    def __init__(self, robotController: RobotController, chat: LLMChat):
        self.robot = robotController
        self.chat = chat
        self.systemInstruction = self.chat.get_system_instruction()

    def __extractJSON(self, text):
        # This pattern looks for ```json, captures everything until the closing ```
        pattern = re.compile(r'```json\n(.*?)```', re.DOTALL)
        match = pattern.search(text)
        if match:
            return match.group(1)
        return None

    def __getPlanFromText(self, text):
        return json.loads(self.__extractJSON(text))

    def executeCommand(self, command):
        command_map = {
            "FRONT": self.robot.moveForward,
            "BACK": self.robot.moveBackward,
            "TLEFT": self.robot.turnLeft,
            "TRIGHT": self.robot.turnRight
        }
        step_count = 0
        while self.robot.computeStep() != -1 and step_count < command["steps"]:
            command_map.get(command["command"])()
            step_count += 1
        self.robot.stopMoving()

    def executePlan(self, plan):
        print(plan)
        for command in plan["commands"]:
            if command["command"] == "FEEDBACK":
                return False
            elif command["command"] == "COMPLETE":
                return True
            self.executeCommand(command)
        return None

    def replay(self, plan):
        self.robot.setPose(plan["initialRobotPose"])
        return self.executePlan(plan)

    def __saveOrUpdateExperimentRecord(self, id, experiment):
        experimentFile = f"{getExperimentFolderById(id)}/experiment.json"
        existing = os.path.exists(experimentFile)
        updatedExeriment = None
        if existing:
            with open(experimentFile, "r") as file:
                updatedExeriment = json.loads(file.read())
                updatedExeriment["plans"].append(experiment["plans"][-1])
                updatedExeriment["poses"].append(experiment["poses"][-1])
        with open(experimentFile, "w") as file:
            file.write(json.dumps(updatedExeriment)
                       if existing else json.dumps(experiment))
        return

    def __operate(self, id, initial_prompt, plan):
        experiment_record = {
            "prompt": initial_prompt,
            "model": self.chat.get_model_name(),
            "systemInstruction": self.systemInstruction,
            "initialRobotPose": self.robot.getPose(),
            "plans": [plan],
            "poses": []
        }
        complete = self.executePlan(plan)
        experiment_record["poses"].append(self.robot.getPose())
        while not complete:
            if complete is None:
                print("Plan in a unknown state")
                self.__saveOrUpdateExperimentRecord(id, experiment_record)
                experiment_record["poses"].append(self.robot.getPose())
                return None
            image = self.robot.getCameraImage()
            saveImage(
                image, f"img_{len(experiment_record['plans'])}.jpg", getExperimentFolderById(id))
            intermediate_response = self.chat.send_message(
                create_message("Here's what you see", toBase64Image(self.robot.getCameraImage())))
            new_plan = self.__getPlanFromText(intermediate_response)
            experiment_record["plans"].append(new_plan)
            self.__saveOrUpdateExperimentRecord(id, experiment_record)
            complete = self.executePlan(new_plan)
            experiment_record["poses"].append(self.robot.getPose())
        print("Plan completed")
        return complete

    def ask(self, prompt):
        experiment_id = get_next_experiment_number()
        experimentFolder = getExperimentFolderById(experiment_id)
        os.makedirs(experimentFolder)
        image = self.robot.getCameraImage()
        saveImage(image, "img_0.jpg", experimentFolder)
        image = toBase64Image(image)
        self.chat.clear_chat()
        response = self.chat.send_message(create_message(prompt, image))
        return self.__operate(experiment_id, prompt, self.__getPlanFromText(response))
