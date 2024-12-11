# ////////////////////////////////////////////////////////////////
# //                     IMPORT STATEMENTS                      //
# ////////////////////////////////////////////////////////////////
import os
import math
import sys
import time
import threading
from platform import machine

from pygame.draw_py import draw_polygon

os.environ["DISPLAY"] = ":0.0"

from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import *
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.slider import Slider
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock
from kivy.animation import Animation
from functools import partial
from kivy.config import Config
from kivy.core.window import Window
from pidev.kivy import DPEAButton
from pidev.kivy import PauseScreen
from time import sleep
from dpeaDPi.DPiComputer import *
from dpeaDPi.DPiStepper import *

# ////////////////////////////////////////////////////////////////
# //                     HARDWARE SETUP                         //
# ////////////////////////////////////////////////////////////////
"""Stepper Motor goes into MOTOR 0 )
    Limit Switch associated with Stepper Motor goes into HOME 0
    One Sensor goes into IN 0
    Another Sensor goes into IN 1
    Servo Motor associated with the Gate goes into SERVO 1
    Motor Controller for DC Motor associated with the Stairs goes into SERVO 0"""

# ////////////////////////////////////////////////////////////////
# //                      GLOBAL VARIABLES                      //
# //                         CONSTANTS                          //
# ////////////////////////////////////////////////////////////////
ON = False
OFF = True
HOME = True
TOP = False
OPEN = False
CLOSE = True
YELLOW = 0.917, 0.796, 0.380, 1
BLUE = .180, 0.188, 0.980, 1
DEBOUNCE = 0.1
INIT_RAMP_SPEED = 2
RAMP_LENGTH = 725


# ////////////////////////////////////////////////////////////////
# //            DECLARE APP CLASS AND SCREENMANAGER             //
# //                     LOAD KIVY FILE                         //
# ////////////////////////////////////////////////////////////////
class MyApp(App):
    def build(self):
        self.title = "Perpetual Motion"
        return sm


Builder.load_file('main.kv')
Window.clearcolor = (.1, .1, .1, 1)  # (WHITE)

# ////////////////////////////////////////////////////////////////
# //                    SLUSH/HARDWARE SETUP                    //
# ////////////////////////////////////////////////////////////////
sm = ScreenManager()

#Servo motor
dpiComputer = DPiComputer()
dpiComputer.initialize()

#Stepper
dpiStepper = DPiStepper()
dpiStepper.setBoardNumber(0)
stepper_num = 0
if not dpiStepper.initialize():
    print("Communication with the DPiStepper board failed")

#ramp speed stuff
speed_steps_per_second = 1600 * 10
accel_steps_per_second_per_second = speed_steps_per_second

# ////////////////////////////////////////////////////////////////
# //                       MAIN FUNCTIONS                       //
# //             SHOULD INTERACT DIRECTLY WITH HARDWARE         //
# ////////////////////////////////////////////////////////////////


# ////////////////////////////////////////////////////////////////
# //        DEFINE MAINSCREEN CLASS THAT KIVY RECOGNIZES        //
# //                                                            //
# //   KIVY UI CAN INTERACT DIRECTLY W/ THE FUNCTIONS DEFINED   //
# //     CORRESPONDS TO BUTTON/SLIDER/WIDGET "on_release"       //
# //                                                            //
# //   SHOULD REFERENCE MAIN FUNCTIONS WITHIN THESE FUNCTIONS   //
# //      SHOULD NOT INTERACT DIRECTLY WITH THE HARDWARE        //
# ////////////////////////////////////////////////////////////////
class MainScreen(Screen):
    staircaseSpeedText = '0'
    rampSpeed = INIT_RAMP_SPEED
    staircaseSpeed = 40
    gate = False
    stair = False
    step = False
    max_rampspeed = 200
    max_staircasespeed = 50
    rampSpeed = max_rampspeed
    staircaseSpeed = max_staircasespeed

    def openGate(self):
        if not self.ids.gate.text:
            i = 0
            servo_number = 0
            for i in range (90): #opens the gate
                dpiComputer.writeServo(servo_number, i)
                sleep(.01)
        else:
            i = 0
            servo_number = 0
            for i in range(180, 0, -1): #closes the gate to original position
                dpiComputer.writeServo(servo_number, i)
                sleep(.01)

    def turnOnStaircase(self):
        speed_steps_per_second = (round(90 * (self.staircaseSpeed/self.max_staircasespeed) + 90))
        servo_number = 1
        if not self.stair:
            dpiComputer.writeServo(servo_number, speed_steps_per_second)
            self.stair = True
        else:
            dpiComputer.writeServo(servo_number, 90)
            self.stair = False

    def moveRamp(self):
        speed_steps_per_second = (round(1600*(8 * (self.rampSpeed/self.max_rampspeed) + 2)))
        dpiStepper.enableMotors(True)
        dpiStepper.setSpeedInStepsPerSecond(0, speed_steps_per_second)
        dpiStepper.setAccelerationInStepsPerSecondPerSecond(0, accel_steps_per_second_per_second)
        dpiStepper.moveToRelativePositionInSteps(stepper_num, -46600, True)
        dpiStepper.moveToHomeInSteps(stepper_num, 1, 1600 * 10,48000)
        dpiStepper.setSpeedInStepsPerSecond(0, speed_steps_per_second)
        dpiStepper.setAccelerationInStepsPerSecondPerSecond(0, accel_steps_per_second_per_second)
        dpiStepper.enableMotors(False)

    def setRampSpeed(self, speed):
        self.rampSpeed = speed

    def setStaircaseSpeed(self, speed):
        self.staircaseSpeed = speed

    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.initialize()
        dpiStepper.moveToHomeInSteps(stepper_num, 1, 2000,45000)


    def toggleGate(self):
        self.openGate()
        print("Open and Close gate here")

    def toggleStaircase(self):
        self.turnOnStaircase()
        print("Turn on and off staircase here")

    def toggleRamp(self):
        self.moveRamp()
        print("Move ramp up and down here")

    def auto(self):
        self.toggleRamp()
        self.toggleStaircase()
        sleep(5)
        self.openGate()
        self.toggleStaircase()
        Clock.schedule_interval(self.checkBall, 0.05)
        print("Run through one cycle of the perpetual motion machine")

    def checkBall(self, dt = 0):
        if dpiComputer.readDigitalIn(dpiComputer.IN_CONNECTOR__IN_0) == 0:
            Clock.unschedule(self.checkBall)
            self.auto()

    def setRampSpeed(self, speed):
        self.RampSpeed = speed
        print("Set the ramp speed and update slider text")

    def setStaircaseSpeed(self, speed):
        self.staircaseSpeed = speed
        print("Set the staircase speed and update slider text")

    def initialize(self):
        print("Close gate, stop staircase and home ramp here")

    def resetColors(self):
        self.ids.gate.color = YELLOW
        self.ids.staircase.color = YELLOW
        self.ids.ramp.color = YELLOW
        self.ids.auto.color = BLUE

    def quit(self):
        print("Exit")
        MyApp().stop()


sm.add_widget(MainScreen(name='main'))

# ////////////////////////////////////////////////////////////////
# //                          RUN APP                           //
# ////////////////////////////////////////////////////////////////
if __name__ == "__main__":
    # Window.fullscreen = True
    # Window.maximize()
    MyApp().run()