import socket
import sys
import copy
import time
import numpy as np
from threading import Thread
# Hardware specific libs for the robot
# See: https://docs.ufactory.cc/xarm_python_sdk/2.-linear-motion
# See: Yonghan's notes, and shared on google-drive
# Note: Currently xarm-python-sdk is installed via pip in this venv
from xarmlib.wrapper import XArmAPI
from resource_agent import ResourceAgent


PA_IP = "127.0.0.1"
PA_PORT = 50501

class RobotArmRA2(ResourceAgent):

    def __init__(self, ra_port : int):
        super().__init__(ra_port)
        self.robot_ip = "192.168.1.156"
        self.arm

    
    def ra_run_autimatic(self):
        '''
        The autimatic control loop where their is preset messages are sent by the
        ra to the pa. This funtion is the ra's main thread (proccessing the pa's incoming
        messages happens in a seperate thread)
        '''
        self.send_msg_to_pa(False,"Autimatic Setup of Machine complete")
        self.setup_robot_connection()
        time.sleep(.5)
        
        pass

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
                self.send_msg_to_pa(False,"Robot_Arm_2")

            #Start Operation
            elif "Operate" in data.decode():
                self.operate()

            #Start Operation
            elif "Finish" in data.decode():
                print('get finish')
                self.completed_flag.set()

            #Kill the use of the file
            elif "Completed" in data.decode():
                self.needed_flag.clear()



    # Robot specific setup functions:
    def setup_robot_connection(self):
        
        self.arm = XArmAPI('192.168.1.156', baud_checkset=False)

        self.params = {
            'grip_speed': 800,
            'radius': -1,
            'auto_enable': True,
            'wait': True,
            'speed': 100,
            'acc': 10000,
            'angle_speed': 20,
            'angle_acc': 500,
            'quit': False,
        }

        # Move the arm to the initial position
        self.arm.set_position(x=250, y=-150, z=400, roll=180.0, pitch=0.0, yaw=0.0, 
                              speed=self.params['speed'], mvacc=self.params['acc'], 
                              radius=self.params['radius'], wait=True)

        self.arm.motion_enable(enable=True)
        self.arm.set_mode(0)
        self.arm.set_state(0)

        self.arm.open_lite6_gripper()

        pass

    #--------------------------------------#
    # PROCESS FUNCTIONS (HARWARE CONTROL)  #
    #--------------------------------------#

    def operate(self):

        print('Got task')
        if not self.running_flag.is_set():
            print('Starting task')
            self.running_flag.set()
            self.task_thread = Thread(target=self.executeTask, daemon=True)
            self.task_thread.start()
        else:
            print("Task is already running!")

        pass

    def executeTask(self):
        "Starts executeTask() in a separate thread if not already running."

        print('executing')

        def move_to_pose(command, speed=400, mvacc=1000):
            pose = command["Pose"]
            if command["Type"] == "Cartesian":
                self.arm.set_position(
                    x=pose[0, 3],
                    y=pose[1, 3],
                    z=pose[2, 3],
                    roll=np.rad2deg(np.arctan2(pose[2, 1], pose[2, 2])),
                    pitch=np.rad2deg(np.arcsin(-pose[2, 0])),
                    yaw=np.rad2deg(np.arctan2(pose[1, 0], pose[0, 0])),
                    speed=speed,
                    mvacc=mvacc,
                    wait=True
                )
            elif command["Type"] == "Joint":
                self.arm.set_position_aa(pose, speed = speed, mvacc = mvacc, wait = True, is_radian=False)
            else: print("Invalid type")

        # Core function
        def execute_pick_and_place(pickup_locations, waypoints):
            standoff = 50
            for pickup in pickup_locations:
                #print(pickup)
                # Step 0: Move above pickup location
                self.arm.open_lite6_gripper()
                #move_to_pose(home)

                forw = copy.deepcopy(pickup)
                forw["Pose"][1, 3] += -130
                forw["Pose"][2, 3] += standoff + 150
                #move_to_pose(forw)

                above_pickup = copy.deepcopy(pickup)

                above_pickup['Pose'][2, 3] += standoff
                move_to_pose(above_pickup, speed = 200)

                #Step 1: Go to pickup
                move_to_pose(pickup)

                # Step 2: Close gripper
                self.arm.close_lite6_gripper()  # Adjust as needed for your gripper
                time.sleep(.4)
                # Step 3: Translate up 30mm
                above_pickup = copy.deepcopy(pickup)
                above_pickup["Pose"][2, 3] += standoff
                move_to_pose(above_pickup)
                # Step 3.5: Translate forwards

                move_to_pose(forw)
                # Step 4: Move to waypoints
                for waypoint in waypoints:
                    move_to_pose(waypoint, speed=150)

                #move_to_pose(forw, speed=150)
                # Step 5: Return to 30mm above pickup location
                move_to_pose(above_pickup, speed=150)

                # Step 6: Return to pickup location
                move_to_pose(pickup)

                # Step 7: Open gripper
                self.arm.open_lite6_gripper()  # Adjust as needed for your gripper
                time.sleep(0.4)
                # Step 8: Move 50mm up to clear location
                clear_pickup = copy.deepcopy(pickup)
                clear_pickup["Pose"][2, 3] += standoff
                move_to_pose(clear_pickup)

        # Example usage (fill in with actual data)
        home = {"Type": "Joint", "Pose": np.array([-27.9, 36.3, 74, 0.1, 37.7, -28]) * np.pi / 180}
        pickup_locations = [{"Type": "Cartesian", "Pose": np.array([[0, -1, 0, 250], [-1, 0, 0, -105], [0, 0, -1, 82], [0, 0, 0, 1]])},
                            {"Type": "Cartesian", "Pose": np.array([[0, -1, 0, -200], [-1, 0, 0, -105], [0, 0, -1, 82], [0, 0, 0, 1]])}]  # List of 4x4 transform matrices for pickup locations
        waypoints = [{"Type": "Cartesian", "Pose": np.array([[ 6.00e-02,-8.20e-01,-5.70e-01,-2.43e+02],
        [ 6.00e-02, 5.80e-01,-8.20e-01,-2.62e+02],
        [ 1.00e+00, 1.00e-02, 8.00e-02, 3.29e+02],
        [ 0.00e+00, 0.00e+00, 0.00e+00, 1.00e+00]])},{"Type": "Cartesian", "Pose": np.array([[-5.00e-02,-8.80e-01, 4.70e-01, 150],
        [ 1.20e-01,-4.70e-01,-8.80e-01,-275],
        [ 9.90e-01, 1.00e-02, 1.30e-01, 3.04e+02],
        [ 0.00e+00, 0.00e+00, 0.00e+00, 1.00e+00]])}]

        #waypoints = [{"Type": "Joint", "Pose": np.array([-31.6, -2.5, 48.5, 14.8, -41.1, 11.8])},
                    #{"Type": "Joint", "Pose": np.array([31.6, -2.5, 48.5, 14.8, -41.1, 11.8])}]

        while self.completed_flag.is_set()==False:
            print('self completed flag: ')
            print(self.completed_flag.is_set())
            execute_pick_and_place(pickup_locations, waypoints)
        pass

if __name__ == "__main__":
    ra = RobotArmRA2(50506)

        # Keep the script alive **only while idle_flag is set**
    while ra.needed_flag.is_set():
        start_time = time.perf_counter()

        while time.perf_counter() - start_time < 1:
            pass
   