import socket
import sys
import time
from threading import Thread

'''commented out to help with testing'''
#from printrun.printcore import printcore
#from printrun import gcoder
#from printrun.eventhandler import PrinterEventHandler

from resource_agent import ResourceAgent



PA_IP = "127.0.0.1"
PA_PORT = 50501

class PrinterRA(ResourceAgent):

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
                self.send_msg_to_pa(False,"Prusa_i3_MK3S")
            
            #Start Operation
            elif "Operate" in data.decode():
                self.executeTask()


    # Hardwar specific init functin
    def init_printer_connection(self):
        '''
        commented out to help with the testing
        '''
        '''
        self.printer = printcore(port='COM3', baud=115200)
        # Check the event handler implementation to get status / read back from printer in general
        myHandler = PrinterEventHandler()
        self.printer.addEventHandler(myHandler)
        while not self.printer.online:
            time.sleep(0.1)
        self.ra_udp_client_socket.sendto("Printer ready".encode(), self.pa_udp_server_address)
        '''

        pass
        
    #--------------------------------------#
    # PROCESS FUNCTIONS (HARWARE CONTROL)  #
    #--------------------------------------#

    def printInitialize(self):
        self.scheduled_tasks += []
        pass

    def executeTask(self):
        self.idle_flag.clear()
        self.running_flag.set()
        print('print action')
        time.sleep(5)
        self.completed_flag.set()
        pass
    
    def print_outer_strucutre(self):
        '''
        commented out to help with testing
        '''
        '''
        gcode=[i.strip() for i in open('G-Code.gcode')] # or pass in your own array of gcode lines instead of reading from a file
        gcode = gcoder.LightGCode(gcode)
        self.printer.startprint(gcode) # this will start a print
        '''
        self.ra_udp_client_socket.sendto("Print done".encode(), self.pa_udp_server_address)
    
if __name__ == "__main__":
    ra = PrinterRA(50503)
       
     # Keep the script alive **only while idle_flag is set**
    while ra.needed_flag.is_set():
        time.sleep(1)
   

'''
class ResourceAgent:

    def __init__(self, ra_port):
        print("Initialized resource agent")
        self.ra_udp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.pa_udp_server_address = ("127.0.0.1", int(ra_port))
        self.ra_udp_client_socket.bind(('', 50501))
        self.pa_reader_thread = Thread(target=self.process_pa_messages, name="pa_message_processing_thread")
        self.pa_reader_thread.daemon = True # Set as deamon to stop when main thread ends
        self.pa_reader_thread.start()
        self.printer = None # Will be manually connected via p
        self.ra_run_manually()

    def ra_run_manually(self):
        """
        The manual control loop where the user can control which messages are sent by the
        ra manually. This funtion is the ra's main thread (proccessing the pa's incoming
        messages happens in a seperate thread)
        """
        while True:
            user_command = input("[RA-CMD] Input (cmd-list with h): " )
            if user_command == 'm':
                self.send_msg_to_pa()
            elif user_command == 'p':
                self.setup_printer_connection()
            elif user_command == 'h':
                print("\tquit - q\n\t")
            elif user_command == 'q':
                return

    def send_msg_to_pa(self):
        manual_message = input("\tEnter message from RA to PA: ")
        self.ra_udp_client_socket.sendto(manual_message.encode(), self.pa_udp_server_address)
    
    def setup_printer_connection(self):
        self.printer = printcore(port='COM3', baud=115200)
        myHandler = PrinterEventHandler()
        self.printer.addEventHandler(myHandler)
        while not self.printer.online:
            time.sleep(0.1)
        self.printer.send_now("M105") # Temp?
        #printer.send_now("G28")
        time.sleep(10)

    def process_create_outer_structure(self):
        gcode=[i.strip() for i in open('filename.gcode')] # or pass in your own array of gcode lines instead of reading from a file
        gcode = gcoder.LightGCode(gcode)
        self.printer.startprint(gcode) # this will start a print

    def process_pa_messages(self):
        while True:
            data, server = self.ra_udp_client_socket.recvfrom(1024)
            print(f"RecevFrom {server}: {data}")
           
    
if __name__ == "__main__": 
    ra = ResourceAgent(sys.argv[1])
'''