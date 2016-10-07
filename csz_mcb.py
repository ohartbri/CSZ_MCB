#!/usr/bin/env python
#Following command will print documentation of csz_mcb.py:
#pydoc csz_mcb

"""
AUTHORS:
Oskar Hartbrich <ohartbri@hawaii.edu>
University of Hawaii at Manoa
Instrumentation Development Lab (IDLab), WAT214

DEPENDENCIES:
csz_ezt430i

OVERVIEW:
Python wrapper for commands to control a Cincinatti Subzero MCB-1.2-.33-H/AC climate chamber via a EZT-430i controller through RS-232 using the modbus protocol.
 
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
from math import log
import serial
from csz_ezt430i import EZT_430i

class MCB_12_33_HAC(object):
    
    def __init__(self, addr, modbus_slaveaddr):
        #EZT_430i.MODBUS_DEBUG = True
        self.instr = EZT_430i(addr, modbus_slaveaddr)

    def _estimate_ramptime(self, temp_start, temp_target):
        ''' Calculate an estimate for the time needed to ramp chamber from one temperature to the next. Based on measured curves from with empty chamber.
            Inputs: temp_start: starting temperature in C, temp_target target temperature in C
            Outputs: estimate of ramping time in seconds'''
        if (temp_start > temp_target):
            #cooling operation
            def t(temperature):
                return -10.0*log((temperature+33.1)/196.8) #parameters obtained from fit to cooldown curve with time in minutes
        else:
            #heating operation
            def t(temperature):
                return -40.6*log((temperature-292.3)/-321.4) #parameters obtained from fit to heatup curve with time in minutes
            
        t_base = t(temp_target) - t(temp_start)

        return (t_base * 1.2 + 0.5) * 60
            
            
            
        
    
    @property
    def temperature_target(self):
        ''' Read the target temperature (loop1 SP) from climate chamber
        Inputs: None
        Output: target temperature'''
        return self.instr.loop1_SP

    @temperature_target.setter
    def temperature_target(self, val):
        ''' Write a target temperature (loop1 SP) to climate chamber. Does not wait until temperature is reached or anything. If you want to ramp the chamber temperature, better use ramp_temperature() 
        Inputs: target temperature
        Output: None'''
        self.instr.loop1_SP = val
    
    @property
    def temperature_current(self):
        ''' Read current temperature (loop PV) from climate chamber
        Inputs: None
        Output: current temperature'''
        return self.instr.loop1_PV
    
    @property
    def busy_status(self):
        ''' Read current controller busy status
        Inputs: None
        Outputs: busy status (0 = ready, 1 = offline/busy)'''
        return self.instr.status
    
    @property
    def error_status(self):
        ''' Read current controller loop error status
        Inputs: None
        Outputs: loop error status (translate via error_string[] dict)'''
        return self.instr.loop1_errorstatus
    
    @property
    def mode_operation(self):
        ''' Read current controller mode/operation status
        Inputs: None
        Outputs: operation mode and status in bits (see B10 in manual)'''
        return self.instr.loop1_mode_operation
    
    @property
    def power(self):
        ''' Read current power (loop1 event) status
        Inputs: None
        Outputs: current power status'''
        return self.instr.get_event(0)

    @power.setter
    def power(self, val):
        ''' Write power (loop1 event) status 
        Inputs: Power status
        Output: None'''
        self.instr.set_event(0,val)
        
    
    def ramp_temperature(self, temperature_target, wait_until_temperature_reached = True):
        ''' Ramp chamber temperature to target. Waits estimated time needed to ramp to new target.
        Inputs: temperature_target, wait_until_temperature_reached (optional, default is True)
        Outputs: None'''

        #check chamber is not busy and no error status is set on temperature loop
        assert(instr.busy_status == False)
        assert(instr.error_status == 0)

        if (wait_until_temperature_reached):
            timeout = _estimate_ramptime(self.instr.loop1_PV, temperature_target)
        
        self.instr.loop1_SP = temperature_target
        self.instr.set_event(0,1)
    
        if (wait_until_temperature_reached):
            sleep(timeout)
