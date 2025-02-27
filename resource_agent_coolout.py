import socket
import sys
import time
from threading import Thread

from resource_agent import ResourceAgent



PA_IP = "127.0.0.1"
PA_PORT = 50501

class CooloutBuffer(ResourceAgent):

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
                self.send_msg_to_pa(False,"Cooling_Machine_1")

            #Start Operation
            elif "Operate" in data.decode():
                self.operate()

            #Kill the use of the file
            elif "Completed" in data.decode():
                self.needed_flag.clear()

    def executeTask(self):
        self.idle_flag.clear()
        self.running_flag.set()
        print('coolout')

        start_time = time.perf_counter()
        while time.perf_counter() - start_time < 5:
            pass  # Non-blocking loop, allows other threads to run

        print("Coolout operation completed.")
        self.running_flag.clear()
        self.completed_flag.set()
        self.idle_flag.set()
        

        pass

    #--------------------------------------#
    # PROCESS FUNCTIONS (HARWARE CONTROL)  #
    #--------------------------------------#

    
if __name__ == "__main__":
    ra = CooloutBuffer(50505)

    # Keep the script alive **only while idle_flag is set**
    while ra.needed_flag.is_set():
        start_time = time.perf_counter()

        while time.perf_counter() - start_time < 1:
            pass
   