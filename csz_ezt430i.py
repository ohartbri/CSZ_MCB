#!/usr/bin/env python
#Following command will print documentation of csz_mcb.py:
#pydoc csz_mcb

"""
AUTHORS:
Oskar Hartbrich <ohartbri@hawaii.edu>
University of Hawaii at Manoa
Instrumentation Development Lab (IDLab), WAT214

DEPENDENCIES:
minimalmodbus (install via pip install minimalmodbus)

OVERVIEW:
Python wrapper for commands to communicate with a CSZ EZT-430i climate chamber controller through RS-232 using the modbus protocol.
 
HOW TO USE: --needs to be updated--
"from rigol_DG4162 import Func_DG4162" will import the class
"func = Rigol_DG4162(addr)" will create the instrument object
"func.channel = 2" will set channel to chan 2 (IMPORTANT: Set chan 1st)
"func.set_voltage = 5" will set voltage to 5 Volts on channel 2
"print func.set_voltage" will read the set voltage on chan 2

MANUALS:
EZT-430i Controller:
User's Manual
http://www.cszindustrial.com/portals/1/pdf/EZT-430i_User_Manual.pdf
Communications Manual:
http://www.cszindustrial.com/portals/1/pdf/EZT-430i_Communications_Manual.pdf

"""

from time import sleep
#from exception import ValueError
import serial
import minimalmodbus

