######### Chi.Bio Operating System V1.0 #########

#Import required python packages
import os
import random
import time
import math
from flask import Flask, render_template, jsonify
from threading import Thread, Lock
import threading
import numpy as np
from datetime import datetime, date
import Adafruit_GPIO.I2C as I2C
import Adafruit_BBIO.GPIO as GPIO
import time
import serial
import simplejson
import copy
import csv
import smbus2 as smbus
import logging
from logging.handlers import TimedRotatingFileHandler



def check_config_value(config_key, default_value, critical=False):
    if config_key not in application.config.keys():
        if critical:
            raise ValueError('config value for %s was not found, it must be set for safe operations' % config_key)
        application.config[config_key] = default_value
        application.logger.warning('config value %s was not found and set to default: %s' % (config_key, default_value))
    else:
        application.logger.info('config found: %s=%s' % (config_key, application.config[config_key]))

application = Flask(__name__)
application.config.from_pyfile('config/chibio_default.cfg', silent=True)
application.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0 #Try this https://stackoverflow.com/questions/23112316/using-flask-how-do-i-modify-the-cache-control-header-for-all-output/23115561#23115561
check_config_value(config_key='LOG_LEVEL', default_value='WARNING')
log_level = logging.getLevelName(application.config['LOG_LEVEL'])
application.logger.setLevel(level=log_level)
handler = TimedRotatingFileHandler(filename='./log/chibio.log',when="w0", interval=1, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
application.logger.addHandler(handler)

lock=Lock()
        
#Initialise data structures.

#Sysdata is a structure created for each device and contains the setup / measured data related to that device during an experiment. All of this information is passed into the user interface during an experiment.
sysData = {'M0' : {
   'UIDevice' : 'M0',
   'present' : 0,
   'presentDevices' : { 'M0' : 0,'M1' : 0,'M2' : 0,'M3' : 0,'M4' : 0,'M5' : 0,'M6' : 0,'M7' : 0},
   'Version' : {'value' : 'Turbidostat V3.0'},
   'DeviceID' : '',
   'DeviceName': '',
   'time' : {'record' : []},
   'LEDA' : {'WL' : '395', 'default': 0.1, 'target' : 0.0, 'max': 1.0, 'min' : 0.0,'ON' : 0},
   'LEDB' : {'WL' : '457', 'default': 0.1, 'target' : 0.0, 'max': 1.0, 'min' : 0.0,'ON' : 0},
   'LEDC' : {'WL' : '500', 'default': 0.1, 'target' : 0.0, 'max': 1.0, 'min' : 0.0,'ON' : 0},
   'LEDD' : {'WL' : '523', 'default': 0.1, 'target' : 0.0, 'max': 1.0, 'min' : 0.0,'ON' : 0},
   'LEDE' : {'WL' : '595', 'default': 0.1, 'target' : 0.0, 'max': 1.0, 'min' : 0.0,'ON' : 0},
   'LEDF' : {'WL' : '623', 'default': 0.1, 'target' : 0.0, 'max': 1.0, 'min' : 0.0,'ON' : 0},
   'LEDG' : {'WL' : '6500K', 'default': 0.1, 'target' : 0.0, 'max': 1.0, 'min' : 0.0,'ON' : 0},
   'LASER650' : {'name' : 'LASER650', 'default': 0.5, 'target' : 0.0, 'max': 1.0, 'min' : 0.0,'ON' : 0},
   'UV' : {'WL' : 'UV', 'default': 0.5, 'target' : 0.0, 'max': 1.0, 'min' : 0.0,'ON' : 0},
   'Heat' : {'default': 0.0, 'target' : 0.0, 'max': 1.0, 'min' : 0.0,'ON' : 0,'record' : []},
   'Thermostat' : {'default': 37.0, 'target' : 0.0, 'max': 50.0, 'min' : 0.0,'ON' : 0,'record' : [],'cycleTime' : 30.0, 'Integral' : 0.0,'last' : -1},
   'Experiment' : {'indicator' : 'USR0', 'startTime' : 'Waiting', 'startTimeRaw' : 0, 'ON' : 0,'cycles' : 0, 'cycleTime' : 60.0,'threadCount' : 0},
   'Terminal' : {'text' : ''},
   'AS7341' : {
        'spectrum' : {'nm410' : 0, 'nm440' : 0, 'nm470' : 0, 'nm510' : 0, 'nm550' : 0, 'nm583' : 0, 'nm620' : 0, 'nm670' : 0,'CLEAR' : 0, 'NIR' : 0,'DARK' : 0,'ExtGPIO' : 0, 'ExtINT' : 0, 'FLICKER' : 0},
        'channels' : {'nm410' : 0, 'nm440' : 0, 'nm470' : 0, 'nm510' : 0, 'nm550' : 0, 'nm583' : 0, 'nm620' : 0, 'nm670' : 0,'CLEAR' : 0, 'NIR' : 0,'DARK' : 0,'ExtGPIO' : 0, 'ExtINT' : 0, 'FLICKER' : 0},
        'current' : {'ADC0': 0,'ADC1': 0,'ADC2': 0,'ADC3': 0,'ADC4': 0,'ADC5' : 0}},
   'ThermometerInternal' : {'current' : 0.0,'record' : []},
   'ThermometerExternal' : {'current' : 0.0,'record' : []},
   'ThermometerIR' : {'current' : 0.0,'record' : []},
   'OD' :  {'current' : 0.0,'target' : 0.5,'default' : 0.5,'max': 10, 'min' : 0,'record' : [],'targetrecord' : [],'Measuring' : 0, 'ON' : 0,'Integral' : 0.0,'Integral2' : 0.0,'device' : 'LASER650'},
   'OD0' : {'target' : 0.0,'raw' : 0.0,'max' : 100000.0,'min': 0.0,'LASERb' : 1.833 ,'LASERa' : 0.226, 'LEDFa' : 0.673, 'LEDAa' : 7.0  },
   'Chemostat' : {'ON' : 0, 'p1' : 0.0, 'p2' : 0.1},
   'Zigzag': {'ON' : 0, 'Zig' : 0.04,'target' : 0.0,'SwitchPoint' : 0},
   'GrowthRate': {'current' : 0.0,'record' : [],'default' : 2.0},
   'Volume' : {'target' : 20.0,'max' : 50.0, 'min' : 0.0,'ON' : 0},
   'Pump1' :  {'target' : 0.0,'default' : 0.0,'max': 1.0, 'min' : -1.0, 'direction' : 1.0, 'ON' : 0,'record' : [], 'thread' : 0},
   'Pump2' :  {'target' : 0.0,'default' : 0.0,'max': 1.0, 'min' : -1.0, 'direction' : 1.0, 'ON' : 0,'record' : [], 'thread' : 0},
   'Pump3' :  {'target' : 0.0,'default' : 0.0,'max': 1.0, 'min' : -1.0, 'direction' : 1.0, 'ON' : 0,'record' : [], 'thread' : 0},
   'Pump4' :  {'target' : 0.0,'default' : 0.0,'max': 1.0, 'min' : -1.0, 'direction' : 1.0, 'ON' : 0,'record' : [], 'thread' : 0},
   'Stir' :  {'target' : 0.0,'default' : 0.5,'max': 1.0, 'min' : 0.0, 'ON' : 0},
   'Light' :  {'target' : 0.0,'default' : 0.5,'max': 1.0, 'min' : 0.0, 'ON' : 0, 'Excite' : 'LEDD', 'record' : []},
   'Custom' :  {'Status' : 0.0,'default' : 0.0,'Program': 'C1', 'ON' : 0,'param1' : 0, 'param2' : 0, 'param3' : 0.0, 'record' : []},
   'FP1' : {'ON' : 0 ,'LED' : 0,'BaseBand' : 0, 'Emit11Band' : 0,'Emit2Band' : 0,'Base' : 0, 'Emit11' : 0,'Emit2' : 0,'BaseRecord' : 0, 'Emit1Record' : 0,'Emit2Record' : 0 ,'Gain' : 0},
   'FP2' : {'ON' : 0 ,'LED' : 0,'BaseBand' : 0, 'Emit11Band' : 0,'Emit2Band' : 0,'Base' : 0, 'Emit11' : 0,'Emit2' : 0,'BaseRecord' : 0, 'Emit1Record' : 0,'Emit2Record' : 0 ,'Gain' : 0},
   'FP3' : {'ON' : 0 ,'LED' : 0,'BaseBand' : 0, 'Emit11Band' : 0,'Emit2Band' : 0,'Base' : 0, 'Emit11' : 0,'Emit2' : 0,'BaseRecord' : 0, 'Emit1Record' : 0,'Emit2Record' : 0 ,'Gain' : 0},
   'biofilm' : {'LEDA' : {'nm410' : 0, 'nm440' : 0, 'nm470' : 0, 'nm510' : 0, 'nm550' : 0, 'nm583' : 0, 'nm620' : 0, 'nm670' : 0,'CLEAR' : 0,'NIR' : 0},
                'LEDB' : {'nm410' : 0, 'nm440' : 0, 'nm470' : 0, 'nm510' : 0, 'nm550' : 0, 'nm583' : 0, 'nm620' : 0, 'nm670' : 0,'CLEAR' : 0,'NIR' : 0},
                'LEDC' : {'nm410' : 0, 'nm440' : 0, 'nm470' : 0, 'nm510' : 0, 'nm550' : 0, 'nm583' : 0, 'nm620' : 0, 'nm670' : 0,'CLEAR' : 0,'NIR' : 0},
                'LEDD' : {'nm410' : 0, 'nm440' : 0, 'nm470' : 0, 'nm510' : 0, 'nm550' : 0, 'nm583' : 0, 'nm620' : 0, 'nm670' : 0,'CLEAR' : 0,'NIR' : 0},
                'LEDE' : {'nm410' : 0, 'nm440' : 0, 'nm470' : 0, 'nm510' : 0, 'nm550' : 0, 'nm583' : 0, 'nm620' : 0, 'nm670' : 0,'CLEAR' : 0,'NIR' : 0},
                'LEDF' : {'nm410' : 0, 'nm440' : 0, 'nm470' : 0, 'nm510' : 0, 'nm550' : 0, 'nm583' : 0, 'nm620' : 0, 'nm670' : 0,'CLEAR' : 0,'NIR' : 0},
                'LEDG' : {'nm410' : 0, 'nm440' : 0, 'nm470' : 0, 'nm510' : 0, 'nm550' : 0, 'nm583' : 0, 'nm620' : 0, 'nm670' : 0,'CLEAR' : 0,'NIR' : 0},
                'LASER650' : {'nm410' : 0, 'nm440' : 0, 'nm470' : 0, 'nm510' : 0, 'nm550' : 0, 'nm583' : 0, 'nm620' : 0, 'nm670' : 0,'CLEAR' : 0,'NIR' : 0}}
   }}



#SysDevices is unique to each device and is responsible for storing information required for the digital communications, and various automation funtions. These values are stored outside sysData since they are not passable into the HTML interface using the jsonify package.        
sysDevices = {'M0' : {
    'AS7341' : {'device' : 0},
    'ThermometerInternal' : {'device' : 0},
    'ThermometerExternal' : {'device' : 0},
    'ThermometerIR' : {'device' : 0,'address' :0},
    'DAC' : {'device' : 0},
    'Pumps' : {'device' : 0,'startup' : 0, 'frequency' : 0},
    'PWM' : {'device' : 0,'startup' : 0, 'frequency' : 0},
    'Pump1' : {'thread' : 0,'threadCount' : 0, 'active' : 0},
    'Pump2' : {'thread' : 0,'threadCount' : 0, 'active' : 0},
    'Pump3' : {'thread' : 0,'threadCount' : 0, 'active' : 0},
    'Pump4' : {'thread' : 0,'threadCount' : 0, 'active' : 0},
    'Experiment' : {'thread' : 0},
    'Thermostat' : {'thread' : 0,'threadCount' : 0},
    
}}


for M in ['M1','M2','M3','M4','M5','M6','M7']:
        sysData[M]=copy.deepcopy(sysData['M0'])
        sysDevices[M]=copy.deepcopy(sysDevices['M0'])
        

#sysItems stores information about digital addresses which is used as a reference for all devices.        
sysItems = {
    'DAC' : {'LEDA' : '00000100','LEDB' : '00000000','LEDC' : '00000110','LEDD' : '00000001','LEDE' : '00000101','LEDF' : '00000011','LEDG' : '00000010','LASER650' : '00000111'},
    'Multiplexer' : {'device' : 0 , 'M0' : '00000001','M1' : '00000010','M2' : '00000100','M3' : '00001000','M4' : '00010000','M5' : '00100000','M6' : '01000000','M7' : '10000000'},
    'UIDevice' : 'M0',
    'Watchdog' : {'pin' : 'P8_11','thread' : 0,'ON' : 1},
    'FailCount' : 0,
    'All' : {'ONL' : 0xFA, 'ONH' : 0xFB, 'OFFL' : 0xFC, 'OFFH' : 0xFD},
    'Stir' : {'ONL' : 0x06, 'ONH' : 0x07, 'OFFL' : 0x08, 'OFFH' : 0x09},
    'Heat' : {'ONL' : 0x3E, 'ONH' : 0x3F, 'OFFL' : 0x40, 'OFFH' : 0x41},
    'UV' : {'ONL' : 0x42, 'ONH' : 0x43, 'OFFL' : 0x44, 'OFFH' : 0x45},
    'LEDA' : {'ONL' : 0x0E, 'ONH' : 0x0F, 'OFFL' : 0x10, 'OFFH' : 0x11},
    'LEDB' : {'ONL' : 0x16, 'ONH' : 0x17, 'OFFL' : 0x18, 'OFFH' : 0x19},
    'LEDC' : {'ONL' : 0x0A, 'ONH' : 0x0B, 'OFFL' : 0x0C, 'OFFH' : 0x0D},
    'LEDD' : {'ONL' : 0x1A, 'ONH' : 0x1B, 'OFFL' : 0x1C, 'OFFH' : 0x1D},
    'LEDE' : {'ONL' : 0x22, 'ONH' : 0x23, 'OFFL' : 0x24, 'OFFH' : 0x25},
    'LEDF' : {'ONL' : 0x1E, 'ONH' : 0x1F, 'OFFL' : 0x20, 'OFFH' : 0x21},
    'LEDG' : {'ONL' : 0x12, 'ONH' : 0x13, 'OFFL' : 0x14, 'OFFH' : 0x15},
    'Pump1' : {
        'In1' : {'ONL' : 0x06, 'ONH' : 0x07, 'OFFL' : 0x08, 'OFFH' : 0x09},
        'In2' : {'ONL' : 0x0A, 'ONH' : 0x0B, 'OFFL' : 0x0C, 'OFFH' : 0x0D},
    },
    'Pump2' : {
        'In1' : {'ONL' : 0x0E, 'ONH' : 0x0F, 'OFFL' : 0x10, 'OFFH' : 0x11},
        'In2' : {'ONL' : 0x12, 'ONH' : 0x13, 'OFFL' : 0x14, 'OFFH' : 0x15},
    },
    'Pump3' : {
        'In1' : {'ONL' : 0x16, 'ONH' : 0x17, 'OFFL' : 0x18, 'OFFH' : 0x19},
        'In2' : {'ONL' : 0x1A, 'ONH' : 0x1B, 'OFFL' : 0x1C, 'OFFH' : 0x1D},
    },
    'Pump4' : {
        'In1' : {'ONL' : 0x1E, 'ONH' : 0x1F, 'OFFL' : 0x20, 'OFFH' : 0x21},
        'In2' : {'ONL' : 0x22, 'ONH' : 0x23, 'OFFL' : 0x24, 'OFFH' : 0x25},
    },
    'AS7341' : {
        '0x00' : {'A' : 'nm470', 'B' : 'U'},
        '0x01' : {'A' : 'U', 'B' : 'nm410'},
        '0x02' : {'A' : 'U', 'B' : 'U'},
        '0x03' : {'A' : 'nm670', 'B' : 'U'},
        '0x04' : {'A' : 'U', 'B' : 'nm583'},
        '0x05' : {'A' : 'nm510', 'B' : 'nm440'},
        '0x06' : {'A' : 'nm550', 'B' : 'U'},
        '0x07' : {'A' : 'U', 'B' : 'nm620'},
        '0x08' : {'A' : 'CLEAR', 'B' : 'U'},
        '0x09' : {'A' : 'nm550', 'B' : 'U'},
        '0x0A' : {'A' : 'U', 'B' : 'nm620'},
        '0x0B' : {'A' : 'U', 'B' : 'U'},
        '0x0C' : {'A' : 'nm440', 'B' : 'U'},
        '0x0D' : {'A' : 'U', 'B' : 'nm510'},
        '0x0E' : {'A' : 'nm583', 'B' : 'nm670'},
        '0x0F' : {'A' : 'nm470', 'B' : 'U'},
        '0x10' : {'A' : 'ExtGPIO', 'B' : 'nm410'},
        '0x11' : {'A' : 'CLEAR', 'B' : 'ExtINT'},
        '0x12' : {'A' : 'DARK', 'B' : 'U'},
        '0x13' : {'A' : 'FLICKER', 'B' : 'NIR'},
    }
}
   


# This section of code is responsible for the watchdog circuit. The circuit is implemented in hardware on the control computer, and requires the watchdog pin be toggled low->high each second, otherwise it will power down all connected devices. This section is therefore critical to operation of the device.
def runWatchdog():  
    #Watchdog toggling function which continually runs in a thread.
    global sysItems;
    if (sysItems['Watchdog']['ON']==1):
        sysItems['Watchdog']['thread']
        GPIO.output(sysItems['Watchdog']['pin'], GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(sysItems['Watchdog']['pin'], GPIO.LOW)
        time.sleep(0.4)
        sysItems['Watchdog']['thread']=Thread(target = runWatchdog, args=())
        sysItems['Watchdog']['thread'].setDaemon(True)
        sysItems['Watchdog']['thread'].start();

GPIO.setup(sysItems['Watchdog']['pin'], GPIO.OUT)
print(str(datetime.now()) + ' Starting watchdog')
application.logger.info('Starting watchdog')
sysItems['Watchdog']['thread']=Thread(target = runWatchdog, args=())
sysItems['Watchdog']['thread'].setDaemon(True)
sysItems['Watchdog']['thread'].start(); 



def initialise(M):
    #Function that initialises all parameters / clears stored values for a given device.
    #If you want to record/add values to sysData, recommend adding an initialisation line in here.
    global sysData;
    global sysItems;
    global sysDevices

    for LED in ['LEDA','LEDB','LEDC','LEDD','LEDE','LEDF','LEDG']:
        sysData[M][LED]['target']=sysData[M][LED]['default']
        sysData[M][LED]['ON']=0
    
    sysData[M]['UV']['target']=sysData[M]['UV']['default']
    sysData[M]['UV']['ON']=0
    
    sysData[M]['LASER650']['target']=sysData[M]['LASER650']['default']
    sysData[M]['LASER650']['ON']=0
    
    FP='FP1'
    sysData[M][FP]['ON']=0
    sysData[M][FP]['LED']="LEDB"
    sysData[M][FP]['Base']=0
    sysData[M][FP]['Emit1']=0
    sysData[M][FP]['Emit2']=0
    sysData[M][FP]['BaseBand']="CLEAR"
    sysData[M][FP]['Emit1Band']="nm510"
    sysData[M][FP]['Emit2Band']="nm550"
    sysData[M][FP]['Gain']="x10"
    sysData[M][FP]['BaseRecord']=[]
    sysData[M][FP]['Emit1Record']=[]
    sysData[M][FP]['Emit2Record']=[]
    FP='FP2'
    sysData[M][FP]['ON']=0
    sysData[M][FP]['LED']="LEDD"
    sysData[M][FP]['Base']=0
    sysData[M][FP]['Emit1']=0
    sysData[M][FP]['Emit2']=0
    sysData[M][FP]['BaseBand']="CLEAR"
    sysData[M][FP]['Emit1Band']="nm583"
    sysData[M][FP]['Emit2Band']="nm620"
    sysData[M][FP]['BaseRecord']=[]
    sysData[M][FP]['Emit1Record']=[]
    sysData[M][FP]['Emit2Record']=[]
    sysData[M][FP]['Gain']="x10"
    FP='FP3'
    sysData[M][FP]['ON']=0
    sysData[M][FP]['LED']="LEDE"
    sysData[M][FP]['Base']=0
    sysData[M][FP]['Emit1']=0
    sysData[M][FP]['Emit2']=0
    sysData[M][FP]['BaseBand']="CLEAR"
    sysData[M][FP]['Emit1Band']="nm620"
    sysData[M][FP]['Emit2Band']="nm670"
    sysData[M][FP]['BaseRecord']=[]
    sysData[M][FP]['Emit1Record']=[]
    sysData[M][FP]['Emit2Record']=[]
    sysData[M][FP]['Gain']="x10"
 
    for PUMP in ['Pump1','Pump2','Pump3','Pump4']:
        sysData[M][PUMP]['default']=0.0;
        sysData[M][PUMP]['target']=sysData[M][PUMP]['default']
        sysData[M][PUMP]['ON']=0
        sysData[M][PUMP]['direction']=1.0
        sysDevices[M][PUMP]['threadCount']=0
        sysDevices[M][PUMP]['active']=0
    
    
    sysData[M]['Heat']['default']=0;
    sysData[M]['Heat']['target']=sysData[M]['Heat']['default']
    sysData[M]['Heat']['ON']=0

    sysData[M]['Thermostat']['default']=37.0;
    sysData[M]['Thermostat']['target']=sysData[M]['Thermostat']['default']
    sysData[M]['Thermostat']['ON']=0
    sysData[M]['Thermostat']['Integral']=0
    sysData[M]['Thermostat']['last']=-1

    sysData[M]['Stir']['target']=sysData[M]['Stir']['default']
    sysData[M]['Stir']['ON']=0
    
    sysData[M]['Light']['target']=sysData[M]['Light']['default']
    sysData[M]['Light']['ON']=0
    sysData[M]['Light']['Excite']='LEDD'
    
    sysData[M]['Custom']['Status']=sysData[M]['Custom']['default']
    sysData[M]['Custom']['ON']=0
    sysData[M]['Custom']['Program']='C1'
    
    sysData[M]['Custom']['param1']=0.0
    sysData[M]['Custom']['param2']=0.0
    sysData[M]['Custom']['param3']=0.0
    
    sysData[M]['OD']['current']=0.0
    sysData[M]['OD']['target']=sysData[M]['OD']['default'];
    sysData[M]['OD0']['target']=65000.0
    sysData[M]['OD0']['raw']=65000.0
    sysData[M]['OD']['device']='LASER650'
    #sysData[M]['OD']['device']='LEDA'
    
    #if (M=='M0'):
    #    sysData[M]['OD']['device']='LEDA'
    
    
    sysData[M]['Volume']['target']=20.0
    
    clearTerminal(M)
    addTerminal(M,'System for %s Initialised' % M)
  
    sysData[M]['Experiment']['ON']=0
    sysData[M]['Experiment']['cycles']=0
    sysData[M]['Experiment']['threadCount']=0
    sysData[M]['Experiment']['startTime']=' Waiting '
    sysData[M]['Experiment']['startTimeRaw']=0
    sysData[M]['OD']['ON']=0
    sysData[M]['OD']['Measuring']=0
    sysData[M]['OD']['Integral']=0.0
    sysData[M]['OD']['Integral2']=0.0
    sysData[M]['Zigzag']['ON']=0
    sysData[M]['Zigzag']['target']=0.0
    sysData[M]['Zigzag']['SwitchPoint']=0
    sysData[M]['GrowthRate']['current']=sysData[M]['GrowthRate']['default']

    sysDevices[M]['Thermostat']['threadCount']=0

    channels=['nm410','nm440','nm470','nm510','nm550','nm583','nm620', 'nm670','CLEAR','NIR','DARK','ExtGPIO', 'ExtINT' , 'FLICKER']
    for channel in channels:
        sysData[M]['AS7341']['channels'][channel]=0
        sysData[M]['AS7341']['spectrum'][channel]=0
    DACS=['ADC0', 'ADC1', 'ADC2', 'ADC3', 'ADC4', 'ADC5']
    for DAC in DACS:
        sysData[M]['AS7341']['current'][DAC]=0

    sysData[M]['ThermometerInternal']['current']=0.0
    sysData[M]['ThermometerExternal']['current']=0.0
    sysData[M]['ThermometerIR']['current']=0.0
 
    sysData[M]['time']['record']=[]
    sysData[M]['OD']['record']=[]
    sysData[M]['OD']['targetrecord']=[]
    sysData[M]['Pump1']['record']=[]
    sysData[M]['Pump2']['record']=[]
    sysData[M]['Pump3']['record']=[]
    sysData[M]['Pump4']['record']=[]
    sysData[M]['Heat']['record']=[]
    sysData[M]['Light']['record']=[]
    sysData[M]['ThermometerInternal']['record']=[]
    sysData[M]['ThermometerExternal']['record']=[]
    sysData[M]['ThermometerIR']['record']=[]
    sysData[M]['Thermostat']['record']=[]
	
    sysData[M]['GrowthRate']['record']=[]

    sysDevices[M]['ThermometerInternal']['device']=I2C.get_i2c_device(0x18,2) #Get Thermometer on Bus 2!!!
    sysDevices[M]['ThermometerExternal']['device']=I2C.get_i2c_device(0x1b,2) #Get Thermometer on Bus 2!!!
    sysDevices[M]['DAC']['device']=I2C.get_i2c_device(0x48,2) #Get DAC on Bus 2!!!
    sysDevices[M]['AS7341']['device']=I2C.get_i2c_device(0x39,2) #Get OD Chip on Bus 2!!!!!
    sysDevices[M]['Pumps']['device']=I2C.get_i2c_device(0x61,2) #Get OD Chip on Bus 2!!!!!
    sysDevices[M]['Pumps']['startup']=0
    sysDevices[M]['Pumps']['frequency']=0x1e #200Hz PWM frequency
    sysDevices[M]['PWM']['device']=I2C.get_i2c_device(0x60,2) #Get OD Chip on Bus 2!!!!!
    sysDevices[M]['PWM']['startup']=0
    sysDevices[M]['PWM']['frequency']=0x03# 0x14 = 300hz, 0x03 is 1526 Hz PWM frequency for fan/LEDs, maximum possible. Potentially dial this down if you are getting audible ringing in the device! 
    #There is a tradeoff between large frequencies which can make capacitors in the 6V power regulation oscillate audibly, and small frequencies which result in the number of LED "ON" cycles varying during measurements.
    sysDevices[M]['ThermometerIR']['device']=smbus.SMBus(bus=2) #Set up SMBus thermometer
    sysDevices[M]['ThermometerIR']['address']=0x5a 
    
    
    # This section of commented code is used for testing I2C communication integrity.
    # sysData[M]['present']=1
    # getData=I2CCom(M,'ThermometerInternal',1,16,0x05,0,0)
    # i=0
    # while (1==1):
    #     i=i+1
    #     if (i%1000==1):
    #         print(str(i))
    #     sysDevices[M]['ThermometerInternal']['device'].readU8(int(0x05))
    # getData=I2CCom(M,which,1,16,0x05,0,0)
    

    scanDevices(M)
    if sysData[M]['present']==1:
        turnEverythingOff(M)
        device_str = " Initialised " + str(M) + ', (' + sysData[M]['DeviceName'] + ') Device ID: ' \
                     + sysData[M]['DeviceID']
        print(str(datetime.now()) + device_str)
        application.logger.info(device_str)


def initialiseAll():
    # Initialisation function which runs at when software is started for the first time.
    sysItems['Multiplexer']['device']=I2C.get_i2c_device(0x74,2) 
    sysItems['FailCount']=0
    time.sleep(2.0) #This wait is to allow the watchdog circuit to boot.
    print(str(datetime.now()) + ' Initialising devices')
    application.logger.info('Initialising devices')

    check_config_value(config_key='TWO_PUMPS_PER_DEVICE', default_value=False)
    check_config_value(config_key='NUMBER_OF_OD_MEASUREMENTS', default_value=4)
    check_config_value(config_key='DEVICE_COMM_FAILURE_THRESHOLD', default_value=10)


    for M in ['M0','M1','M2','M3','M4','M5','M6','M7']:
        initialise(M)
    scanDevices("all")
    
    
  
    
def turnEverythingOff(M):
    # Function which turns off all actuation/hardware.
    for LED in ['LEDA','LEDB','LEDC','LEDD','LEDE','LEDF','LEDG']:
        sysData[M][LED]['ON']=0
        
    sysData[M]['LASER650']['ON']=0
    sysData[M]['Pump1']['ON']=0
    sysData[M]['Pump2']['ON']=0
    sysData[M]['Pump3']['ON']=0
    sysData[M]['Pump4']['ON']=0
    sysData[M]['Stir']['ON']=0
    sysData[M]['Heat']['ON']=0
    sysData[M]['UV']['ON']=0
    
    I2CCom(M,'DAC',0,8,int('00000000',2),int('00000000',2),0)#Sets all DAC Channels to zero!!! 
    setPWM(M,'PWM',sysItems['All'],0,0)

    if application.config['TWO_PUMPS_PER_DEVICE']:
        chibios_to_shut_down = [0, 1, 2, 3]
    else:
        chibios_to_shut_down = [0, 1, 2, 4, 5, 6, 7]
    if int(M[1]) in chibios_to_shut_down:
        setPWM(M=M, device='Pumps', channels=sysItems['All'], fraction=0, ConsecutiveFails=0)
    
    SetOutputOn(M,'Stir',0)
    SetOutputOn(M,'Thermostat',0)
    SetOutputOn(M,'Heat',0)
    SetOutputOn(M,'UV',0)
    SetOutputOn(M,'Pump1',0)
    SetOutputOn(M,'Pump2',0)
    SetOutputOn(M,'Pump3',0)
    SetOutputOn(M,'Pump4',0)
    


 

@application.route('/')
def index():
    #Function responsible for sending appropriate device's data to user interface. 
    global sysData
    global sysItems
    
    outputdata=sysData[sysItems['UIDevice']]
    for M in ['M0','M1','M2','M3','M4','M5','M6','M7']:
            if sysData[M]['present']==1:
                outputdata['presentDevices'][M]=1
            else:
                outputdata['presentDevices'][M]=0
    return render_template('index.html',**outputdata)
    
@application.route('/getSysdata/')
def getSysdata():
    #Similar to function above, packages data to be sent to UI.
    global sysData
    global sysItems
    outputdata=sysData[sysItems['UIDevice']]
    for M in ['M0','M1','M2','M3','M4','M5','M6','M7']:
            if sysData[M]['present']==1:
                outputdata['presentDevices'][M]=1
            else:
                outputdata['presentDevices'][M]=0
    return jsonify(outputdata)

@application.route('/changeDevice/<M>',methods=['POST'])
def changeDevice(M):
    #Function responsible for changin which device is selected in the UI.
    global sysData
    global sysItems
    M=str(M)
    if sysData[M]['present']==1:
        for Mb in ['M0','M1','M2','M3','M4','M5','M6','M7']:
            sysData[Mb]['UIDevice']=M
        
        sysItems['UIDevice']=M

    return ('', 204)

@application.route('/scanDevices/<which>',methods=['POST'])
def scanDevices(which):
    #Scans to decide which devices are plugged in/on. Does this by trying to communicate with their internal thermometers (if this communication failes, software assumes device is not present)
    global sysData
    which=str(which)
    
    if which=="all":
        for M in ['M0','M1','M2','M3','M4','M5','M6','M7']:
            sysData[M]['present']=1
            I2CCom(M,'ThermometerInternal',1,16,0x05,0,0) #We arbitrarily poll the thermometer to see if anything is plugged in! 
            sysData[M]['DeviceID']=GetID(M)
    else: 
        
        sysData[which]['present']=1
        I2CCom(which,'ThermometerInternal',1,16,0x05,0,0)
        sysData[which]['DeviceID']=GetID(which)

    return ('', 204)


def GetID(M):
    #Gets the CHi.Bio reactor's ID, which is basically just the unique ID of the infrared thermometer.
    global sysData
    M=str(M)
    ID=''
    if sysData[M]['present']==1:
        pt1=str(I2CCom(M,'ThermometerIR',1,0,0x3C,0,1))
        pt2=str(I2CCom(M,'ThermometerIR',1,0,0x3D,0,1))
        pt3=str(I2CCom(M,'ThermometerIR',1,0,0x3E,0,1))
        pt4=str(I2CCom(M,'ThermometerIR',1,0,0x3F,0,1))
        ID = pt1+pt2+pt3+pt4
        
    return ID
    

def addTerminal(M,strIn):
    #Responsible for adding a new line to the terminal in the UI.
    global sysData
    application.logger.info(strIn)
    now=datetime.now()
    timeString=now.strftime("%Y-%m-%d %H:%M:%S ")
    sysData[M]['Terminal']['text']=timeString + ' - ' +  str(strIn) + '</br>' + sysData[M]['Terminal']['text']
    
@application.route("/ClearTerminal/<M>",methods=['POST'])
def clearTerminal(M):
    #Deletes everything from the terminal.
    global sysData
    M=str(M)
    if (M=="0"):
        M=sysItems['UIDevice']
        
    sysData[M]['Terminal']['text']=''
    addTerminal(M,'Terminal on %s Cleared' % M)
    return ('', 204)   
    


@application.route("/SetFPMeasurement/<item>/<Excite>/<Base>/<Emit1>/<Emit2>/<Gain>",methods=['POST'])
def SetFPMeasurement(item,Excite,Base,Emit1,Emit2,Gain):
    #Sets up the fluorescent protein measurement in terms of gain, and which LED / measurement bands to use.
    FP=str(item)
    Excite=str(Excite)
    Base=str(Base)
    Emit1=str(Emit1)
    Emit2=str(Emit2)
    Gain=str(Gain)
    M=sysItems['UIDevice']
    
    if sysData[M][FP]['ON']==1:
        sysData[M][FP]['ON']=0
        return ('', 204)
    else: 
        sysData[M][FP]['ON']=1
        sysData[M][FP]['LED']=Excite
        sysData[M][FP]['BaseBand']=Base
        sysData[M][FP]['Emit1Band']=Emit1
        sysData[M][FP]['Emit2Band']=Emit2
        sysData[M][FP]['Gain']=Gain
        return ('', 204)  
     

        
    
    

@application.route("/SetOutputTarget/<item>/<M>/<value>",methods=['POST'])
def SetOutputTarget(M,item, value):
    #General function used to set the output level of a particular item, ensuring it is within an acceptable range.
    global sysData
    item = str(item)
    value = float(value)
    M=str(M)
    if (M=="0"):
        M=sysItems['UIDevice']
    info_msg = " Set item: " + str(item) + " to value " + str(value) + " on " + str(M)
    print(str(datetime.now()) + info_msg)
    application.logger.info(info_msg)
    if (value<sysData[M][item]['min']):
        value=sysData[M][item]['min']
    if (value>sysData[M][item]['max']):
        value=sysData[M][item]['max']
        
    sysData[M][item]['target']=value
    
    if(sysData[M][item]['ON']==1 and not(item=='OD' or item=='Thermostat')): #Checking to see if our item is already running, in which case
        SetOutputOn(M,item,0) #we turn it off and on again to restart at new rate.
        SetOutputOn(M,item,1)
    return ('', 204)    
    


    
@application.route("/SetOutputOn/<item>/<force>/<M>",methods=['POST'])
def SetOutputOn(M,item,force):
    #General function used to switch an output on or off.
    global sysData
    item = str(item)
    force = int(force)
    M=str(M)
    application.logger.info('device: %s on %s, output is  %s ' % (item, M, force))
    if (M=="0"):
        M=sysItems['UIDevice']
    #The first statements are to force it on or off it the command is called in force mode (force implies it sets it to a given state, regardless of what it is currently in)
    if (force==1):
        sysData[M][item]['ON']=1
        SetOutput(M,item)
        return ('', 204)
    
    elif(force==0):
        sysData[M][item]['ON']=0;
        SetOutput(M,item)
        return ('', 204)
    
    #Elsewise this is doing a flip operation (i.e. changes to opposite state to that which it is currently in)
    if (sysData[M][item]['ON']==0):
        sysData[M][item]['ON']=1
        SetOutput(M,item)
        return ('', 204)    
    
    else:
        sysData[M][item]['ON']=0;
        SetOutput(M,item)
        return ('', 204)    


def SetOutput(M,item):
    #Here we actually do the digital communications required to set a given output. This function is called by SetOutputOn above as required.
    global sysData
    global sysItems
    global sysDevices
    M=str(M)
    #We go through each different item and set it going as appropriate.
    if(item=='Stir'): 
        #Stirring is initiated at a high speed for a couple of seconds to prevent the stir motor from stalling (e.g. if it is started at an initial power of 0.3)
        if (sysData[M][item]['target']*float(sysData[M][item]['ON'])>0):
            setPWM(M,'PWM',sysItems[item],1.0*float(sysData[M][item]['ON']),0) # This line is to just get stirring started briefly.
            time.sleep(1.5)

            if (sysData[M][item]['target']>0.4 and sysData[M][item]['ON']==1):
                setPWM(M,'PWM',sysItems[item],0.5*float(sysData[M][item]['ON']),0) # This line is to just get stirring started briefly.
                time.sleep(0.75)
            
            if (sysData[M][item]['target']>0.8 and sysData[M][item]['ON']==1):
                setPWM(M,'PWM',sysItems[item],0.7*float(sysData[M][item]['ON']),0) # This line is to just get stirring started briefly.
                time.sleep(0.75)

        setPWM(M,'PWM',sysItems[item],sysData[M][item]['target']*float(sysData[M][item]['ON']),0)
        
        
    elif(item=='Heat'):
        setPWM(M,'PWM',sysItems[item],sysData[M][item]['target']*float(sysData[M][item]['ON']),0)
    elif(item=='UV'):
        setPWM(M,'PWM',sysItems[item],sysData[M][item]['target']*float(sysData[M][item]['ON']),0)
    elif (item=='Thermostat'):
        sysDevices[M][item]['thread']=Thread(target = Thermostat, args=(M,item))
        sysDevices[M][item]['thread'].setDaemon(True)
        sysDevices[M][item]['thread'].start();
        
    elif (item=='Pump1' or item=='Pump2' or item=='Pump3' or item=='Pump4'): 
        if (sysData[M][item]['target']==0):
            sysData[M][item]['ON']=0
        sysDevices[M][item]['thread']=Thread(target = PumpModulation, args=(M,item))
        
        sysDevices[M][item]['thread'].setDaemon(True)
        sysDevices[M][item]['thread'].start();

    elif (item=='OD'):
        SetOutputOn(M,'Pump1',0)
        SetOutputOn(M,'Pump2',0) #We turn pumps off when we switch OD state
    elif (item=='Zigzag'):
        sysData[M]['Zigzag']['target']=5.0
        sysData[M]['Zigzag']['SwitchPoint']=sysData[M]['Experiment']['cycles']
    
    elif (item=='LEDA' or item=='LEDB' or item=='LEDC' or item=='LEDD' or item=='LEDE' or item=='LEDF' or item=='LEDG'):
        setPWM(M,'PWM',sysItems[item],sysData[M][item]['target']*float(sysData[M][item]['ON']),0)
        
    else: #This is if we are setting the DAC. All should be in range [0,1]
        register = int(sysItems['DAC'][item],2)
        
        value=sysData[M][item]['target']*float(sysData[M][item]['ON']) 
        if (value==0):
            value=0
        else:
            value=(value+0.00)/1.00
            sf=0.303 #This factor is scaling down the maximum voltage being fed to the laser, preventing its photodiode current (and hence optical power) being too large.
            value=value*sf
        binaryValue=bin(int(value*4095.9)) #Bit of a dodgy method for ensuring we get an integer in [0,4095]
        toWrite=str(binaryValue[2:].zfill(16))
        toWrite1=int(toWrite[0:8],2)
        toWrite2=int(toWrite[8:16],2)
        I2CCom(M,'DAC',0,8,toWrite1,toWrite2,0)
       
        
        
    
    
        
  
def PumpModulation(M,item):
    #Responsible for turning pumps on/off with an appropriate duty cycle. They are turned on for a fraction of each ~1minute cycle to achieve low pump rates.
    global sysData
    global sysItems
    global sysDevices

    if application.config['TWO_PUMPS_PER_DEVICE']:
        pump_mapping = {'M4': 'M0', 'M5': 'M1', 'M6': 'M2', 'M7': 'M3'}
        if int(M[1]) in [0, 1, 2, 3]:
            if item == 'Pump1' or item == 'Pump2':
                MB = M
                itemB = item
            elif item == 'Pump3' or item == 'Pump4':
                sysData[M][item]['ON'] = 0
                return
        else:
            if item == 'Pump1' or item == 'Pump2':
                MB = pump_mapping[M]
                itemB = 'Pump' + str(int(item[4])+2)
            elif item == 'Pump3' or item == 'Pump4':
                sysData[M][item]['ON'] = 0
                return
    else:
        MB = M
        itemB = item

    sysDevices[M][item]['threadCount']=(sysDevices[M][item]['threadCount']+1)%100 #Index of the particular thread running.
    currentThread=sysDevices[M][item]['threadCount']
    
    while (sysDevices[M][item]['active']==1): #Idea is we will wait here if a previous thread on this pump is already running. Potentially all this 'active' business could be removed from this fuction.
        time.sleep(0.02)
        
    if (abs(sysData[M][item]['target']*sysData[M][item]['ON'])!=1 and currentThread==sysDevices[M][item]['threadCount']): #In all cases we turn things off to begin
        sysDevices[M][item]['active']=1
        setPWM(MB,'Pumps',sysItems[itemB]['In1'],0.0*float(sysData[M][item]['ON']),0)
        setPWM(MB,'Pumps',sysItems[itemB]['In2'],0.0*float(sysData[M][item]['ON']),0)
        setPWM(MB,'Pumps',sysItems[itemB]['In1'],0.0*float(sysData[M][item]['ON']),0)
        setPWM(MB,'Pumps',sysItems[itemB]['In2'],0.0*float(sysData[M][item]['ON']),0)
        sysDevices[M][item]['active']=0
    if (sysData[M][item]['ON']==0):
        return
    
    Time1=datetime.now()
    cycletime=sysData[M]['Experiment']['cycleTime']*1.05 #We make this marginally longer than the experiment cycle time to avoid too much chaos when you come back around to pumping again.
    
    Ontime=cycletime*abs(sysData[M][item]['target'])
    
    # Decided to remove the below section in order to prevent media buildup in the device if you are pumping in very rapidly. This check means that media is removed, then added. Removing this code means these happen simultaneously.
    #if (item=="Pump1" and abs(sysData[M][item]['target'])<0.3): #Ensuring we run Pump1 after Pump2.
    #    waittime=cycletime*abs(sysData[M]['Pump2']['target']) #We want to wait until the output pump has stopped, otherwise you are very inefficient with your media since it will be pumping out the fresh media fromthe top of the test tube right when it enters.
    #    time.sleep(waittime+1.0)  
        
    
    if (sysData[M][item]['target']>0 and currentThread==sysDevices[M][item]['threadCount']): #Turning on pumps in forward direction
        sysDevices[M][item]['active']=1
        setPWM(MB,'Pumps',sysItems[itemB]['In1'],1.0*float(sysData[M][item]['ON']),0)
        setPWM(MB,'Pumps',sysItems[itemB]['In2'],0.0*float(sysData[M][item]['ON']),0)
        sysDevices[M][item]['active']=0
    elif (sysData[M][item]['target']<0 and currentThread==sysDevices[M][item]['threadCount']): #Or backward direction.
        sysDevices[M][item]['active']=1
        setPWM(MB,'Pumps',sysItems[itemB]['In1'],0.0*float(sysData[M][item]['ON']),0)
        setPWM(MB,'Pumps',sysItems[itemB]['In2'],1.0*float(sysData[M][item]['ON']),0)
        sysDevices[M][item]['active']=0
  
    time.sleep(Ontime)
    
    if(abs(sysData[M][item]['target'])!=1 and currentThread==sysDevices[M][item]['threadCount']): #Turning off pumps at appropriate time.
        sysDevices[M][item]['active']=1
        setPWM(MB,'Pumps',sysItems[itemB]['In1'],0.0*float(sysData[M][item]['ON']),0)
        setPWM(MB,'Pumps',sysItems[itemB]['In2'],0.0*float(sysData[M][item]['ON']),0)
        setPWM(MB,'Pumps',sysItems[itemB]['In1'],0.0*float(sysData[M][item]['ON']),0)
        setPWM(MB,'Pumps',sysItems[itemB]['In2'],0.0*float(sysData[M][item]['ON']),0)
        sysDevices[M][item]['active']=0
    
    Time2=datetime.now()
    elapsedTime=Time2-Time1
    elapsedTimeSeconds=round(elapsedTime.total_seconds(),2)
    Offtime=cycletime-elapsedTimeSeconds
    if (Offtime>0.0):
        time.sleep(Offtime)   
    
    
    if (sysData[M][item]['ON']==1 and sysDevices[M][item]['threadCount']==currentThread): #If pumps need to keep going, this starts a new pump thread.
        sysDevices[M][item]['thread']=Thread(target = PumpModulation, args=(M,item))
        sysDevices[M][item]['thread'].setDaemon(True)
        sysDevices[M][item]['thread'].start();
    
        





def Thermostat(M,item):
    #Function that implements thermostat temperature control using MPC algorithm.
    global sysData
    global sysItems
    global sysDevices
    ON=sysData[M][item]['ON']
    sysDevices[M][item]['threadCount']=(sysDevices[M][item]['threadCount']+1)%100
    currentThread=sysDevices[M][item]['threadCount']
    
    if (ON==0):
        SetOutputOn(M,'Heat',0)
        return
    
    MeasureTemp(M,'IR') #Measures temperature - note that this may be happening DURING stirring.

    CurrentTemp=sysData[M]['ThermometerIR']['current']
    TargetTemp=sysData[M]['Thermostat']['target']
    LastTemp=sysData[M]['Thermostat']['last']
    
    #MPC Controller Component
    MediaTemp=sysData[M]['ThermometerExternal']['current']
    MPC=0
    if (MediaTemp>0.0):
        Tdiff=CurrentTemp-MediaTemp
        Pumping=sysData[M]['Pump1']['target']*float(sysData[M]['Pump1']['ON'])*float(sysData[M]['OD']['ON'])
        Gain=2.5
        MPC=Gain*Tdiff*Pumping
        
        
    #PI Controller Component
    e=TargetTemp-CurrentTemp
    dt=sysData[M]['Thermostat']['cycleTime']
    I=sysData[M]['Thermostat']['Integral']
    if (abs(e)<2.0):
        I=I+0.0005*dt*e
        P=0.25*e
    else:
        P=0.5*e;
    
    if (abs(TargetTemp-LastTemp)>2.0): #This resets integrator if we make a big jump in set point.
        I=0.0
    elif(I<0.0):
        I=0.0
    elif (I>1.0):
        I=1.0
    
    sysData[M]['Thermostat']['Integral']=I

    U=P+I+MPC
    
    if(U>1.0):
        U=1.0
        sysData[M]['Heat']['target']=U
        sysData[M]['Heat']['ON']=1
    elif(U<0):  
        U=0
        sysData[M]['Heat']['target']=U
        sysData[M]['Heat']['ON']=0
    else:
        sysData[M]['Heat']['target']=U
        sysData[M]['Heat']['ON']=1
    
    sysData[M]['Thermostat']['last']=sysData[M]['Thermostat']['target']
   
    SetOutput(M,'Heat')
    
    time.sleep(dt)  
        
    
    if (sysData[M][item]['ON']==1 and sysDevices[M][item]['threadCount']==currentThread):
        sysDevices[M][item]['thread']=Thread(target = Thermostat, args=(M,item))
        sysDevices[M][item]['thread'].setDaemon(True)
        sysDevices[M][item]['thread'].start();
    else:
        sysData[M]['Heat']['ON']=0
        sysData[M]['Heat']['target']=0
        SetOutput(M,'Heat')
        
        
    
    
    
    
        

@application.route("/Direction/<item>/<M>",methods=['POST'])
def direction(M,item):
    #Flips direction of a pump.
    global sysData
    M=str(M)
    if (M=="0"):
        M=sysItems['UIDevice']
    sysData[M][item]['target']=-1.0*sysData[M][item]['target']
    if (sysData[M]['OD']['ON']==1):
            sysData[M][item]['direction']=-1.0*sysData[M][item]['direction']

    return ('', 204)  
    

    
def AS7341Read(M,Gain,ISteps,reset):
    #Responsible for reading data from the spectrometer.
    global sysItems
    global sysData
    reset=int(reset)
    ISteps=int(ISteps)
    if ISteps>255:
        ISteps=255 #255 steps is approx 0.71 seconds.
    elif (ISteps<0):
        ISteps=0
    if Gain>10:
        Gain=10 #512x
    elif (Gain<0):
        Gain=0 #0.5x

    I2CCom(M,'AS7341',0,8,int(0xA9),int(0x04),0) #This sets us into BANK mode 0, for accesing registers 0x80+. The 4 means we have WTIMEx16
    if (reset==1):
        I2CCom(M,'AS7341',0,8,int(0x80),int(0x00),0) #Turns power down
        time.sleep(0.01)
        I2CCom(M,'AS7341',0,8,int(0x80),int(0x01),0) #Turns power on with spectral measurement disabled
    else:
        I2CCom(M,'AS7341',0,8,int(0x80),int(0x01),0)  #Turns power on with spectral measurement disabled

    I2CCom(M,'AS7341',0,8,int(0xAF),int(0x10),0) #Tells it we are going to now write SMUX configuration to RAM
    
    
    #I2CCom(M,'AS7341',0,100,int(0x00),int(0x00),0) #Forces AS7341SMUX to run since length is 100.
    AS7341SMUX(M,'AS7341',0,0)
    
    I2CCom(M,'AS7341',0,8,int(0x80),int(0x11),0)  #Runs SMUX command (i.e. cofigures SMUX with data from ram)
    time.sleep(0.001)
    I2CCom(M,'AS7341',0,8,int(0x81),ISteps,0)  #Sets number of integration steps of length 2.78ms Max ISteps is 255
    I2CCom(M,'AS7341',0,8,int(0x83),0xFF,0)  #Sets maxinum wait time of 0.7mS (multiplex by 16 due to WLONG)
    I2CCom(M,'AS7341',0,8,int(0xAA),Gain,0)  #Sets gain on ADCs. Maximum value of Gain is 10 and can take values from 0 to 10.
    #I2CCom(M,'AS7341',0,8,int(0xA9),int(0x14),0) #This sets us into BANK mode 1, for accessing 0x60 to 0x74. The 4 means we have WTIMEx16
    #I2CCom(M,'AS7341',0,8,int(0x70),int(0x00),0)  #Sets integration mode SPM (normal mode)
    #Above is default of 0x70!
    I2CCom(M,'AS7341',0,8,int(0x80),int(0x0B),0)  #Starts spectral measurement, with WEN (wait between measurements feature) enabled.
    time.sleep((ISteps+1)*0.0028 + 0.2) #Wait whilst integration is done and results are processed. 
    
    ASTATUS=int(I2CCom(M,'AS7341',1,8,0x94,0x00,0)) #Get measurement status, including saturation details.
    C0_L=int(I2CCom(M,'AS7341',1,8,0x95,0x00,0))
    C0_H=int(I2CCom(M,'AS7341',1,8,0x96,0x00,0))
    C1_L=int(I2CCom(M,'AS7341',1,8,0x97,0x00,0))
    C1_H=int(I2CCom(M,'AS7341',1,8,0x98,0x00,0))
    C2_L=int(I2CCom(M,'AS7341',1,8,0x99,0x00,0))
    C2_H=int(I2CCom(M,'AS7341',1,8,0x9A,0x00,0))
    C3_L=int(I2CCom(M,'AS7341',1,8,0x9B,0x00,0))
    C3_H=int(I2CCom(M,'AS7341',1,8,0x9C,0x00,0))
    C4_L=int(I2CCom(M,'AS7341',1,8,0x9D,0x00,0))
    C4_H=int(I2CCom(M,'AS7341',1,8,0x9E,0x00,0))
    C5_L=int(I2CCom(M,'AS7341',1,8,0x9F,0x00,0))
    C5_H=int(I2CCom(M,'AS7341',1,8,0xA0,0x00,0))

    I2CCom(M,'AS7341',0,8,int(0x80),int(0x01),0)  #Stops spectral measurement, leaves power on.

    #Status2=int(I2CCom(M,'AS7341',1,8,0xA3,0x00,0)) #Reads system status at end of spectral measursement. 
    #print(str(ASTATUS))
    #print(str(Status2))

    sysData[M]['AS7341']['current']['ADC0']=int(bin(C0_H)[2:].zfill(8)+bin(C0_L)[2:].zfill(8),2)
    sysData[M]['AS7341']['current']['ADC1']=int(bin(C1_H)[2:].zfill(8)+bin(C1_L)[2:].zfill(8),2)
    sysData[M]['AS7341']['current']['ADC2']=int(bin(C2_H)[2:].zfill(8)+bin(C2_L)[2:].zfill(8),2)
    sysData[M]['AS7341']['current']['ADC3']=int(bin(C3_H)[2:].zfill(8)+bin(C3_L)[2:].zfill(8),2)
    sysData[M]['AS7341']['current']['ADC4']=int(bin(C4_H)[2:].zfill(8)+bin(C4_L)[2:].zfill(8),2)
    sysData[M]['AS7341']['current']['ADC5']=int(bin(C5_H)[2:].zfill(8)+bin(C5_L)[2:].zfill(8),2)
    
    
    if (sysData[M]['AS7341']['current']['ADC0']==65535 or sysData[M]['AS7341']['current']['ADC1']==65535 or sysData[M]['AS7341']['current']['ADC2']==65535 or sysData[M]['AS7341']['current']['ADC3']==65535 or sysData[M]['AS7341']['current']['ADC4']==65535 or sysData[M]['AS7341']['current']['ADC5']==65535 ):
        print(str(datetime.now()) + ' Spectrometer measurement was saturated on device ' + str(M)) #Not sure if this saturation check above actually works correctly...
    return 0
        

def AS7341SMUX(M,device,data1,data2):
    #Sets up the ADC multiplexer on the spectrometer, this is responsible for connecting photodiodes to amplifier/adc circuits within the device. 
    #The spectrometer has only got 6 ADCs but >6 photodiodes channels, hence you need to select a subset of photodiodes to measure with each shot. The relative gain does change slightly (1-2%) between ADCs.
    global sysItems
    global sysData
    global sysDevices
    M=str(M)
    Addresses=['0x00','0x01','0x02','0x03','0x04','0x05','0x06','0x07','0x08','0x0A','0x0B','0x0C','0x0D','0x0E','0x0F','0x10','0x11','0x12']
    for a in Addresses:
        A=sysItems['AS7341'][a]['A']
        B=sysItems['AS7341'][a]['B']
        if (A!='U'):
            As=sysData[M]['AS7341']['channels'][A]
        else:
            As=0
        if (B!='U'):
            Bs=sysData[M]['AS7341']['channels'][B]
        else:
            Bs=0
        Ab=str(bin(As))[2:].zfill(4)
        Bb=str(bin(Bs))[2:].zfill(4)
        C=Ab+Bb
        #time.sleep(0.001) #Added this to remove errors where beaglebone crashed!
        I2CCom(M,'AS7341',0,8,int(a,16),int(C,2),0) #Tells it we are going to now write SMUX configuration to RAM
        #sysDevices[M][device]['device'].write8(int(a,16),int(C,2))


@application.route("/GetSpectrum/<Gain>/<M>",methods=['POST'])
def GetSpectrum(M,Gain):
    #Measures entire spectrum, i.e. every different photodiode, which requires 2 measurement shots. 
    Gain=int(Gain[1:])
    global sysData
    global sysItems
    M=str(M)   
    if (M=="0"):
        M=sysItems['UIDevice']
    out=GetLight(M,['nm410','nm440','nm470','nm510','nm550','nm583'],Gain,255)
    out2=GetLight(M,['nm620', 'nm670','CLEAR','NIR','DARK'],Gain,255)
    sysData[M]['AS7341']['spectrum']['nm410']=out[0]
    sysData[M]['AS7341']['spectrum']['nm440']=out[1]
    sysData[M]['AS7341']['spectrum']['nm470']=out[2]
    sysData[M]['AS7341']['spectrum']['nm510']=out[3]
    sysData[M]['AS7341']['spectrum']['nm550']=out[4]
    sysData[M]['AS7341']['spectrum']['nm583']=out[5]
    sysData[M]['AS7341']['spectrum']['nm620']=out2[0]
    sysData[M]['AS7341']['spectrum']['nm670']=out2[1]
    sysData[M]['AS7341']['spectrum']['CLEAR']=out2[2]
    sysData[M]['AS7341']['spectrum']['NIR']=out2[3]
    
        
    return ('', 204)   
    


        
    
def GetLight(M,wavelengths,Gain,ISteps):
    #Runs spectrometer measurement and puts data into appropriate structure.
    global sysData
    M=str(M)
    channels=['nm410','nm440','nm470','nm510','nm550','nm583','nm620', 'nm670','CLEAR','NIR','DARK','ExtGPIO', 'ExtINT' , 'FLICKER']
    for channel in channels:
        sysData[M]['AS7341']['channels'][channel]=0 #First we set all measurement ADC indexes to zero.
    index=1;
    for wavelength in wavelengths:
        if wavelength != "OFF":
            sysData[M]['AS7341']['channels'][wavelength]=index #Now assign ADCs to each of the channel where needed. 
        index=index+1

    success=0
    while success<2:
        try:
            AS7341Read(M,Gain,ISteps,success) 
            success=2
        except:
            print(str(datetime.now()) + 'AS7341 measurement failed on ' + str(M))
            success=success+1
            if success==2:
                print(str(datetime.now()) + 'AS7341 measurement failed twice on ' + str(M) + ', setting unity values')
                sysData[M]['AS7341']['current']['ADC0']=1
                DACS=['ADC1', 'ADC2', 'ADC3', 'ADC4', 'ADC5']
                for DAC in DACS:
                    sysData[M]['AS7341']['current'][DAC]=0

    output=[0.0,0.0,0.0,0.0,0.0,0.0]
    index=0
    DACS=['ADC0', 'ADC1', 'ADC2', 'ADC3', 'ADC4', 'ADC5']
    for wavelength in wavelengths:
        if wavelength != "OFF":
            output[index]=sysData[M]['AS7341']['current'][DACS[index]]
        index=index+1

    return output


def GetTransmission(M,item,wavelengths,Gain,ISteps):
    #Gets light transmission through sample by turning on light, measuring, turning off light.
    global sysData
    M=str(M)
    SetOutputOn(M,item,1)
    output=GetLight(M,wavelengths,Gain,ISteps)
    SetOutputOn(M,item,0)
    return output




@application.route("/SetCustom/<Program>/<Status>",methods=['POST'])
def SetCustom(Program,Status):
    #Turns a custom program on/off.
	
    global sysData
    M=sysItems['UIDevice']
    item="Custom"
    if sysData[M][item]['ON']==1:
        sysData[M][item]['ON']=0
    else:
        sysData[M][item]['Program']=str(Program)
        sysData[M][item]['Status']=float(Status)
        sysData[M][item]['ON']=1
        sysData[M][item]['param1']=0.0 #Thus parameters get reset each time you restart your program.
        sysData[M][item]['param2']=0.0
        sysData[M][item]['param3']=0.0
    return('',204)
		
        
def CustomProgram(M):
    #Runs a custom program, some examples are included. You can remove/edit this function as you see fit.
    #Note that the custom programs (as set up at present) use an external .csv file with input parameters. THis is done to allow these parameters to easily be varied on the fly. 
    global sysData
    M=str(M)
    program=sysData[M]['Custom']['Program']
    #Subsequent few lines reads in external parameters from a file if you are using any.
    fname='InputParameters_' + str(M)+'.csv'
	
    with open(fname, 'rb') as f:
        reader = csv.reader(f)
        listin = list(reader)
    Params=listin[0]
    addTerminal(M,'Running Program = ' + str(program) + ' on device ' + str(M))
	
	
    if (program=="C1"): #Optogenetic Integral Control Program
        integral=0.0 #Integral in integral controller
        green=0.0 #Intensity of Green actuation 
        red=0.0 #Intensity of red actuation.
        GFPNow=sysData[M]['FP1']['Emit1']
        GFPTarget=sysData[M]['Custom']['Status'] #This is the controller setpoint.
        error=GFPTarget-GFPNow
        if error>0.0075:
            green=1.0
            red=0.0
            sysData[M]['Custom']['param3']=0.0 
        elif error<-0.0075:
            green=0.0
            red=1.0
            sysData[M]['Custom']['param3']=0.0
        else:
            red=1.0
            balance=float(Params[0]) #our guess at green light level to get 50% expression.
            KI=float(Params[1])
            KP=float(Params[2])
            integral=sysData[M]['Custom']['param3']+error*KI
            green=balance+KP*error+integral
            sysData[M]['Custom']['param3']=integral
        

        GreenThread=Thread(target = CustomLEDCycle, args=(M,'LEDD',green))
        GreenThread.setDaemon(True)
        GreenThread.start();
        RedThread=Thread(target = CustomLEDCycle, args=(M,'LEDF',red))
        RedThread.setDaemon(True)
        RedThread.start();
        sysData[M]['Custom']['param1']=green
        sysData[M]['Custom']['param2']=red
        addTerminal(M,'Program on %s = ' % M + str(program) + ' green= ' + str(green)+ ' red= ' + str(red) + ' integral= ' + str(integral))
	
    elif (program=="C2"): #UV Integral Control Program
        integral=0.0 #Integral in integral controller
        UV=0.0 #Intensity of Green actuation 
        GrowthRate=sysData[M]['GrowthRate']['current']
        GrowthTarget=sysData[M]['Custom']['Status'] #This is the controller setpoint.
        error=GrowthTarget-GrowthRate
        KP=float(Params[0]) #Past data suggest value of ~0.005
        KI=float(Params[1]) #Past data suggest value of ~2e-5
        integral=sysData[M]['Custom']['param2']+error*KI
        if(integral>0):
            integral=0.0
        sysData[M]['Custom']['param2']=integral
        UV=-1.0*(KP*error+integral)
        sysData[M]['Custom']['param1']=UV
        SetOutputTarget(M,'UV',UV)
        SetOutputOn(M,'UV',1)
        addTerminal(M,'Program on %s= ' % M + str(program) + ' UV= ' + str(UV)+  ' integral= ' + str(integral))
        
    elif (program=="C3"): #UV Integral Control Program Mk 2
        integral=sysData[M]['Custom']['param2'] #Integral in integral controller
        integral2=sysData[M]['Custom']['param3'] #Second integral controller
        UV=0.0 #Intensity of UV
        GrowthRate=sysData[M]['GrowthRate']['current']
        GrowthTarget=sysData[M]['Custom']['Status'] #This is the controller setpoint.
        error=GrowthTarget-GrowthRate
        KP=float(Params[0]) #Past data suggest value of ~0.005
        KI=float(Params[1]) #Past data suggest value of ~2e-5
        KI2=float(Params[2])
        integral=sysData[M]['Custom']['param2']+error*KI
        if(integral>0):
            integral=0.0
            
        if(abs(error)<0.3): #This is a second high-gain integrator which only gets cranking along when we are close to the target.
            integral2=sysData[M]['Custom']['param3']+error*KI2
        if(integral2>0):
            integral2=0.0
            
        sysData[M]['Custom']['param2']=integral
        sysData[M]['Custom']['param3']=integral2
        UV=-1.0*(KP*error+integral+integral2)
        m=50.0
        UV=(1.0/m)*(math.exp(m*UV)-1.0) #Basically this is to force the UV level to increase exponentially!
        sysData[M]['Custom']['param1']=UV
        SetOutputTarget(M,'UV',UV)
        SetOutputOn(M,'UV',1)
        addTerminal(M,'Program on %s = ' % M + str(program) + ' UV= ' + str(UV)+  ' integral= ' + str(integral))
    elif (program=="C4"): #UV Integral Control Program Mk 4
        rategain=float(Params[0]) 
        timept=sysData[M]['Custom']['Status'] #This is the timestep as we follow in minutes
        
        UV=0.001*math.exp(timept*rategain) #So we just exponentialy increase UV over time!
        sysData[M]['Custom']['param1']=UV
        SetOutputTarget(M,'UV',UV)
        SetOutputOn(M,'UV',1)
        
        timept=timept+1
        sysData[M]['Custom']['Status']=timept
            
    elif (program=="C5"): #UV Dosing program
        timept=int(sysData[M]['Custom']['Status']) #This is the timestep as we follow in minutes
        sysData[M]['Custom']['Status']=timept+1 #Increment time as we have entered the loop another time!
        
        Pump2Ontime=sysData[M]['Experiment']['cycleTime']*1.05*abs(sysData[M]['Pump2']['target'])*sysData[M]['Pump2']['ON']+0.5 #The amount of time Pump2 is going to be on for following RegulateOD above.
        time.sleep(Pump2Ontime) #Pause here is to prevent output pumping happening at the same time as stirring.
        
        timelength=300 #Time between doses in minutes
        if(timept%timelength==2): #So this happens every 5 hours!
            iters=(timept//timelength)
            Dose0=float(Params[0])
            Dose=Dose0*(2.0**float(iters)) #UV Dose, in terms of amount of time UV shoudl be left on at 1.0 intensity.
            print(str(datetime.now()) + ' Gave dose ' + str(Dose) + " at iteration " + str(iters) + " on device " + str(M))
            
            if (Dose<30.0):  
                powerlvl=Dose/30.0
                SetOutputTarget(M,'UV',powerlvl)
                Dose=30.0
            else:    
                SetOutputTarget(M,'UV',1.0) #Ensure UV is on at aopropriate intensity
                
            SetOutputOn(M,'UV',1) #Activate UV
            time.sleep(Dose) #Wait for dose to be administered
            SetOutputOn(M,'UV',0) #Deactivate UV
            
    elif (program=="C6"): #UV Dosing program 2 - constant value!
        timept=int(sysData[M]['Custom']['Status']) #This is the timestep as we follow in minutes
        sysData[M]['Custom']['Status']=timept+1 #Increment time as we have entered the loop another time!
        
        Pump2Ontime=sysData[M]['Experiment']['cycleTime']*1.05*abs(sysData[M]['Pump2']['target'])*sysData[M]['Pump2']['ON']+0.5 #The amount of time Pump2 is going to be on for following RegulateOD above.
        time.sleep(Pump2Ontime) #Pause here is to prevent output pumping happening at the same time as stirring.
    
        timelength=300 #Time between doses in minutes
        if(timept%timelength==2): #So this happens every 5 hours!
            iters=(timept//timelength)
            if iters>3:
                iters=3
                
            Dose0=float(Params[0])
            Dose=Dose0*(2.0**float(iters)) #UV Dose, in terms of amount of time UV shoudl be left on at 1.0 intensity.
            print(str(datetime.now()) + ' Gave dose ' + str(Dose) + " at iteration " + str(iters) + " on device " + str(M))
              
            if (Dose<30.0):  
                powerlvl=Dose/30.0
                SetOutputTarget(M,'UV',powerlvl)
                Dose=30.0
            else:    
                SetOutputTarget(M,'UV',1.0) #Ensure UV is on at aopropriate intensity
            
            SetOutputOn(M,'UV',1) #Activate UV
            time.sleep(Dose) #Wait for dose to be administered
            SetOutputOn(M,'UV',0) #Deactivate UV
                
                
    
    return

def CustomLEDCycle(M,LED,Value):
    #This function cycles LEDs for a fraction of 30 seconds during an experiment.
    global sysData
    M=str(M)
    if (Value>1.0):
        Value=1.0
        
    if (Value>0.0):
        SetOutputOn(M,LED,1)
        time.sleep(Value*30.0)#Sleep whatever fraction of 30 seconds we are interested in
        SetOutputOn(M,LED,0)
        
    return

        

@application.route("/SetLightActuation/<Excite>",methods=['POST'])
def SetLightActuation(Excite):
    #Basic function used to set which LED is used for optogenetics.
    global sysData
    M=sysItems['UIDevice']
    item="Light"
    if sysData[M][item]['ON']==1:
        sysData[M][item]['ON']=0
        return ('', 204)
    else:
        sysData[M][item]['Excite']=str(Excite)
        sysData[M][item]['ON']=1
        return('',204)
        
        
        
def LightActuation(M,toggle):
    #Another optogenetic function, turning LEDs on/off during experiment as appropriate.
    global sysData
    M=str(M)
    toggle=int(toggle)
    LEDChoice=sysData[M]['Light']['Excite']
    if (toggle==1 and sysData[M]['Light']['ON']==1):
        SetOutputOn(M,LEDChoice,1)
    else:
        SetOutputOn(M,LEDChoice,0)
    return 0


@application.route("/CharacteriseDevice/<M>/<Program>",methods=['POST'])     
def CharacteriseDevice(M,Program): 
    # THis umbrella function is used to run the actual characteriseation function in a thread to prevent GUnicorn worker timeout.
    Program=str(Program)
    if (Program=='C1'):
        cthread=Thread(target = CharacteriseDevice2, args=(M))
        cthread.setDaemon(True)
        cthread.start()
    
    return('',204)
        
        
        
def CharacteriseDevice2(M):
    global sysData
    global sysItems
    print('In1')
    M=str(M)
    if (M=="0"):
        M=sysItems['UIDevice']
        
    result= { 'LEDA' : {'nm410' : [],'nm440' : [],'nm470' : [],'nm510' : [],'nm550' : [],'nm583' : [],'nm620' : [],'nm670' : [],'CLEAR' : []},
        'LEDB' : {'nm410' : [],'nm440' : [],'nm470' : [],'nm510' : [],'nm550' : [],'nm583' : [],'nm620' : [],'nm670' : [],'CLEAR' : []},
        'LEDC' : {'nm410' : [],'nm440' : [],'nm470' : [],'nm510' : [],'nm550' : [],'nm583' : [],'nm620' : [],'nm670' : [],'CLEAR' : []},
        'LEDD' : {'nm410' : [],'nm440' : [],'nm470' : [],'nm510' : [],'nm550' : [],'nm583' : [],'nm620' : [],'nm670' : [],'CLEAR' : []},
        'LEDE' : {'nm410' : [],'nm440' : [],'nm470' : [],'nm510' : [],'nm550' : [],'nm583' : [],'nm620' : [],'nm670' : [],'CLEAR' : []},
        'LEDF' : {'nm410' : [],'nm440' : [],'nm470' : [],'nm510' : [],'nm550' : [],'nm583' : [],'nm620' : [],'nm670' : [],'CLEAR' : []},
        'LEDG' : {'nm410' : [],'nm440' : [],'nm470' : [],'nm510' : [],'nm550' : [],'nm583' : [],'nm620' : [],'nm670' : [],'CLEAR' : []},
        'LASER650' : {'nm410' : [],'nm440' : [],'nm470' : [],'nm510' : [],'nm550' : [],'nm583' : [],'nm620' : [],'nm670' : [],'CLEAR' : []},
        }
        
        
    print('Got in!')   
    bands=['nm410' ,'nm440','nm470','nm510','nm550','nm583','nm620','nm670','CLEAR']    
    powerlevels=[0,0.01,0.02,0.03,0.04,0.05,0.06,0.07,0.08,0.09,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0]
    items= ['LEDA','LEDB','LEDC','LEDD','LEDE','LEDF','LEDG','LASER650']
    gains=['x4','x4','x4','x4','x4','x4','x4','x1']
    gi=-1
    for item in items:
        gi=gi+1
        for power in powerlevels:
            SetOutputTarget(M,item,power)
            SetOutputOn(M,item,1)
            GetSpectrum(M,gains[gi])
            SetOutputOn(M,item,0)
            print(item + ' ' + str(power))
            for band in bands:
                result[item][band].append(int(sysData[M]['AS7341']['spectrum'][band]))
            addTerminal(M,'Measured Item on %s = ' % M + str(item) + ' at power ' + str(power))
            time.sleep(0.05)
                
    
    filename = 'characterisation_data_' + M + '.txt'
    f = open(filename,'w')
    simplejson.dump(result,f)
    f.close()
    return

  
        
        

def I2CCom(M,device,rw,hl,data1,data2,SMBUSFLAG):
    #Function used to manage I2C bus communications for ALL devices.
    M=str(M) #Turbidostat to write to
    device=str(device) #Name of device to be written to
    rw=int(rw) #1 if read, 0 if write
    hl=int(hl) #8 or 16
    SMBUSFLAG=int(SMBUSFLAG) # If this flag is set to 1 it means we are communuicating with an SMBUs device.
    data1=int(data1) #First data/register 
    if hl<20:
        data2=int(data2) #First data/register 
    global sysItems
    global sysData
    
    global sysDevices
    if(sysData[M]['present']==0): #Something stupid has happened in software if this is the case!
        critical_msg = ' Trying to communicate with M%s absent device - bug in software!. ' \
                       'Disabling hardware and software!' % M
        print(str(datetime.now()) + critical_msg)
        application.logger.critical(critical_msg)
        sysItems['Watchdog']['ON']=0 #Basically this will crash all the electronics and the software.
        out=0
        tries=-1
        os._exit(4)
    
    #cID=str(M)+str(device)+'d'+str(data1)+'d'+str(data2)  # This is an ID string for the communication that we are trying to send - not used at present
    #Any time a thread gets to this point it will wait until the lock is free. Then, only one thread at a time will advance. 
    lock.acquire()

    
    #We now connect the multiplexer to the appropriate device to allow digital communications.
    tries=0
    while(tries!=-1):
        try:
            sysItems['Multiplexer']['device'].write8(int(0x00),int(sysItems['Multiplexer'][M],2)) #We have established connection to correct device. 
            check=(sysItems['Multiplexer']['device'].readRaw8()) #We check that the Multiplexer is indeed connected to the correct channel.
            if(check==int(sysItems['Multiplexer'][M],2)):
                tries=-1
                application.logger.debug('Connection to mux on %s to channel %s has been established' % (M, check))
            else:
                tries=tries+1
                time.sleep(0.02)
                warn_msg = ' Multiplexer didnt switch ' + str(tries) + " times on " + str(M)
                print(str(datetime.now()) + warn_msg)
                application.logger.warning(warn_msg)
        except: #If there is an error in the above.
            tries=tries+1
            time.sleep(0.02)
            warn_msg = ' Failed Multiplexer Comms ' + str(tries) + " times"
            print(str(datetime.now()) + warn_msg)
            application.logger.warning(warn_msg)

            if (tries>2):
                try:
                    sysItems['Multiplexer']['device'].write8(int(0x00),int(0x00)) #Disconnect multiplexer.
                    warn_msg = 'Disconnected multiplexer on ' + str(M) + ', trying to connect again.'
                    print(warn_msg)
                    application.logger.warning(warn_msg)
                except:
                    warn_msg = 'Failed to recover multiplexer on device ' + str(M)
                    print(warn_msg)
                    application.logger.warning(warn_msg)
            if tries==5:
                time.sleep(0.2)
                
        if tries>20: #If it has failed a number of times then likely something is seriously wrong, so we crash the software.
            sysItems['Watchdog']['ON']=0 #Basically this will crash all the electronics and the software. 
            out=0
            critical_msg = 'Failed to communicate to Multiplexer %d times. Disabling hardware and software!' % 20
            print(critical_msg)
            application.logger.critical(critical_msg)
            tries=-1
            os._exit(4)
    
    

    
    time.sleep(0.0005)
    out=0;
    tries=0
    
    while(tries!=-1): #We now do appropriate read/write on the bus.
        try:
            if SMBUSFLAG==0:
                if rw==1:
                    if hl==8:
                        out=int(sysDevices[M][device]['device'].readU8(data1))
                    elif(hl==16):
                        out=int(sysDevices[M][device]['device'].readU16(data1,data2))
                else:
                    if hl==8:
                        sysDevices[M][device]['device'].write8(data1,data2)
                        out=1
                    elif(hl==16):
                        sysDevices[M][device]['device'].write16(data1,data2)
                        out=1
                    
            elif SMBUSFLAG==1:
                out=sysDevices[M][device]['device'].read_word_data(sysDevices[M][device]['address'],data1)
            tries=-1
        except: #If the above fails then we can try again (a limited number of times)
            tries=tries+1
            
            if (device!="ThermometerInternal"):
                warn_msg = ' Failed ' + str(device) + ' comms ' + str(tries) + " times on device " + str(M)
                print(str(datetime.now()) + warn_msg)
                application.logger.warning(warn_msg)
                time.sleep(0.02)
            if (device=='AS7341'):
                warn_msg = ' Failed  AS7341 in I2CCom while trying to send ' + str(data1) + " and " + str(data2)
                print(str(datetime.now()) + warn_msg)
                application.logger.warning(warn_msg)
                out=-1
                tries=-1

        if (tries>2 and device=="ThermometerInternal"): #We don't allow the internal thermometer to fail, since this is what we are using to see if devices are plugged in at all.
            out=0
            sysData[M]['present']=0
            tries=-1
        if tries >= application.config['DEVICE_COMM_FAILURE_THRESHOLD']: #In this case something else has gone wrong, so we panic.
            sysItems['Watchdog']['ON']=0 #Basically this will crash all the electronics and the software. 
            out=0
            sysData[M]['present']=0
            critical_msg = 'Failed to communicate to a device %d times. Disabling hardware and software!' % application.config['DEVICE_COMM_FAILURE_THRESHOLD']
            print(critical_msg)
            application.logger.critical(critical_msg)
            tries=-1
            os._exit(4)
                
    time.sleep(0.0005)
    

    
    try:
        sysItems['Multiplexer']['device'].write8(int(0x00),int(0x00)) #Disconnect multiplexer with each iteration. 
    except:
        warn_msg = 'Failed to disconnect multiplexer on device ' + str(M)
        print(warn_msg)
        application.logger.warning(warn_msg)


    
    lock.release() #Bus lock is released so next command can occur.
    
    return(out)
    
    
    

@application.route("/CalibrateOD/<item>/<M>/<value>/<value2>",methods=['POST'])
def CalibrateOD(M,item,value,value2):
    #Used to calculate calibration value for OD measurements.
    global sysData
    item = str(item)
    ODRaw = float(value)
    ODActual = float(value2)
    M=str(M)
    if (M=="0"):
        M=sysItems['UIDevice']
        
    device=sysData[M]['OD']['device']
    if (device=='LASER650'):
        a=sysData[M]['OD0']['LASERa']#Retrieve the calibration factors for OD.
        b=sysData[M]['OD0']['LASERb'] 
        if (ODActual<0):
            ODActual=0
            print("You put a negative OD into calibration! Setting it to 0")
        
        raw=((ODActual/a +  (b/(2*a))**2)**0.5) - (b/(2*a)) #THis is performing the inverse function of the quadratic OD calibration.
        OD0=(10.0**raw)*ODRaw
        if (OD0<sysData[M][item]['min']):
            OD0=sysData[M][item]['min']
            print('OD calibration value seems too low?!')

        if (OD0>sysData[M][item]['max']):
            OD0=sysData[M][item]['max']
            print('OD calibration value seems too high?!')

    
        sysData[M][item]['target']=OD0
        print("Calibrated OD")
    elif (device=='LEDF'):
        a=sysData[M]['OD0']['LEDFa']#Retrieve the calibration factors for OD.
        
        if (ODActual<0):
            ODActual=0
            print("You put a negative OD into calibration! Setting it to 0")
        if (M=='M0'):
            CF=1299.0
        elif (M=='M1'):
            CF=1206.0
        elif (M=='M2'):
            CF=1660.0
        elif (M=='M3'):
            CF=1494.0
            
        raw=(ODActual)/a  #THis is performing the inverse function of the linear OD calibration.
        OD0=ODRaw - raw*CF
        OD0=ODRaw/ODActual
        print(OD0)
    
        if (OD0<sysData[M][item]['min']):
            OD0=sysData[M][item]['min']
            print('OD calibration value seems too low?!')
        if (OD0>sysData[M][item]['max']):
            OD0=sysData[M][item]['max']
            print('OD calibration value seems too high?!')
    
        sysData[M][item]['target']=OD0
        print("Calibrated OD")
    elif (device=='LEDA'):
        a=sysData[M]['OD0']['LEDAa']#Retrieve the calibration factors for OD.
        
        if (ODActual<0):
            ODActual=0
            print("You put a negative OD into calibration! Setting it to 0")
        if (M=='M0'):
            CF=422
        elif (M=='M1'):
            CF=379
        elif (M=='M2'):
            CF=574
        elif (M=='M3'):
            CF=522
            
        raw=(ODActual)/a  #THis is performing the inverse function of the linear OD calibration.
        OD0=ODRaw - raw*CF
        OD0=ODRaw/ODActual
        print(OD0)
    
        if (OD0<sysData[M][item]['min']):
            OD0=sysData[M][item]['min']
            print('OD calibration value seems too low?!')
        if (OD0>sysData[M][item]['max']):
            OD0=sysData[M][item]['max']
            print('OD calibration value seems too high?!')
    
        sysData[M][item]['target']=OD0
        print("Calibrated OD")
        
    return ('', 204)    
    
    
        
@application.route("/MeasureOD/<M>",methods=['POST'])
def MeasureOD(M):
    #Measures laser transmission and calculates calibrated OD from this.
    global sysData
    global sysItems
    M=str(M)
    if (M=="0"):
        M=sysItems['UIDevice']
    device=sysData[M]['OD']['device']
    if (device=='LASER650'):
        out=GetTransmission(M,'LASER650',['CLEAR'],1,255)
        sysData[M]['OD0']['raw']=float(out[0])
    
        a=sysData[M]['OD0']['LASERa']#Retrieve the calibration factors for OD.
        b=sysData[M]['OD0']['LASERb'] 
        try:
            raw=math.log10(sysData[M]['OD0']['target']/sysData[M]['OD0']['raw'])
            sysData[M]['OD']['current']=raw*b + raw*raw*a
        except:
            sysData[M]['OD']['current']=0;
            print(str(datetime.now()) + ' OD Measurement exception on ' + str(device))
    elif (device=='LEDF'):
        out=GetTransmission(M,'LEDF',['CLEAR'],7,255)

        sysData[M]['OD0']['raw']=out[0]
        a=sysData[M]['OD0']['LEDFa']#Retrieve the calibration factors for OD.
        try:
            if (M=='M0'):
                CF=1299.0
            elif (M=='M1'):
                CF=1206.0
            elif (M=='M2'):
                CF=1660.0
            elif (M=='M3'):
                CF=1494.0
            raw=out[0]/CF - sysData[M]['OD0']['target']/CF
            raw=out[0]/sysData[M]['OD0']['target']
            sysData[M]['OD']['current']=raw
        except:
            sysData[M]['OD']['current']=0;
            print(str(datetime.now()) + ' OD Measurement exception on ' + str(device))

    elif (device=='LEDA'):
        out=GetTransmission(M,'LEDA',['CLEAR'],7,255)

        sysData[M]['OD0']['raw']=out[0]
        a=sysData[M]['OD0']['LEDAa']#Retrieve the calibration factors for OD.
        try:
            if (M=='M0'):
                CF=422.0
            elif (M=='M1'):
                CF=379.0
            elif (M=='M2'):
                CF=574.0
            elif (M=='M3'):
                CF=522.0
            raw=out[0]/CF - sysData[M]['OD0']['target']/CF
            raw=out[0]/sysData[M]['OD0']['target']
            #sysData[M]['OD']['current']=raw*a
            sysData[M]['OD']['current']=raw
        except:
            sysData[M]['OD']['current']=0;
            print(str(datetime.now()) + ' OD Measurement exception on ' + str(device))
    
    return ('', 204)  
    

@application.route("/MeasureFP/<M>",methods=['POST'])    
def MeasureFP(M):
    #Responsible for measuring each of the active Fluorescent proteins.
    global sysData
    M=str(M)
    if (M=="0"):
        M=sysItems['UIDevice']
    for FP in ['FP1','FP2','FP3']:
        if sysData[M][FP]['ON']==1:
            Gain=int(sysData[M][FP]['Gain'][1:])
            out=GetTransmission(M,sysData[M][FP]['LED'],[sysData[M][FP]['BaseBand'],sysData[M][FP]['Emit1Band'],sysData[M][FP]['Emit2Band']],Gain,255)
            sysData[M][FP]['Base']=float(out[0])
            if (sysData[M][FP]['Base']>0):
                sysData[M][FP]['Emit1']=float(out[1])/sysData[M][FP]['Base']
                sysData[M][FP]['Emit2']=float(out[2])/sysData[M][FP]['Base']
            else:#This might happen if you try to measure in CLEAR whilst also having CLEAR as baseband! 
                sysData[M][FP]['Emit1']=float(out[1]) 
                sysData[M][FP]['Emit2']=float(out[2])

    return ('', 204)      
    

    
    
@application.route("/MeasureTemp/<which>/<M>",methods=['POST'])
def MeasureTemp(M,which): 
    #Used to measure temperature from each thermometer.
    global sysData
    global sysItems
   
    if (M=="0"):
        M=sysItems['UIDevice']
    M=str(M)
    which='Thermometer' + str(which)
    if (which=='ThermometerInternal' or which=='ThermometerExternal'):
        getData=I2CCom(M,which,1,16,0x05,0,0)
        getDataBinary=bin(getData)
        tempData=getDataBinary[6:]
        temperature=float(int(tempData,2))/16.0
    elif(which=='ThermometerIR'):
        getData=I2CCom(M,which,1,0,0x07,0,1)
        temperature = (getData*0.02) - 273.15

    if sysData[M]['present']==0:
        temperature=0.0
    if temperature>100.0:#It seems sometimes the IR thermometer returns a value of 1000 due to an error. This prevents that.
        temperature=sysData[M][which]['current']
    sysData[M][which]['current']=temperature
    return ('', 204) 
    


    
def setPWM(M,device,channels,fraction,ConsecutiveFails):
    #Sets up the PWM chip (either the one in the reactor or on the pump board)
    global sysItems
    application.logger.debug('PWM command: %s device: %s channels: %s fractions: %s ConsecutiveFails: %d' %
                            (M, device, channels, fraction, ConsecutiveFails))
    if sysDevices[M][device]['startup']==0: #The following boots up the respective PWM device to the correct frequency. Potentially there is a bug here; if the device loses power after this code is run for the first time it may revert to default PWM frequency.
        I2CCom(M,device,0,8,0x00,0x11,0) #Turns off device.
        I2CCom(M,device,0,8,0xfe,sysDevices[M][device]['frequency'],0) #Sets frequency of PWM oscillator. 
        sysDevices[M][device]['startup']=1
    I2CCom(M,device,0,8,0x00,0x01,0) #Turns device on for sure! 
        
    
    timeOn=int(fraction*4095.99)
    I2CCom(M,device,0,8,channels['ONL'],0x00,0)
    I2CCom(M,device,0,8,channels['ONH'],0x00,0)
    
    OffVals=bin(timeOn)[2:].zfill(12)
    HighVals='0000' + OffVals[0:4]
    LowVals=OffVals[4:12]
    
    I2CCom(M,device,0,8,channels['OFFL'],int(LowVals,2),0)
    I2CCom(M,device,0,8,channels['OFFH'],int(HighVals,2),0)
    
    CheckLow=I2CCom(M,device,1,8,channels['OFFL'],-1,0)
    CheckHigh=I2CCom(M,device,1,8,channels['OFFH'],-1,0)
    CheckLowON=I2CCom(M,device,1,8,channels['ONL'],-1,0)
    CheckHighON=I2CCom(M,device,1,8,channels['ONH'],-1,0)
    
    if(CheckLow!=(int(LowVals,2)) or CheckHigh!=(int(HighVals,2)) or CheckHighON!=int(0x00) or CheckLowON!=int(0x00)): #We check to make sure it has been set to appropriate values.
        ConsecutiveFails=ConsecutiveFails+1
        print(str(datetime.now()) + ' Failed transmission test on ' + str(device) + ' ' + str(ConsecutiveFails) + ' times consecutively on device '  + str(M) )
        if ConsecutiveFails>10:
            sysItems['Watchdog']['ON']=0 #Basically this will crash all the electronics and the software.
            error_msg = 'Failed to communicate to PWM %d times. Disabling hardware and software!' % 10
            print(error_msg)
            application.logger.critical(error_msg)
            os._exit(4)
        else:
            time.sleep(0.1)
            sysItems['FailCount']=sysItems['FailCount']+1
            setPWM(M,device,channels,fraction,ConsecutiveFails)
    



def csvData(M):
    #Used to format current data and write a new row to CSV file output. Note if you want to record any additional parameters/measurements then they need to be added to this function.
    global sysData
    M=str(M)

    fieldnames = ['exp_time','od_measured','od_setpoint','od_zero_setpoint','thermostat_setpoint','heating_rate',
                  'internal_air_temp','external_air_temp','media_temp','opt_gen_act_int','pump_1_rate','pump_2_rate',
                  'pump_3_rate','pump_4_rate','media_vol','stirring_rate','LED_395nm_setpoint','LED_457nm_setpoint',
                  'LED_500nm_setpoint','LED_523nm_setpoint','LED_595nm_setpoint','LED_623nm_setpoint',
                  'LED_6500K_setpoint','laser_setpoint','LED_UV_int','FP1_base','FP1_emit1','FP1_emit2','FP2_base',
                  'FP2_emit1','FP2_emit2','FP3_base','FP3_emit1','FP3_emit2','custom_prog_param1','custom_prog_param2',
                  'custom_prog_param3','custom_prog_status','zigzag_target','growth_rate']

    row=[sysData[M]['time']['record'][-1],
        sysData[M]['OD']['record'][-1],
        sysData[M]['OD']['targetrecord'][-1],
        sysData[M]['OD0']['target'],
        sysData[M]['Thermostat']['record'][-1],
        sysData[M]['Heat']['target']*float(sysData[M]['Heat']['ON']),
        sysData[M]['ThermometerInternal']['record'][-1],
        sysData[M]['ThermometerExternal']['record'][-1],
        sysData[M]['ThermometerIR']['record'][-1],
        sysData[M]['Light']['record'][-1],
        sysData[M]['Pump1']['record'][-1],
        sysData[M]['Pump2']['record'][-1],
        sysData[M]['Pump3']['record'][-1],
        sysData[M]['Pump4']['record'][-1],
        sysData[M]['Volume']['target'],
        sysData[M]['Stir']['target']*sysData[M]['Stir']['ON'],]
    for LED in ['LEDA','LEDB','LEDC','LEDD','LEDE','LEDF','LEDG','LASER650']:
        row=row+[sysData[M][LED]['target']]
    row=row+[sysData[M]['UV']['target']*sysData[M]['UV']['ON']]
    for FP in ['FP1','FP2','FP3']:
        if sysData[M][FP]['ON']==1:
            row=row+[sysData[M][FP]['Base']]
            row=row+[sysData[M][FP]['Emit1']]
            row=row+[sysData[M][FP]['Emit2']]
        else:
            row=row+([0.0, 0.0, 0.0])
    
    row=row+[sysData[M]['Custom']['param1']*float(sysData[M]['Custom']['ON'])]
    row=row+[sysData[M]['Custom']['param2']*float(sysData[M]['Custom']['ON'])]
    row=row+[sysData[M]['Custom']['param3']*float(sysData[M]['Custom']['ON'])]
    row=row+[sysData[M]['Custom']['Status']*float(sysData[M]['Custom']['ON'])]
    row=row+[sysData[M]['Zigzag']['target']*float(sysData[M]['Zigzag']['ON'])]
    row=row+[sysData[M]['GrowthRate']['current']*sysData[M]['Zigzag']['ON']]
   
   
	#Following can be uncommented if you are recording ALL spectra for e.g. biofilm experiments
    #bands=['nm410' ,'nm440','nm470','nm510','nm550','nm583','nm620','nm670','CLEAR','NIR']    
    #items= ['LEDA','LEDB','LEDC','LEDD','LEDE','LEDF','LEDG','LASER650']
    #for item in items:
    #   for band in bands:
    #       row=row+[sysData[M]['biofilm'][item][band]]

    if len(row) != len(fieldnames):
        raise ValueError('CSV_WRITER: mismatch between column num and header num')

    filename = sysData[M]['Experiment']['startTime'] + '_' + M + '_data' + '.csv'
    filename=filename.replace(":","_")

    lock.acquire() #We are avoiding writing to a file at the same time as we do digital communications, since it might potentially cause the computer to lag and consequently data transfer to fail.
    if os.path.isfile(filename) is False:
        with open(filename, 'a') as csvFile:
            writer = csv.writer(csvFile)
            writer.writerow(fieldnames)

    with open(filename, 'a') as csvFile: # Here we append the above row to our CSV file.
        writer = csv.writer(csvFile)
        writer.writerow(row)
    csvFile.close()        
    lock.release() 
    

def downsample(M):
    #In order to prevent the UI getting too laggy, we downsample the stored data every few hours. Note that this doesnt downsample that which has already been written to CSV, so no data is ever lost.
    global sysData
    M=str(M)
    
    
    
    
    #We now generate a new time vector which is downsampled at half the rate of the previous one
    time=np.asarray(sysData[M]['time']['record'])
    newlength=int(round(len(time)/2,2)-1)
    tnew=np.linspace(time[0],time[-11],newlength)
    tnew=np.concatenate([tnew,time[-10:]])
    
    #In the following we make a new array, index, which has the indices at which we want to resample our existing data vectors.
    i=0
    index=np.zeros((len(tnew),),dtype=int)
    for timeval in tnew:
        idx = np.searchsorted(time, timeval, side="left")
        if idx > 0 and (idx == len(time) or np.abs(timeval - time[idx-1]) < np.abs(timeval - time[idx])):
            index[i]=idx-1
        else:
            index[i]=idx
        i=i+1
    
 
    sysData[M]['time']['record']=downsampleFunc(sysData[M]['time']['record'],index)
    sysData[M]['OD']['record']=downsampleFunc(sysData[M]['OD']['record'],index)
    sysData[M]['OD']['targetrecord']=downsampleFunc(sysData[M]['OD']['targetrecord'],index)
    sysData[M]['Thermostat']['record']=downsampleFunc(sysData[M]['Thermostat']['record'],index)
    sysData[M]['Light']['record']=downsampleFunc(sysData[M]['Light']['record'],index)
    sysData[M]['ThermometerInternal']['record']=downsampleFunc(sysData[M]['ThermometerInternal']['record'],index)
    sysData[M]['ThermometerExternal']['record']=downsampleFunc(sysData[M]['ThermometerExternal']['record'],index)
    sysData[M]['ThermometerIR']['record']=downsampleFunc(sysData[M]['ThermometerIR']['record'],index)
    sysData[M]['Pump1']['record']=downsampleFunc(sysData[M]['Pump1']['record'],index)
    sysData[M]['Pump2']['record']=downsampleFunc(sysData[M]['Pump2']['record'],index)
    sysData[M]['Pump3']['record']=downsampleFunc(sysData[M]['Pump3']['record'],index)
    sysData[M]['Pump4']['record']=downsampleFunc(sysData[M]['Pump4']['record'],index)
    sysData[M]['GrowthRate']['record']=downsampleFunc(sysData[M]['GrowthRate']['record'],index)
    
        
    for FP in ['FP1','FP2','FP3']:
        sysData[M][FP]['BaseRecord']=downsampleFunc(sysData[M][FP]['BaseRecord'],index)
        sysData[M][FP]['Emit1Record']=downsampleFunc(sysData[M][FP]['Emit1Record'],index)
        sysData[M][FP]['Emit2Record']=downsampleFunc(sysData[M][FP]['Emit2Record'],index)
        
def downsampleFunc(datain,index):
    #This function Is used to downsample the arrays, taking the points selected by the index vector.
    datain=list(datain)
    newdata=[]
    newdata=np.zeros((len(index),),dtype=float)

    i=0
    for loc in list(index):
        newdata[i]=datain[int(loc)]
        
        i=i+1
    return list(newdata)
    
        



def RegulateOD(M):
    #Function responsible for turbidostat functionality (OD control)
    global sysData
    global sysItems
    M=str(M)
    
    if (sysData[M]['Zigzag']['ON']==1):
        TargetOD=sysData[M]['OD']['target']
        Zigzag(M) #Function that calculates new target pump rates, and sets pumps to desired rates. 

    
    Pump1Current=abs(sysData[M]['Pump1']['target'])
    Pump2Current=abs(sysData[M]['Pump2']['target'])
    Pump1Direction=sysData[M]['Pump1']['direction']
    Pump2Direction=sysData[M]['Pump2']['direction']
    
    
    
    ODNow=sysData[M]['OD']['current']
    ODTarget=sysData[M]['OD']['target']
    if (ODTarget<=0): #There could be an error on the log operationif ODTarget is 0!
        ODTarget=0.000001
        
    errorTerm=ODTarget-ODNow
    Volume=sysData[M]['Volume']['target']
    
    PercentPerMin=4*60/Volume #Gain parameter to convert from pump rate to rate of OD reduction.

    if sysData[M]['Experiment']['cycles']<3:
        Pump1=0 #In first few cycles we do precisely no pumping.
    else:
        ODPast=sysData[M]['OD']['record'][-1]
        timeElapsed=((sysData[M]['time']['record'][-1])-(sysData[M]['time']['record'][-2]))/60.0 #Amount of time betwix measurements in minutes
        if (ODNow>0):
            try:
                NewGrowth = math.log((ODTarget)/(ODNow))/timeElapsed
            except:
                NewGrowth=0.0
        else:
            NewGrowth=0.0
            
        Pump1=-1.0*NewGrowth/PercentPerMin
        
        #Next Section is Integral Control
        ODerror=ODNow-ODTarget
        # Integrator 1 - resoponsible for short-term integration to overcome troubles if an input pump makes a poor seal.
        ODIntegral=sysData[M]['OD']['Integral']
        if ODerror<0.01:
            ODIntegral=0
        elif (abs(ODNow-ODPast)<0.05 and ODerror>0.025): #preventing massive accidental jumps causing trouble with this integral term.
            ODIntegral=ODIntegral+0.1*ODerror
        sysData[M]['OD']['Integral']=ODIntegral
        # Integrator 2 
        ODIntegral2=sysData[M]['OD']['Integral2']
        if (abs(ODerror)>0.1 and abs(ODNow-ODPast)<0.05):
            ODIntegral2=0
        elif (abs(ODNow-ODPast)<0.1):
            ODIntegral2=ODIntegral2+0.01*ODerror
            Pump1=Pump1*0.7 #This is essentially enforcing a smaller Proportional gain when we are near to OD setpoint.
        sysData[M]['OD']['Integral2']=ODIntegral2
        
        Pump1=Pump1+ODIntegral+ODIntegral2
        
        if (ODNow-ODPast)>0.04: #This is to counteract noisy jumps in OD measurements from causing mayhem in the regulation algorithm.
            Pump1=0.0

    #Make sure values are in appropriate range. We want to limit the maximum size of pump1 to prevent it from overflowing.
    if(Pump1>0.02):
        Pump1=0.02
    elif(Pump1<0):
        Pump1=0.0

    if(sysData[M]['Chemostat']['ON']==1):
        Pump1=float(sysData[M]['Chemostat']['p1'])

    #Set new Pump targets
    sysData[M]['Pump1']['target']=Pump1*Pump1Direction
    sysData[M]['Pump2']['target']=(Pump1*4+0.07)*Pump2Direction

    if(sysData[M]['Experiment']['cycles']%5==1): #Every so often we do a big output pump to make sure tubes are clear.
        sysData[M]['Pump2']['target']=0.25*sysData[M]['Pump2']['direction']
    
    
    
    
    if (sysData[M]['Experiment']['cycles']>15):
        #This section is to check if we have added any liquid recently, if not, then we dont run pump 2 since it won't be needed.
        pastpumping=abs(sysData[M]['Pump1']['target'])
        for pv in range(-10,-1):
            pastpumping=pastpumping+abs(sysData[M]['Pump1']['record'][pv])
        
        if pastpumping==0.0:
            sysData[M]['Pump2']['target']=0.0
            sysData[M]['Pump1']['target']=0.0 #This should be equal to 0 anyway.
        
        

    SetOutputOn(M,'Pump1',1)
    SetOutputOn(M,'Pump2',1)

        
    if (sysData[M]['Zigzag']['ON']==1): #If the zigzag growth estimation is running then we change OD setpoint appropriately.
        try:
            sysData[M]['OD']['target']=TargetOD
        except:
            print('Somehow you managed to activate Zigzag at a sub-optimal time')
            #Do nothing
 
    return
    
def Zigzag(M):
    #This function dithers OD in a "zigzag" pattern, and estimates growthrate. This function is only called when ZigZag mode is active.
    global sysData
    global sysItems
    M=str(M)
    centre=sysData[M]['OD']['target']
    current=sysData[M]['OD']['current']
    zig=sysData[M]['Zigzag']['Zig']
    iteration=sysData[M]['Experiment']['cycles']
	
    try:
        last=sysData[M]['OD']['record'][-1]
    except: #This will happen if you activate Zigzag in first control iteration!
        last=current
    
    if (current<centre-zig and last<centre):
        if(sysData[M]['Zigzag']['target']!=5.0):
            sysData[M]['Zigzag']['SwitchPoint']=iteration
        sysData[M]['Zigzag']['target']=5.0 #an excessively high OD value.
    elif (current>centre+zig and last>centre+zig):
        sysData[M]['Zigzag']['target']=centre-zig*1.5
        sysData[M]['Zigzag']['SwitchPoint']=iteration

    sysData[M]['OD']['target']=sysData[M]['Zigzag']['target']
	
    #Subsequent section is for growth estimation.
	
    TimeSinceSwitch=iteration-sysData[M]['Zigzag']['SwitchPoint']
    if (iteration>6 and TimeSinceSwitch>5): #The reason we wait a few minutes after starting growth is that new media may still be introduced, it takes a while for the growth to get going.
        dGrowthRate=(math.log(current)-math.log(last))*60.0 #Converting to units of 1/hour
        sysData[M]['GrowthRate']['current']=sysData[M]['GrowthRate']['current']*0.95 + dGrowthRate*0.05 #We are essentially implementing an online growth rate estimator with learning rate 0.05

    return



@application.route("/ExperimentReset",methods=['POST'])
def ExperimentReset():
    #Resets parameters/values of a given experiment.
    initialise(sysItems['UIDevice'])
    return ('', 204)   

@application.route("/Experiment/<value>/<M>",methods=['POST'])
def ExperimentStartStop(M,value):
    #Stops or starts an experiment. 
    global sysData
    global sysDevices
    global sysItems
    M=str(M)
    if (M=="0"):
        M=sysItems['UIDevice']
       
    value=int(value)
    #Turning it on involves keeping current pump directions,
    if (value and (sysData[M]['Experiment']['ON']==0)):
        
        sysData[M]['Experiment']['ON']=1
        addTerminal(M,'Experiment on %s Started' % M)
        
        if (sysData[M]['Experiment']['cycles']==0):
            now=datetime.now()
            timeString=now.strftime("%Y-%m-%d %H:%M:%S")
            sysData[M]['Experiment']['startTime']=timeString
            sysData[M]['Experiment']['startTimeRaw']=now
        
        sysData[M]['Pump1']['direction']=1.0 #Sets pumps to go forward.
        sysData[M]['Pump2']['direction']=1.0

        turnEverythingOff(M)
        
        SetOutputOn(M,'Thermostat',1)
        sysDevices[M]['Experiment']=Thread(target = runExperiment, args=(M,'placeholder'))
        sysDevices[M]['Experiment'].setDaemon(True)
        sysDevices[M]['Experiment'].start();
        
    else:
        sysData[M]['Experiment']['ON']=0
        sysData[M]['OD']['ON']=0
        addTerminal(M,'Experiment on %s Stopping at end of cycle' % M)
        SetOutputOn(M,'Pump1',0)
        SetOutputOn(M,'Pump2',0)
        SetOutputOn(M,'Stir',0)
        SetOutputOn(M,'Thermostat',0)
        
    return ('', 204)
    
    
    
def runExperiment(M,placeholder):
    #Primary function for running an automated experiment.
    M=str(M)
   
    global sysData
    global sysItems
    global sysDevices
    
    sysData[M]['Experiment']['threadCount']=(sysData[M]['Experiment']['threadCount']+1)%100
    currentThread=sysData[M]['Experiment']['threadCount']
        
    # Get time running in seconds
    now=datetime.now()
    elapsedTime=now-sysData[M]['Experiment']['startTimeRaw']
    elapsedTimeSeconds=round(elapsedTime.total_seconds(),2)
    sysData[M]['Experiment']['cycles']=sysData[M]['Experiment']['cycles']+1
    addTerminal(M,'Cycle ' + str(sysData[M]['Experiment']['cycles']) + ' on %s Started' % M)
    CycleTime=sysData[M]['Experiment']['cycleTime']

    SetOutputOn(M,'Stir',0) #Turning stirring off
    time.sleep(5.0) #Wait for liquid to settle.
    if (sysData[M]['Experiment']['ON']==0):
        turnEverythingOff(M)
        addTerminal(M,'Experiment on %s Stopped' % M)
        return
    
    sysData[M]['OD']['Measuring']=1 #Begin measuring - this flag is just to indicate that a measurement is currently being taken.
    
    # We now measure OD N times and take the average to reduce noise when in auto mode!
    ODV = 0.0
    for _ in range(0, application.config['NUMBER_OF_OD_MEASUREMENTS']-1):
        MeasureOD(M)
        ODV=ODV+sysData[M]['OD']['current']
        time.sleep(0.25)
    sysData[M]['OD']['current'] = ODV/float(application.config['NUMBER_OF_OD_MEASUREMENTS'])
    
    MeasureTemp(M,'Internal') #Measuring all temperatures
    MeasureTemp(M,'External')
    MeasureTemp(M,'IR')
    MeasureFP(M) #And now fluorescent protein concentrations. 
    
    #Temporary Biofilm Section - the below makes the device all spectral data for all LEDs each cycle.
    
    # bands=['nm410' ,'nm440','nm470','nm510','nm550','nm583','nm620','nm670','CLEAR','NIR']    
    # items= ['LEDA','LEDB','LEDC','LEDD','LEDE','LEDF','LEDG','LASER650']
    # gains=['x10','x10','x10','x10','x10','x10','x10','x1']
    # gi=-1
    # for item in items:
    #     gi=gi+1
    #     SetOutputOn(M,item,1)
    #     GetSpectrum(M,gains[gi])
    #     SetOutputOn(M,item,0)
    #     for band in bands:
    #         sysData[M]['biofilm'][item][band]=int(sysData[M]['AS7341']['spectrum'][band])

    sysData[M]['OD']['Measuring']=0
    if (sysData[M]['OD']['ON']==1):
        RegulateOD(M) #Function that calculates new target pump rates, and sets pumps to desired rates. 
    
    LightActuation(M,1) 
    
    if (sysData[M]['Custom']['ON']==1): #Check if we have enabled custom programs
        CustomThread=Thread(target = CustomProgram, args=(M,)) #We run this in a thread in case we are doing something slow, we dont want to hang up the main l00p. The comma after M is to cast the args as a tuple to prevent it iterating over the thread M
        CustomThread.setDaemon(True)
        CustomThread.start();

    
    Pump2Ontime=sysData[M]['Experiment']['cycleTime']*1.05*abs(sysData[M]['Pump2']['target'])*sysData[M]['Pump2']['ON']+0.5 #The amount of time Pump2 is going to be on for following RegulateOD above.
    time.sleep(Pump2Ontime) #Pause here is to prevent output pumping happening at the same time as stirring.
    
    SetOutputOn(M,'Stir',1) #Start stirring again.

    if(sysData[M]['Experiment']['cycles']%10==9): #Dont want terminal getting unruly, so clear it each 10 rotations.
        clearTerminal(M)
    
    #######Below stores all the results for plotting later
    sysData[M]['time']['record'].append(elapsedTimeSeconds)
    sysData[M]['OD']['record'].append(sysData[M]['OD']['current'])
    sysData[M]['OD']['targetrecord'].append( sysData[M]['OD']['target']*sysData[M]['OD']['ON'])
    sysData[M]['Thermostat']['record'].append(sysData[M]['Thermostat']['target']*float(sysData[M]['Thermostat']['ON']))
    sysData[M]['Light']['record'].append(float(sysData[M]['Light']['ON']))
    sysData[M]['ThermometerInternal']['record'].append(sysData[M]['ThermometerInternal']['current'])
    sysData[M]['ThermometerExternal']['record'].append(sysData[M]['ThermometerExternal']['current'])
    sysData[M]['ThermometerIR']['record'].append(sysData[M]['ThermometerIR']['current'])
    sysData[M]['Pump1']['record'].append(sysData[M]['Pump1']['target']*float(sysData[M]['Pump1']['ON']))
    sysData[M]['Pump2']['record'].append(sysData[M]['Pump2']['target']*float(sysData[M]['Pump2']['ON']))
    sysData[M]['Pump3']['record'].append(sysData[M]['Pump3']['target']*float(sysData[M]['Pump3']['ON']))
    sysData[M]['Pump4']['record'].append(sysData[M]['Pump4']['target']*float(sysData[M]['Pump4']['ON']))
    sysData[M]['GrowthRate']['record'].append(sysData[M]['GrowthRate']['current']*float(sysData[M]['Zigzag']['ON']))
    for FP in ['FP1','FP2','FP3']:
        if sysData[M][FP]['ON']==1:
            sysData[M][FP]['BaseRecord'].append(sysData[M][FP]['Base'])
            sysData[M][FP]['Emit1Record'].append(sysData[M][FP]['Emit1'])
            if (sysData[M][FP]['Emit2Band']!= "OFF"):
                sysData[M][FP]['Emit2Record'].append(sysData[M][FP]['Emit2'])
            else:
                sysData[M][FP]['Emit2Record'].append(0.0)
        else:
            sysData[M][FP]['BaseRecord'].append(0.0)
            sysData[M][FP]['Emit1Record'].append(0.0)
            sysData[M][FP]['Emit2Record'].append(0.0)
    
    #We  downsample our records such that the size of the data vectors being plot in the web interface does not get unruly. 
    if (len(sysData[M]['time']['record'])>200):
        downsample(M)

    #### Writing Results to data files
    csvData(M) #This command writes system data to a CSV file for future keeping.
    #And intermittently write the setup parameters to a data file. 
    if(sysData[M]['Experiment']['cycles']%10==1): #We only write whole configuration file each 10 cycles since it is not really that important. 
        TempStartTime=sysData[M]['Experiment']['startTimeRaw']
        sysData[M]['Experiment']['startTimeRaw']=0 #We had to set this to zero during the write operation since the system does not like writing data in such a format.
        
        filename = sysData[M]['Experiment']['startTime'] + '_' + M + '.txt'
        filename=filename.replace(":","_")
        f = open(filename,'w')
        simplejson.dump(sysData[M],f)
        f.close()
        sysData[M]['Experiment']['startTimeRaw']=TempStartTime
    ##### Written

    if (sysData[M]['Experiment']['ON']==0):
        turnEverythingOff(M)
        addTerminal(M, 'Experiment on %s Stopped' % M)
        return
    
    nowend=datetime.now()
    elapsedTime2=nowend-now
    elapsedTimeSeconds2=round(elapsedTime2.total_seconds(),2)
    sleeptime=CycleTime-elapsedTimeSeconds2
    if (sleeptime<0):
        sleeptime=0
        addTerminal(M, 'Experiment Cycle Time on %s is too short!!!' % M)
        
    time.sleep(sleeptime)
    LightActuation(M,0) #Turn light actuation off if it is running.
    addTerminal(M, 'Cycle ' + str(sysData[M]['Experiment']['cycles']) + 'on %s Complete' % M)

    #Now we run this function again if the automated experiment is still going.
    if (sysData[M]['Experiment']['ON'] and sysData[M]['Experiment']['threadCount']==currentThread):
        sysDevices[M]['Experiment']=Thread(target = runExperiment, args=(M,'placeholder'))
        sysDevices[M]['Experiment'].setDaemon(True)
        sysDevices[M]['Experiment'].start();
        
    else: 
        turnEverythingOff(M)
        addTerminal(M, 'Experiment on %s Stopped' % M)
   

if __name__ == '__main__':
    initialiseAll()
    application.run(debug=True,threaded=True,host='0.0.0.0',port=5000)
    
initialiseAll()
print(str(datetime.now()) + ' Start Up Complete')
