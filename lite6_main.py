import copy

from xarmlib.wrapper import XArmAPI
import numpy as np
import time
# Initialize arm and connection
arm = XArmAPI('192.168.1.156')  # Replace with the actual IP address of your arm
arm.clean_error()
arm.motion_enable(enable=True)
arm.set_mode(0)
arm.set_state(0)
arm.clean_error()
arm.move_gohome(speed=200)
arm.set_allow_approx_motion(True)
# Utility function to move the arm to a pose
def move_to_pose(command, speed=400, mvacc=1000):
    pose = command["Pose"]
    if command["Type"] == "Cartesian":
        arm.set_position(
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
        arm.set_position_aa(pose, speed = speed, mvacc = mvacc, wait = True, is_radian=False)
    else: print("Invalid type")

# Core function
def execute_pick_and_place(pickup_locations, waypoints):
    standoff = 50
    for pickup in pickup_locations:
        #print(pickup)
        # Step 0: Move above pickup location
        arm.open_lite6_gripper()
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
        arm.close_lite6_gripper()  # Adjust as needed for your gripper
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
        arm.open_lite6_gripper()  # Adjust as needed for your gripper
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
while True:
    execute_pick_and_place(pickup_locations, waypoints)
#move_to_pose(pickup_locations[0])
#move_to_pose(waypoints[0])
#move_to_pose(waypoints[1])
# Disconnect arm
arm.disconnect()
