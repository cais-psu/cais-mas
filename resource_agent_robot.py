import socket
import sys
import time
from threading import Thread
# Hardware specific libs for the robot
# See: https://docs.ufactory.cc/xarm_python_sdk/2.-linear-motion
# See: Yonghan's notes, and shared on google-drive
# Note: Currently xarm-python-sdk is installed via pip in this venv
# from xarm.wrapper import XArmAPI
from resource_agent import ResourceAgent



PA_IP = "127.0.0.1"
PA_PORT = 50501

class RobotArmRA(ResourceAgent):

    def __init__(self, ra_port : int):
        super().__init__(ra_port)
    
    # ---------------------------------------#
    # GENERIC RESOURCE AGENT FUNCTIONS       #
    # ---------------------------------------#

    def process_pa_messages(self):
        while True:
            data, server = self.ra_udp_client_socket.recvfrom(1024)
            print(f"RecevFrom {server}: {data}")

            #The different responses that can be done when reciving messages 
            if "ProcessName" in data.decode(): # Or messages like "Status"
                self.generic_process_function()

            #Provide the status of the program
            elif "ProvideStatus" in data.decode():
                self.send_status_to_pa()
            
            #Provide ability
            elif "Resource" in data.decode():
                self.send_msg_to_pa(False,"Robot_Arm")

            #Start Operation
            elif "Operate" in data.decode():
                self.executeTask()
            
            ## The place to move 
            # to cooling location
            elif 'coolingLocation' in data.decode():
                self.handlingPrinterToCoolout()

            elif 'rolloutLocation' in data.decode():
                self.handlingCooloutToRollout()


    # Robot specific setup functions:
    def setup_robot_connection(self):

        #self.arm=XArmAPI(self.robot_ip)
        #self.arm.motion_enable(enable=True)
        #self.arm.set_mode(0)
        #self.arm.set_state(0)
        pass

    #--------------------------------------#
    # PROCESS FUNCTIONS (HARWARE CONTROL)  #
    #--------------------------------------#

    def handlingPrinterToCoolout(self):
        self.idle_flag.clear()
        self.running_flag.set()
        print('handling printer to coolout')
        time.sleep(5)
        self.completed_flag.set()
        pass

    def handlingCooloutToRollout(self):
        self.idle_flag.clear()
        self.running_flag.set()
        print('handling coolout to rollout')
        time.sleep(5)
        self.completed_flag.set()
        pass

    def executeTask(self):
        self.idle_flag.clear()
        self.running_flag.set()
        time.sleep(5)
        self.completed_flag.set()
        pass

    def move_process(self):
        # Position is (x,y,z,roll, pitch, yaw) in units [mm] and [deg]
        
        '''
        commented out due to library problem
        '''
        #self.arm.set_position(0,300, 350,180,0,0)
        #self.arm.set_position(300,0,250,180,0,0) 

        # Currently some issues with the gripper, movement doesnt work 
        #code = self.arm.set_gripper_mode(0)
        #print('set gripper mode: location mode, code={}'.format(code))
        #code= self.arm.set_gripper_enable(True)
        #print('set gripper enable, code={}'.format(code))
        #self.arm.set_gripper_speed(1000)
        #self.arm.set_gripper_position(550, wait=True)
        
        # Add more motions ...
        pass
    
  
if __name__ == "__main__":
    ra = RobotArmRA(50504)

        # Keep the script alive **only while idle_flag is set**
    while ra.needed_flag.is_set():
        time.sleep(1)
   