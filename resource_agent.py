import socket
import sys
import time
from threading import Thread
import threading

#from printrun.printcore import printcore
#from printrun import gcoder
#from printrun.eventhandler import PrinterEventHandler


PA_IP = "127.0.0.1"
PA_PORT = 50501

class ResourceAgent:

    def __init__(self, ra_port : int):
        # Set-up of UDP connection, binding to own port and spec of server address
        self.ra_udp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.ra_udp_client_socket.bind(('', int(ra_port)))
        self.pa_udp_server_address = ((PA_IP, PA_PORT))
        # Set-up seperate thread to read incoming messages from product agent
        self.pa_reader_thread = Thread(target=self.process_pa_messages, name="pa_message_processing_thread")
        self.pa_reader_thread.daemon = True # Set as deamon to stop when main thread ends
        self.pa_reader_thread.start()

        # Flag for when the operation is running 
        self.running_flag = threading.Event()

        self.completed_flag = threading.Event()

        self.idle_flag = threading.Event()
        self.idle_flag.set()

        self.needed_flag = threading.Event()
        self.needed_flag.set()
        
        startUp = input("\tRA Manual(1) or Autimatic (2): ")
        while startUp != "3":

            if startUp == "1":
                self.ra_run_manually()
                startUp = "3"

            elif startUp == "2":
                self.ra_run_autimatic()
                startUp = "3"

            else:
                startUp = input("\tManual(1) or Autimatic (2): ")

        # main atributes
        self.scheduled_tasks = []
        self.capabilities = []
        self.message_dic = {}


    def ra_run_manually(self):
        '''
        The manual control loop where the user can control which messages are sent by the
        ra manually. This funtion is the ra's main thread (proccessing the pa's incoming
        messages happens in a seperate thread)
        '''
        while True:
            user_command = input("[RA-CMD] Input (cmd-list with h): " )
            if user_command == 'm':
                self.send_msg_to_pa()
            elif user_command == 'h':
                print("\tquit - q\n\t")
            elif user_command == 'q':
                self.pa_reader_thread.join() # Since reader thread is a deamon this should be obsolete
                return
            
    def ra_run_autimatic(self):
        '''
        The autimatic control loop where their is preset messages are sent by the
        ra to the pa. This funtion is the ra's main thread (proccessing the pa's incoming
        messages happens in a seperate thread)
        '''
        self.send_msg_to_pa(False,"Autimatic Setup of Machine complete")
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


    def send_msg_to_pa(self,manual,msg):
        if manual == True:
            message = input("\tEnter message from RA to PA: ")
        else:
            message = msg

        self.ra_udp_client_socket.sendto(message.encode(), self.pa_udp_server_address)

    def operate(self):
        "Starts executeTask() in a separate thread if not already running."
        if not self.running_flag.is_set():
            self.running_flag.set()
            self.task_thread = Thread(target=self.executeTask, daemon=True)
            self.task_thread.start()
        else:
            print("Task is already running!")

        pass

    def executeTask(self):
        pass

    def sendTaskCompleted(self):
        
        #clears flag announcing it running
        self.running_flag.clear()

        self.completed_flag.clear()

        self.idle_flag.set()

        self.send_msg_to_pa(False, "Task Completed")

        pass


    #--------------------------------------#
    # PROCESS FUNCTIONS (HARWARE CONTROL)  #
    #--------------------------------------#
    def generic_process_function(self):
        '''
        Hardware control to realize a process
        '''
        print("Executing a generic process funcion...")
    
    def send_status_to_pa(self):
        # Checks the running flag and reports wether it is in operation or idle, or if it has just finished a task
        if self.completed_flag.is_set():
            self.sendTaskCompleted()

        elif self.running_flag.is_set():
            self.ra_udp_client_socket.sendto("Currently in operation".encode(), self.pa_udp_server_address)

        elif self.idle_flag.is_set():
            self.ra_udp_client_socket.sendto("Currently in idle".encode(), self.pa_udp_server_address)



    
if __name__ == "__main__":
    ra = ResourceAgent(sys.argv[1])
   