class EZT_430i(object):
    #these are tested defaults to communicate with the climate chamber controller. 
    SERIAL_TIMEOUT = 0.3
    SERIAL_PARITY = serial.PARITY_NONE
    SERIAL_BAUDRATE = 9600

    COMMAND_DELAY = 0.5 #delay in seconds between commands. 0.5 is a tested default
    
    MODBUS_DEBUG = False
    
    #EZT_430i register addresses:
    _REG_STATUS = 0
    _REG_EVENTS = 12
    _REG_LOOP1_PV = 35
    _REG_LOOP1_SP = 36
    _REG_LOOP1_MODE_OPERATION = 38
    _REG_LOOP1_ERROR = 39
    _REG_LOOP2_PV = 40
    _REG_LOOP2_SP = 41
    _REG_LOOP2_MODE_OPERATION = 43
    _REG_LOOP2_ERROR = 44
    
    error_string = {0: 'No Error',
		    4: 'Illegal Setup Values',
		    10:'Comm Error - Bad Function Code',
		    11:'Comm Error - Register Out of Range',
		    14:'Comm Error - Write Read Only Data',
		    15:'Comm Error - Out of Range Data',
		    25:'Holdback Time Out',
		    26:'Auto Tune Error',
		    27:'Input Type Requires Calibration',
		    29:'EEPROM Error',
		    30:'Cold Junction Failure',
		    39:'Sensor Break',
		    40:'A to D failure'}
		   
    
    def __init__(self, addr, modbus_slaveaddr):
	self.addr = addr
	self.modbus_slaveaddr = modbus_slaveaddr
	
	#save default setting of minimalmodbus 
	tmp_modbus_TIMEOUT = minimalmodbus.TIMEOUT
	tmp_modbus_PARITY = minimalmodbus.PARITY
	tmp_modbus_BAUDRATE = minimalmodbus.BAUDRATE
    
	minimalmodbus.TIMEOUT = self.SERIAL_TIMEOUT
	minimalmodbus.PARITY = self.SERIAL_PARITY
	minimalmodbus.BAUDRATE = self.SERIAL_BAUDRATE
		
	self.instr = minimalmodbus.Instrument(addr, modbus_slaveaddr)
	self.instr.debug = self.MODBUS_DEBUG
	
	#reste minimalmodbus settings to defaults. if using open/close for each command, this cannot be done like this i guess.
	minimalmodbus.TIMEOUT = tmp_modbus_TIMEOUT
	minimalmodbus.PARITY = tmp_modbus_PARITY
	minimalmodbus.BAUDRATE = tmp_modbus_BAUDRATE
	
    def _wait_timeout(self):
	sleep(self.COMMAND_DELAY)
	
    def wait_after(f):
	def wrapper(self,*args, **kwargs):
	    r = f(self,*args, **kwargs)
	    self._wait_timeout()
	    return r
	return wrapper
	    

    @property
    @wait_after
    def status(self):
	''' Read the status register of the controller.
	    Input: None
	    Output: true if system is ready to go, false if system is not ready (busy)'''
	return self.instr.read_register(self._REG_STATUS) > 0
	
    @property
    @wait_after
    def events(self):
	''' read the whole event status register from the controller
	    Input: None
	    Output: event status register (bit0 is event1, bit1 is event2 up to bit5 event6)'''
	return self.instr.read_register(self._REG_EVENTS)
    
    @events.setter
    @wait_after
    def events(self, val):
	''' write the whole event status register to the controller
	    Input: event status register
	    Output: None'''
	self.instr.write_register(self._REG_EVENTS, val)
	
    def get_event(self, eventnumber):
	''' read the event status of the given event number
	    Input: event number
	    Output: event status '''
	events = self.events
	mask = 1 << eventnumber
	return (events & mask)
    
    def set_event(self, eventnumber, val):
	''' set the event status of the given  event number. other events will not be touched
	    Inputs: event number, event status value
	    Output: None '''
	
	if val not in [0, 1]:
	    raise ValueError('wrong event value given. must be 1 or 0')
	    return
	
	events = self.events
		
	mask = 1 << eventnumber
	
	if (val == 1):
	    events = events | mask
	elif (val == 0):
	    mask = ~mask
	    events = events & mask
	
	self.events = events
    
    @property
    @wait_after
    def loop1_PV(self):
	''' read the PV (process value, typically current temperature) of control loop 1
	    Inputs: None
	    Output: loop 1 PV'''
	return self.instr.read_register(self._REG_LOOP1_PV, 1, signed=True)
   
    @loop1_PV.setter
    @wait_after
    def loop1_PV(self, val):
	''' write the PV (process value, typically current temperature) of control loop 1
	    Inputs: PV to write (up to one decimal)
	    Outputs: None'''
        self.instr.write_register(self._REG_LOOP1_PV,val,1,signed=True)
	
	
    @property
    @wait_after
    def loop1_SP(self):
	''' read the SP (set point, typically target temperature) of control loop 1
	    Inputs: None
	    Output: loop 1 SP'''
	return self.instr.read_register(self._REG_LOOP1_SP,1,signed=True)
   
    @loop1_SP.setter
    @wait_after
    def loop1_SP(self, val):
	''' write the SP (process value, typically target temperature) of control loop 1
	    Inputs: SP to write (up to one decimal)
	    Outputs: None'''
        self.instr.write_register(self._REG_LOOP1_SP,val,1,signed=True)

    @property
    @wait_after
    def loop1_mode_operation(self):
	''' read the mode/operational status of control loop 1. 
	    Inputs: None
	    Output: error status'''
	return self.instr.read_register(self._REG_LOOP1_MODE_OPERATION)
   	
    @property
    @wait_after
    def loop1_errorstatus(self):
	''' read the error status of control loop 1. use predefined dictionary EZT_430i.error_string[] to translate error status to text
	    Inputs: None
	    Output: error status'''
	return self.instr.read_register(self._REG_LOOP1_ERROR)
   	
    @property
    @wait_after
    def loop2_PV(self):
	''' read the PV (process value, typically current humidity) of control loop 2
	    Inputs: None
	    Output: loop 1 PV'''
	return self.instr.read_register(self._REG_LOOP2_PV,1,signed=True)
   
    @loop2_PV.setter
    @wait_after
    def loop2_PV(self, val):
	''' write the PV (process value, typically current humidity) of control loop 2
	    Inputs: PV to write (up to one decimal)
	    Outputs: None'''
        self.instr.write_register(self._REG_LOOP2_PV,val,1,signed=True)
	
	
    @property
    @wait_after
    def loop2_SP(self):
	''' read the SP (set point, typically target humidity) of control loop 2
	    Inputs: None
	    Output: loop 1 SP'''
	return self.instr.read_register(self._REG_LOOP2_SP,1,signed=True)
   
    @loop1_SP.setter
    @wait_after
    def loop2_SP(self, val):
	''' write the SP (process value, typically target humidity) of control loop 2
	    Inputs: SP to write (up to one decimal)
	    Outputs: None'''
        self.instr.write_register(self._REG_LOOP2_SP,val,1,signed=True)
	
    @property
    @wait_after
    def loop2_mode_operation(self):
	''' read the mode/operational status of control loop 2. 
	    Inputs: None
	    Output: error status'''
	return self.instr.read_register(self._REG_LOOP2_MODE_OPERATION)
   	
    @property
    @wait_after
    def loop2_errorstatus(self):
	''' read the error status of control loop 2 use predefined dictionary EZT_430i.error_string[] to translate error status to text
	    Inputs: None
	    Output: error status'''
	return self.instr.read_register(self._REG_LOOP2_ERROR)
   	
	
	    
	    
	
	
    

   
    
