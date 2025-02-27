'''
This scirpts creates a preliminary simple product
agent implementation serving as a demo to evaluate LLM
generated agent-knowledege bases.

The future implemenation of this agent aims at:
- reading a state machine as input
- discovering and interfacing with multiple resource agents
- (future) configuring a ROS communication framework based on the state machines

The baseline implementation will have the a-priori known state-machine
hard code.

It will exchange messages with two resource agents via UDP protocol.


Date: Nov. 11 2024
Author(s): Josua Hoefgen
'''

import socket
from threading import Thread
import threading
import json
import time

from resource_agent import ResourceAgent
from resource_agent_rolloutbuffer import RolloutBuffer
from resource_agent_printer import PrinterRA
from resource_agent_robot import RobotArmRA
from resource_agent_coolout import CooloutBuffer

class ProductAgent:

    def __init__(self):

        # Port Set Up
        self.pa_port = 50501
        self.pa_udp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.pa_udp_server_socket.bind(('', 50501))
        
        # Different data holders to hold differnt aspects about the RA
        self.ra_list = []
        self.ra_resource_dic = {}
        print("Set up product agent")

        # Used more in testing when artificially adding the RA's
        self.ra_holder = []

        # Thread Set Up
        self.ra_reader_thread = Thread(target=self.process_ra_messages, name="ra_reader_thread")
        self.ra_reader_thread.daemon = True # So reader stops when main thread ends
        self.ra_reader_thread.start()

        # Flags to help operate through threads
        self.query_flag = threading.Event()
        self.operating_finished = threading.Event()

        # Main location state
        self.currentLocation = 'printerLocation'
        self.locations = {
            'Prusa_i3_MK3S': 'printerLocation',
            'Prusa_MK4': 'printerLocation',
            'Cooling_Machine_1': 'coolingLocation',
            'Rollout_1': 'rolloutLocation'
        }

        #Created a manual or autimatic option to start up the program
        startUp = input("\tManual(1) or Autimatic (2): ")
        while startUp != "3":

            if startUp == "1":
                self.manual_pa_control()
                startUp = "3"

            elif startUp == "2":
                self.autimatic_pa_control()
                startUp = "3"

            else:
                startUp = input("\tManual(1) or Autimatic (2): ")


    def process_ra_messages(self):
        while True:
            # recieves message
            message, address = self.pa_udp_server_socket.recvfrom(1024)
            print(f"RecevFrom {address} : {message.decode()}")

            # adds the new RA to list if not currently in it
            if address not in self.ra_list:

                self.ra_list.append(address)
                print(f"Added RA {address} to RA list at index {len(self.ra_list)}")

            # Waits to recieve a message to link the RA to the resource it can provide in a dictionary
            if self.query_flag.is_set() == True:

                self.ra_resource_dic[message.decode()] = address

            # When recieves message that the task the RA had gets completed
            if message.decode() == "Task Completed":

                self.operating_finished.set()
                print('A Task has been completed')

    def manual_pa_control(self):
        '''
        Manual use of the product agent
        '''

        while True:
            user_pa_control_cmd = input("[PA-Cmd] Input pa cmd: ")

            if user_pa_control_cmd == 'q':
                # self.ra_reader_thread.join()
                print("Shutting down PA")
                return
            
            elif user_pa_control_cmd == 'm':

                agent_id = input("\tEnter agent id: ")
                message = input("\tEnter message to RA: ")

                print('Choosen ID: '+agent_id)
                print('Size of the ra list: ')
                print(self.ra_list)

                self.pa_udp_server_socket.sendto(message.encode(), self.ra_list[int(agent_id)-1])
            print(user_pa_control_cmd)

    def autimatic_pa_control(self):
        """
        Autimatic process used to create the connections for testing purposes
        """
        #created different agents for testing purposes
        # Time buffer
        start_time = time.perf_counter()

        while time.perf_counter() - start_time < 1:
            pass

        # Continues to main operation using the state machine
        self.operate("C:/Users/zekam/Documents/PennStateAgentSystem/spec_1.json")
        pass            

    def operate(self, directory):
        """
        Go through a .json file and retrieve all the states and transitions to go through the required operations for the product agents
        """

        # Read the file and store the different states and transitions
        with open(directory, "r") as file:
            stateMachine = json.load(file)

        # two lists to contain the files states and transitions
        states = stateMachine["states"]
        transitions = stateMachine["transitions"]

        #initialize the current state by going through and finding which state has it apart of its details
        for state, props in states.items():
            if props["initialState"]:
                current_state = state
                break

        
        
        '''
        Code for checking all the states
        stateKeys = []
        for state, dummy in states.items():
            stateKeys += [state]
        
        runThroughTransitions = [current_state]
        '''
        
        # querys the resource available from the different RAs
        for i in range(len(self.ra_list)):
            #sets flag saying currently gethering this information
            self.query_flag.set()
            # queries the resource adds a buffer and then clears the query flag
            self.queryResource(i)
            start_time = time.perf_counter()

            while time.perf_counter() - start_time < 1:
                pass
            self.query_flag.clear()


        '''
        To possibly use in doing traveling salesman problem with the given state machine

        for transition, details in transitions.items():
            if details["parent"] == current_state:
                availableTransitions += [transition]
                for available in availableTransitions:
                    
                print(availableTransitions)

        '''

        # Well not in the final state goes through and does the processes of each state
        while not states[current_state]["finalState"]:
            print('New State: ')
            availableTransitions = []

            # Goes through all the transitions and finds which one has the current state as its parent and adds it to a list
            # left as a list for later use when multiple may have the same parent
            for transition, details in transitions.items():

                if details["parent"] == current_state:

                    availableTransitions += [transition]
            
            tasksList = []
            
            # Goes through the transition chosen and adds all the tasks needed to a list
            # Also left as a list when further use has mutliple tasks per transition
            for transition in availableTransitions:

                for tasks in transitions[transition]["programCall"]:
                    tasksList += [tasks]

            '''
            Operation for the work required of the transition
            '''
            # Goes through the tasks in tasks list to find the RA needed for completion
            # Currently breaks but left in a loop for later built upon use

            for tasks in tasksList:

                currentRA = self.ra_list.index(self.ra_resource_dic[transitions[availableTransitions[0]]["programCall"][tasks]['possibleResources'][0]])
                
                print('location needed by process:')
                print(self.locations[transitions[availableTransitions[0]]["programCall"][tasks]['possibleResources'][0]])

                print('current location:')
                print(self.currentLocation)

                if self.locations[transitions[availableTransitions[0]]["programCall"][tasks]['possibleResources'][0]] != self.currentLocation:

                    self.robot_arm_movement(self.ra_list.index(self.ra_resource_dic['Robot_Arm']), 
                                            self.locations[transitions[availableTransitions[0]]["programCall"][tasks]['possibleResources'][0]])
                    
                break

            # Sends the task to the required RA in a separate thread
            print('Action by RA Started')
            self.sendTaskToRA(currentRA)

            # Function to continuously query the RA status in a separate thread
            while self.operating_finished.is_set() == False:
                start_time = time.perf_counter()

                while time.perf_counter() - start_time < 1:
                    pass
                self.queryStatus(currentRA)

            #changes to next state
            current_state = transitions[availableTransitions[0]]['child']     
            
        self.completeProductionProcess()
        pass

    def robot_arm_movement(self,robotRA, newLocation):
        '''
        Robot arm operation
        Hard coded before every action as not currently in any transition tasks
        '''
        print('Move action started to')
        print(newLocation)

        # Sends the task to the required RA
        self.sendTaskToRobot(robotRA, newLocation)

        # Waits for the Operating flag to clear when requesting status, so continually asks until changed
        while self.operating_finished.is_set() == False:
            start_time = time.perf_counter()

            while time.perf_counter() - start_time < 1:
                pass

            self.queryStatus(robotRA)

        print('Move Action has ended')

        pass

    # ---------------------------------------#
    # PA calls to the RAs      #
    # ---------------------------------------#

    def sendTaskToRA(self,agentID):
        """
        sends start task message to RA
        """
        # sets operating flag to wait for other methods to wait on it
        self.operating_finished.clear()
        message = "Operate"
        self.pa_udp_server_socket.sendto(message.encode(), self.ra_list[int(agentID)])
        pass

    def sendTaskToRobot(self,agentID,newLocation):
        """
        sends start task message to robot with location
        """
        # sets operating flag to wait for other methods to wait on it
        self.operating_finished.clear()
        message = newLocation
        self.pa_udp_server_socket.sendto(message.encode(), self.ra_list[int(agentID)])
        pass

    def queryResource(self,agentID):
        """
        Queries the status of the choosen agent
        """
        message = "Resource"
        self.pa_udp_server_socket.sendto(message.encode(), self.ra_list[int(agentID)])
        pass

    def queryStatus(self,agentID):
        """
        Queries the status of the choosen agent
        """
        message = "ProvideStatus"
        self.pa_udp_server_socket.sendto(message.encode(), self.ra_list[int(agentID)])
        pass

    def completeProductionProcess(self):
        """
        
        """
        message = "Completed"
        for agents in self.ra_list:
            self.pa_udp_server_socket.sendto(message.encode(), agents)

        print("Done!")
        pass
        

if __name__ == "__main__":
    pa = ProductAgent()