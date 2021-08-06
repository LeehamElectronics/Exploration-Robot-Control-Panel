########################################################################################################################
#                                           All Code written By Liam Price                                             #
#                             IoT Exploration Robot VET IT Control Panel main_window.py                                #
#                                              Date Started: 9-07-2020                                                 #
########################################################################################################################

#  ██╗░░░░░██████╗░██████╗░██████╗░██╗░█████╗░███████╗
#  ██║░░░░░██╔══██╗██╔══██╗██╔══██╗██║██╔══██╗██╔════╝
#  ██║░░░░░██║░░██║██████╔╝██████╔╝██║██║░░╚═╝█████╗░░
#  ██║░░░░░██║░░██║██╔═══╝░██╔══██╗██║██║░░██╗██╔══╝░░
#  ███████╗██████╔╝██║░░░░░██║░░██║██║╚█████╔╝███████╗
#  ╚══════╝╚═════╝░╚═╝░░░░░╚═╝░░╚═╝╚═╝░╚════╝░╚══════╝

#  ░██████╗░█████╗░███████╗████████╗░██╗░░░░░░░██╗░█████╗░██████╗░███████╗
#  ██╔════╝██╔══██╗██╔════╝╚══██╔══╝░██║░░██╗░░██║██╔══██╗██╔══██╗██╔════╝
#  ╚█████╗░██║░░██║█████╗░░░░░██║░░░░╚██╗████╗██╔╝███████║██████╔╝█████╗░░
#  ░╚═══██╗██║░░██║██╔══╝░░░░░██║░░░░░████╔═████║░██╔══██║██╔══██╗██╔══╝░░
#  ██████╔╝╚█████╔╝██║░░░░░░░░██║░░░░░╚██╔╝░╚██╔╝░██║░░██║██║░░██║███████╗
#  ╚═════╝░░╚════╝░╚═╝░░░░░░░░╚═╝░░░░░░╚═╝░░░╚═╝░░╚═╝░░╚═╝╚═╝░░╚═╝╚══════╝

# Libraries Here #
from tkinter import *
from PIL import ImageTk, Image  # Used for rotating images
import paho.mqtt.client as mqtt
import time, logging
import multiprocessing
import json

############################################
#                                          #
#   Global Variables and data structures   #
#                                          #
############################################
crane_positions = {}
crane_constraints = {}
crane_speeds = {}
tank_gyro_values = {}
birds_eye_image = Image.open("media/birds_eye_sqaure.png")
front_tank_view = Image.open("media/front_view_tank.png")
side_tank_view = Image.open("media/side_view_tank.png")

yaw_prev = 1000
pitch_prev = 1000
rotation_temp_prev = 1000


#########################################################################
#                                                                       #
#                        Main Window Functions                          #
#                                                                       #
#########################################################################


def log_out():
    print("Logging out...")
    my_window.destroy()
    import login_window


def power_val_update(*args):
    global power_sel
    val_temp = power_val.get()
    print("power val update sequence")
    if val_temp == "HIGH":
        power_sel.config(bg="RED")
    if val_temp == "MED":
        power_sel.config(bg="ORANGE")
    if val_temp == "LOW":
        power_sel.config(bg="GREEN")


def ctrl_mode_val_update(*args):
    print("Updating Controller Mode")
    if ctrl_mode_val.get() == "Sticky":
        print("Sticky Control Enabled")
    elif ctrl_mode_val.get() == "Momentary":
        print("Momentary Control Enabled")
    elif ctrl_mode_val.get() == "Steering Wheel":
        print("Steering Wheel OptionMenu")
        custom_controller_func()


def remap(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


#########################################################################
#                                                                       #
#                         MQTT Setup Code                               #
#                                                                       #
#########################################################################
online_mode = False
connection_profile = {}


def connect_mqtt():
    print("Connecting to mqtt")
    client.username_pw_set(connection_profile['cred_user'], connection_profile['cred_pass'])
    client.connect(connection_profile['mqtt_ip'], connection_profile['mqtt_port'])  # establish connection
    time.sleep(1)
    client.loop_start()
    client.subscribe("/ExpR/out")  # subscribe to mqtt topic
    client.subscribe("/ExpR/out/crane_pos")  # subscribe to mqtt topic
    client.subscribe("/ExpR/out/crane_con")  # subscribe to mqtt topic
    client.subscribe("/ExpR/out/crane_speed")  # subscribe to mqtt topic
    client.subscribe("/ExpR/out/current_main")  # subscribe to mqtt topic for reading current usage
    client.subscribe("/ExpR/out/tank_gyro")  # subscribe to mqtt topic for reading gyro values
    print("Connect success!")
    main_window_setup()


def on_subscribe(client, userdata, mid, granted_qos):
    # print("subscribed with qos",granted_qos, "\n")
    time.sleep(1)
    logging.info("sub acknowledge message id=" + str(mid))


def on_disconnect(client, userdata, rc=0):
    logging.info("DisConnected result code " + str(rc))


def on_connect(client, userdata, flags, rc):
    logging.info("Connected flags" + str(flags) + "result code " + str(rc))


def on_message(client, userdata, message):
    global final_img
    global final_pitch_img
    global final_yaw_img
    global rotated_b
    global rotated_f
    global rotated_s
    global yaw_prev
    global pitch_prev
    global rotation_temp_prev

    msg = str(message.payload.decode("utf-8"))
    topic = str(message.topic)

    print("Received Topic: " + topic + " msg: " + msg)
    if topic == "/ExpR/out/crane_pos":
        print("updated crane position msg found")
        # print("Current crane_pos JSON RAW: " + msg)
        try:
            print("Trying to read JSON data now...")
            crane_dict = json.loads(msg)
            print("Succsefully read JSON file: ")
            print(str(crane_dict))
        except Exception as failure:
            print("Failed to read JSON because of: " + failure)
        crane_rot_pos_var.set(crane_dict["rot"])
        crane_CA_pos_var.set(crane_dict["ca_1"])
        crane_CA_2_pos_var.set(crane_dict["ca_2"])
        crane_FA_pos_var.set(crane_dict["fa"])
        crane_gripper_pos_var.set(crane_dict["grip"])
    elif topic == "/ExpR/out/crane_con":
        print("updated crane constraint msg found")
        try:
            print("Trying to read JSON data now...")
            crane_con_dict = json.loads(msg)
            print("Succsefully read JSON file: ")
            print(str(crane_con_dict))
        except Exception as failure:
            print("Failed to read JSON because of: " + failure)
        crane_rot_con_x.set(crane_con_dict["rx"])
        crane_rot_con_y.set(crane_con_dict["ry"])
        crane_cen_con_x.set(crane_con_dict["cx"])
        crane_cen_con_y.set(crane_con_dict["cy"])
        crane_fa_con_x.set(crane_con_dict["fx"])
        crane_fa_con_y.set(crane_con_dict["fy"])
        crane_gr_con_x.set(crane_con_dict["gx"])
        crane_gr_con_y.set(crane_con_dict["gy"])
    elif topic == "/ExpR/out/crane_speed":
        print("updated crane movement speed msg found")
        try:
            print("Trying to read JSON data now...")
            crane_speed_dict = json.loads(msg)
            print("Succsefully read JSON file: ")
            print(str(crane_speed_dict))
        except Exception as failure:
            print("Failed to read JSON because of: " + failure)
        crane_rot_speed_var.set(crane_speed_dict["rs"])
        crane_CA_speed_var.set(crane_speed_dict["cs"])
        crane_FA_speed_var.set(crane_speed_dict["fs"])
        crane_gripper_speed_var.set(crane_speed_dict["gs"])
    elif topic == "/ExpR/out/current_main":
        print("New current value: " + msg)
        OldMax = 140
        OldMin = 110
        NewMax = 100
        NewMin = 0

        NewValue = remap(float(msg), OldMin, OldMax, NewMin, NewMax)

        final = int(round(NewValue, 1))
        print(final)
        power_usage.set(final)
    elif topic == "/ExpR/out/tank_gyro":
        print("New gyro value RAW: " + msg)
        try:
            print("Trying to read JSON data now...")
            tank_gyro_values = json.loads(msg)
            print("Succsefully read JSON file: ")
            print(str(tank_gyro_values))
        except Exception as failure:
            print("Failed to read JSON because of: " + failure)

        pitch = int(tank_gyro_values["r"])
        yaw = int(tank_gyro_values["p"])
        # if yaw < 0:
        #    yaw = abs(yaw)
        # else:
        #    y = yaw * 2
        #    yaw = yaw - y
        rotation_temp = int(tank_gyro_values["y"])
        if rotation_temp < 0:
            rotation_temp = abs(rotation_temp)
        else:
            r = rotation_temp * 2
            rotation_temp = rotation_temp - r

        robot_gyro_yaw_val.set(yaw)
        robot_gyro_pitch_val.set(pitch)
        robot_gyro_rot_val.set(rotation_temp)

        if rotation_temp != rotation_temp_prev:
            rotation_temp_prev = rotation_temp
            rotated_b = birds_eye_image.rotate(rotation_temp)
            final_img = ImageTk.PhotoImage(rotated_b)
            gyro_rotation_picture = Label(gyro_frame, image=final_img, justify=CENTER, relief=RAISED, bg="gray")
            gyro_rotation_picture.grid(row=3, column=0, columnspan=2)

        if pitch != pitch_prev:
            pitch_prev = pitch
            rotated_f = front_tank_view.rotate(pitch)
            final_pitch_img = ImageTk.PhotoImage(rotated_f)
            gyro_pitch_picture = Label(gyro_frame, image=final_pitch_img, justify=CENTER, relief=RAISED, bg="gray")
            gyro_pitch_picture.grid(row=3, column=2, columnspan=2)

        if yaw != yaw_prev:
            yaw_prev = yaw
            rotated_s = side_tank_view.rotate(yaw)
            final_yaw_img = ImageTk.PhotoImage(rotated_s)
            gyro_yaw_picture = Label(gyro_frame, image=final_yaw_img, justify=CENTER, relief=RAISED, bg="gray")
            gyro_yaw_picture.grid(row=3, column=4, columnspan=2)

    else:
        print("unhandled topic: " + topic + " msg: " + msg)


def on_publish(client, userdata, mid):
    logging.info("message published " + str(mid))


logging.basicConfig(level=logging.INFO)  # Error Logging #
QOS = 0  # QoS Level keep at 0
CLEAN_SESSION = True
client = mqtt.Client("ExpR-CtrlP", False)  # create client object
client.on_subscribe = on_subscribe  # assign function to callback
client.on_disconnect = on_disconnect  # assign function to callback
client.on_connect = on_connect  # assign function to callback
client.on_message = on_message  # when a payload is received this function runs
client.on_publish = on_publish


#########################################################################
#                                                                       #
#  Below are the functions specific for each event that is called from  #
#   main_window.py such as when you click a button and it sends a time  #
#                       value to the MQTT broker.                       #
#                                                                       #
#########################################################################
def forward():
    global lte_1_pic
    global bottom_frame
    print("Forward")  # Diagnostic purposes
    client.publish("/ExpR/in", "1")
    signal_strength = Label(bottom_frame, image=lte_1_pic)
    signal_strength.grid(row=1, column=2, sticky='nw', rowspan=2)


def back():
    global four_g_pic
    global bottom_frame
    print("Back")  # Diagnostic purposes
    client.publish("/ExpR/in", "2")
    signal_type = Label(bottom_frame, image=four_g_pic)
    signal_type.grid(row=1, column=3, sticky='nw', rowspan=2)


def left():
    print("Left")  # Diagnostic purposes
    client.publish("/ExpR/in", "3")


def right():
    print("Right")  # Diagnostic purposes
    client.publish("/ExpR/in", "4")


def stop():
    print("Stop")  # Diagnostic purposes
    client.publish("/ExpR/in", "5")


def light_toggle():
    print("Light Toggle")
    client.publish("/ExpR/in/SW_btn_d", "6")


def get_crane_pos():
    print("Getting Crane position values")
    client.publish("/ExpR/in", "g")


def append_crane_pos():
    print("Appending current crane pos as default into EEPROM")
    client.publish("/ExpR/in", "s")


def get_crane_con():
    print("Getting current crane constraint values")
    client.publish("/ExpR/in", "k")


def append_crane_con():
    print("Appending current crane constraints to EEPROM")
    client.publish("/ExpR/in", "o")


def get_crane_speed():
    print("Getting current crane speed values")
    client.publish("/ExpR/in", "y")


def append_crane_speed():
    print("Appending current crane speed to EEPROM")
    client.publish("/ExpR/in", "u")


def send_new_crane_pos():
    print("Sending NEW crane pos to tank")

    crane_positions["rot"] = crane_rot_pos_var.get()
    crane_positions["ca_1"] = crane_CA_pos_var.get()
    crane_positions["ca_2"] = crane_CA_2_pos_var.get()
    crane_positions["fa"] = crane_FA_pos_var.get()
    crane_positions["grip"] = crane_gripper_pos_var.get()

    crane_positions_string = json.dumps(crane_positions)
    print(crane_positions_string)
    client.publish("/ExpR/in/newC", crane_positions_string)


def send_new_crane_constraints():
    print("Sending NEW crane pos to tank")

    # Crane rotation constraint #
    crane_constraints["rcx"] = crane_rot_con_x.get()
    crane_constraints["rcy"] = crane_rot_con_y.get()
    # Crane center axis constraint #
    crane_constraints["ccx"] = crane_cen_con_x.get()
    crane_constraints["ccy"] = crane_cen_con_y.get()
    # Crane forearm constraint #
    crane_constraints["fcx"] = crane_fa_con_x.get()
    crane_constraints["fcy"] = crane_fa_con_y.get()
    # Crane gripper constraint #
    crane_constraints["gcx"] = crane_gr_con_x.get()
    crane_constraints["gcy"] = crane_gr_con_y.get()

    crane_constraints_string = json.dumps(crane_constraints)
    print(crane_constraints_string)
    client.publish("/ExpR/in/ncc", crane_constraints_string)


def send_new_crane_speed():
    print("Sending NEW crane speed to tank")

    crane_speeds["rs"] = crane_rot_speed_var.get()
    crane_speeds["cs"] = crane_CA_speed_var.get()
    crane_speeds["fs"] = crane_FA_speed_var.get()
    crane_speeds["gs"] = crane_gripper_speed_var.get()

    crane_speeds_string = json.dumps(crane_speeds)
    print(crane_speeds_string)
    client.publish("/ExpR/in/ncs", crane_speeds_string)


def send_new_timing_values():
    print("Sending new timings values to robot")
    timings = {}

    timings["c"] = robot_current_meas_timing.get()
    timings["g"] = robot_gyro_update_timing.get()

    timings_string = json.dumps(timings)
    print(timings_string)
    client.publish("/ExpR/in/nt", timings_string)


def key_pressed(event):
    global arrow_forward_button
    key = event.keysym
    print("You hit the " + key + " Key")
    if key == "Up":
        forward()
    if key == "Down":
        back()
    if key == "Right":
        right()
    if key == "Left":
        left()
    if key == "space":
        stop()


def start_steering_wheel_ctrl(prfl):
    # Some of the Pygame code was taken directly from the Pygame wiki as an example that I built off. Google Pygame for
    # more info on the module
    print("Starting steering_wheel_module")
    # You will need to manually set your MQTT credentials and connection options here, I know it's annoying, but it's
    # difficult for me to parse the variables from the login screen into this function because it's running on another
    # CPU core, if you would like to help, contact me at liamisprice@gmail.com
    print(f"Connecting to mqtt with {prfl['mqtt_ip']} and port {prfl['mqtt_port']}")
    logging.basicConfig(level=logging.INFO)  # Error Logging #
    client = mqtt.Client("ExpR-CtrlP-Steering", False)  # create client object
    client.on_subscribe = on_subscribe  # assign function to callback
    client.on_disconnect = on_disconnect  # assign function to callback
    client.on_connect = on_connect  # assign function to callback
    client.on_message = on_message  # when a payload is received this function runs
    client.username_pw_set(prfl['cred_user'], prfl['cred_pass'])
    client.connect(prfl['mqtt_ip'], prfl['mqtt_port'])  # establish connection
    time.sleep(1)
    client.loop_start()
    print("Connect success!")
    # import pygame_sdl2 as pygame
    import pygame
    # Define some colors.
    BLACK = pygame.Color('black')
    WHITE = pygame.Color('white')

    # This is a simple class that will help us print to the screen.
    # It has nothing to do with the joysticks, just outputting the
    # information.
    class TextPrint(object):
        def __init__(self):
            self.reset()
            self.font = pygame.font.Font(None, 20)

        def tprint(self, screen, textString):
            textBitmap = self.font.render(textString, True, BLACK)
            screen.blit(textBitmap, (self.x, self.y))
            self.y += self.line_height

        def reset(self):
            self.x = 10
            self.y = 10
            self.line_height = 15

        def indent(self):
            self.x += 10

        def unindent(self):
            self.x -= 10

    pygame.init()

    # Set the width and height of the screen (width, height).
    screen = pygame.display.set_mode((600, 2000))

    pygame.display.set_caption("ExpR Steering Wheel GUI")

    # Loop until the user clicks the close button.
    done = False

    # Used to manage how fast the screen updates.
    clock = pygame.time.Clock()

    # Initialize the joysticks.
    pygame.joystick.init()

    # Get ready to print.
    textPrint = TextPrint()

    button_0_pressed = False
    button_1_pressed = False
    button_2_pressed = False
    button_3_pressed = False
    button_4_pressed = False
    button_5_pressed = False
    button_6_pressed = False
    button_7_pressed = False
    button_8_pressed = False
    button_9_pressed = False
    button_10_pressed = False
    button_11_pressed = False
    button_12_pressed = False

    axis_temp_check = False

    # -------- Main Program Loop -----------
    while not done:
        #
        # EVENT PROCESSING STEP
        #
        # Possible joystick actions: JOYAXISMOTION, JOYBALLMOTION, JOYBUTTONDOWN,
        # JOYBUTTONUP, JOYHATMOTION
        for event in pygame.event.get():  # User did something.
            if event.type == pygame.QUIT:  # If user clicked close.
                done = True  # Flag that we are done so we exit this loop.
            elif event.type == pygame.JOYHATMOTION:
                hat_temp = str(joystick.get_hat(0))
                print("Hat motion: " + hat_temp)
                if hat_temp == "(0, 1)":
                    print("forarm up")
                    client.publish("/ExpR/in/hat", "y")
                elif hat_temp == "(0, -1)":
                    print("forarm down")
                    client.publish("/ExpR/in/hat", "x")
                elif hat_temp == "(1, 0)":
                    print("centre_axis up")
                    client.publish("/ExpR/in/hat", "v")
                elif hat_temp == "(-1, 0)":
                    print("centre_axis down")
                    client.publish("/ExpR/in/hat", "c")
                elif hat_temp == "(0, 0)":
                    print("origin")
                    client.publish("/ExpR/in/hat", "b")
            elif event.type == pygame.JOYBUTTONDOWN:
                print("Joystick button pressed.")
                if joystick.get_button(0) == True:
                    button_0_pressed = True
                    print("button 1 hit")
                    client.publish("/ExpR/in/SW_btn_d", "0")
                elif joystick.get_button(1) == True:
                    button_1_pressed = True
                    print("button 1 hit")
                    client.publish("/ExpR/in/SW_btn_d", "1")
                elif joystick.get_button(2) == True:
                    button_2_pressed = True
                    print("button 2 hit")
                    client.publish("/ExpR/in/SW_btn_d", "2")
                elif joystick.get_button(3) == True:
                    print("button 3 hit")
                    client.publish("/ExpR/in/SW_btn_d", "3")
                    button_3_pressed = True
                elif joystick.get_button(4) == True:
                    print("button 4 hit = left crane_rot")
                    client.publish("/ExpR/in/SW_btn_d", "5")
                    button_4_pressed = True
                elif joystick.get_button(5) == True:
                    print("button 5 hit = right crane_rot")
                    client.publish("/ExpR/in/SW_btn_d", "4")
                    button_5_pressed = True
                elif joystick.get_button(6) == True:
                    print("button 6 hit")
                    client.publish("/ExpR/in/SW_btn_d", "6")
                    button_6_pressed = True
                elif joystick.get_button(7) == True:
                    print("button 7 hit")
                    client.publish("/ExpR/in/SW_btn_d", "7")
                    button_7_pressed = True
                elif joystick.get_button(8) == True:
                    print("button 8 hit")
                    client.publish("/ExpR/in/SW_btn_d", "8")
                    button_8_pressed = True
                elif joystick.get_button(9) == True:
                    print("button 9 hit")
                    client.publish("/ExpR/in/SW_btn_d", "9")
                    button_9_pressed = True
                elif joystick.get_button(10) == True:
                    print("button 10 hit")
                    client.publish("/ExpR/in/SW_btn_d", "6")
                    button_10_pressed = True
                elif joystick.get_button(11) == True:
                    print("button 11 hit")
                    client.publish("/ExpR/in/SW_btn_d", "s")
                    button_11_pressed = True
                elif joystick.get_button(12) == True:
                    print("button 12 hit")
                    client.publish("/ExpR/in/SW_btn_d", "12")
                    button_12_pressed = True
            elif event.type == pygame.JOYBUTTONUP:
                print("Joystick button released.")
                if joystick.get_button(0) == False and button_0_pressed == True:
                    button_1_pressed = False
                    print("button 0 released")
                    client.publish("/ExpR/in/SW_btn_u", "0")
                if joystick.get_button(1) == False and button_1_pressed == True:
                    button_1_pressed = False
                    print("button 1 released")
                    client.publish("/ExpR/in/SW_btn_u", "1")
                elif joystick.get_button(2) == False and button_2_pressed == True:
                    button_2_pressed = False
                    print("button 2 released")
                    client.publish("/ExpR/in/SW_btn_u", "2")
                elif joystick.get_button(3) == False and button_3_pressed == True:
                    button_3_pressed = False
                    print("button 3 released")
                    client.publish("/ExpR/in/SW_btn_u", "3")
                elif joystick.get_button(4) == False and button_4_pressed == True:
                    button_4_pressed = False
                    print("button 4 released")
                    client.publish("/ExpR/in/SW_btn_u", "5")
                elif joystick.get_button(5) == False and button_5_pressed == True:
                    button_5_pressed = False
                    print("button 5 released")
                    client.publish("/ExpR/in/SW_btn_u", "4")
                elif joystick.get_button(6) == False and button_6_pressed == True:
                    button_6_pressed = False
                    print("button 6 released")
                    client.publish("/ExpR/in/SW_btn_u", "6")
                elif joystick.get_button(7) == False and button_7_pressed == True:
                    button_7_pressed = False
                    print("button 7 released")
                    client.publish("/ExpR/in/SW_btn_u", "7")
                elif joystick.get_button(8) == False and button_8_pressed == True:
                    button_8_pressed = False
                    print("button 8 released")
                    client.publish("/ExpR/in/SW_btn_u", "8")
                elif joystick.get_button(9) == False and button_9_pressed == True:
                    button_9_pressed = False
                    print("button 9 released")
                    client.publish("/ExpR/in/SW_btn_u", "9")
                elif joystick.get_button(10) == False and button_10_pressed == True:
                    button_10_pressed = False
                    print("button 10 released")
                    # client.publish("/ExpR/in/SW_btn_u", "10")
                elif joystick.get_button(11) == False and button_11_pressed == True:
                    button_11_pressed = False
                    print("button 11 released")
                    client.publish("/ExpR/in/SW_btn_u", "s")
                elif joystick.get_button(12) == False and button_12_pressed == True:
                    button_12_pressed = False
                    print("button 12 released")
                    client.publish("/ExpR/in/SW_btn_u", "12")
            elif event.type == pygame.JOYAXISMOTION:
                if not axis_temp_check:
                    axis_0_temp = 1.0
                    axis_1_temp = 1.0
                    axis_2_temp = 1.0
                    axis_temp_check = True
                    print("Values set to 1")
                axis_0_current = round(joystick.get_axis(0) * 2, 1)
                axis_1_current = round(joystick.get_axis(1), 1) * 100
                axis_2_current = round(joystick.get_axis(2), 1) * 100
                if axis_0_current != axis_0_temp:
                    if axis_0_current > 0:
                        if axis_0_current < 1:
                            axis_0_temp = round(abs(axis_0_current - 1), 1)
                            axis_0_temp = str(axis_0_temp)
                            print("SOFT RIGHT " + axis_0_temp)
                            client.publish("/ExpR/in/SW_axs_0/Rs", axis_0_temp)
                            axis_0_temp = axis_0_current
                        else:
                            axis_0_temp = round(axis_0_current - 1, 1)
                            axis_0_temp = str(axis_0_temp)
                            print("HARD RIGHT" + axis_0_temp)
                            client.publish("/ExpR/in/SW_axs_0/Rh", axis_0_temp)
                            axis_0_temp = axis_0_current
                    else:
                        if axis_0_current > -1:
                            axis_0_temp = round(axis_0_current + 1, 1)
                            axis_0_temp = str(axis_0_temp)
                            print("SOFT LEFT " + axis_0_temp)
                            client.publish("/ExpR/in/SW_axs_0/Ls", axis_0_temp)
                            axis_0_temp = axis_0_current
                        else:
                            axis_0_temp = round(abs(axis_0_current + 1), 1)
                            axis_0_temp = str(axis_0_temp)
                            print("HARD LEFT" + axis_0_temp)
                            client.publish("/ExpR/in/SW_axs_0/Lh", axis_0_temp)
                            axis_0_temp = axis_0_current
                if axis_1_current != axis_1_temp:
                    axis_1_temp = axis_1_current
                    axis_1_temp = str(axis_1_temp)
                    print(axis_1_temp)
                    client.publish("/ExpR/in/SW_axs_1", axis_1_temp)
                    axis_1_temp = axis_1_current
                if axis_2_current != axis_2_temp:
                    axis_2_temp = axis_2_current
                    axis_2_temp = str(axis_2_temp)
                    print(axis_2_temp)
                    client.publish("/ExpR/in/SW_axs_2", axis_2_temp)
                    axis_2_temp = axis_2_current

        #
        # DRAWING STEP
        #
        # First, clear the screen to white. Don't put other drawing commands
        # above this, or they will be erased with this command.
        screen.fill(WHITE)
        textPrint.reset()

        # Get count of joysticks.
        joystick_count = pygame.joystick.get_count()

        textPrint.tprint(screen, "Number of joysticks: {}".format(joystick_count))
        textPrint.indent()

        # For each joystick:
        for i in range(joystick_count):
            joystick = pygame.joystick.Joystick(i)
            joystick.init()

            textPrint.tprint(screen, "Joystick {}".format(i))
            textPrint.indent()

            # Get the name from the OS for the controller/joystick.
            name = joystick.get_name()
            textPrint.tprint(screen, "Joystick name: {}".format(name))

            # Usually axis run in pairs, up/down for one, and left/right for
            # the other.
            axes = joystick.get_numaxes()
            textPrint.tprint(screen, "Number of axes: {}".format(axes))
            textPrint.indent()

            for i in range(axes):
                axis = joystick.get_axis(i)
                textPrint.tprint(screen, "Axis {} value: {:>6.3f}".format(i, axis))
            textPrint.unindent()

            buttons = joystick.get_numbuttons()
            textPrint.tprint(screen, "Number of buttons: {}".format(buttons))
            textPrint.indent()

            for i in range(buttons):
                button = joystick.get_button(i)
                textPrint.tprint(screen,
                                 "Button {:>2} value: {}".format(i, button))
            textPrint.unindent()

            hats = joystick.get_numhats()
            textPrint.tprint(screen, "Number of hats: {}".format(hats))
            textPrint.indent()

            # Hat position. All or nothing for direction, not a float like
            # get_axis(). Position is a tuple of int values (x, y).
            for i in range(hats):
                hat = joystick.get_hat(i)
                textPrint.tprint(screen, "Hat {} value: {}".format(i, str(hat)))

            textPrint.unindent()

            textPrint.unindent()

        #
        # ALL CODE TO DRAW SHOULD GO ABOVE THIS COMMENT
        #

        # Go ahead and update the screen with what we've drawn.
        pygame.display.flip()

        # Limit to 20 frames per second.
        clock.tick(20)

    # Close the window and quit.
    # If you forget this line, the program will 'hang'
    # on exit if running from IDLE.
    pygame.quit()


def custom_controller_func():
    print("PROFILE: " + str(connection_profile))
    sw_ctrl = multiprocessing.Process(target=start_steering_wheel_ctrl, args=(connection_profile,))
    sw_ctrl.start()


#########################################################################
#                                                                       #
#                         Tkinter Setup Code                            #
#                                                                       #
#########################################################################
my_window = Tk()

# Key listener setup code #
my_window.bind("<Key>", key_pressed)

#########################################################################
#                                                                       #
#                           String Variables                            #
#                                                                       #
#########################################################################
power_val = StringVar()
power_val.set("HIGH")
power_val.trace('w', power_val_update)

ctrl_mode_val = StringVar()
ctrl_mode_val.set("Sticky")
ctrl_mode_val.trace('w', ctrl_mode_val_update)

# Crane Position Variables from GUI #
crane_rot_pos_var = StringVar()
crane_CA_pos_var = StringVar()
crane_CA_2_pos_var = StringVar()
crane_FA_pos_var = StringVar()
crane_gripper_pos_var = StringVar()

# Crane Constraint Variables from GUI #
# Rotation Axis
crane_rot_con_x = StringVar()
crane_rot_con_y = StringVar()

# Center Axis #
crane_cen_con_x = StringVar()
crane_cen_con_y = StringVar()

# ForeArm Axis #
crane_fa_con_x = StringVar()
crane_fa_con_y = StringVar()

# Gripper Axis #
crane_gr_con_x = StringVar()
crane_gr_con_y = StringVar()

# Crane Speed Variables from GUI #
crane_rot_speed_var = StringVar()
crane_CA_speed_var = StringVar()
crane_FA_speed_var = StringVar()
crane_gripper_speed_var = StringVar()

# Robot update timing values:
robot_current_meas_timing = StringVar()
robot_gyro_update_timing = StringVar()

# Robot Gyro values:
robot_gyro_yaw_val = StringVar()
robot_gyro_pitch_val = StringVar()
robot_gyro_rot_val = StringVar()


#########################################################################
#                                                                       #
#                         Geometry Management                           #
#                                                                       #
#########################################################################
def main_window_setup():
    global bg_photo  # This stops the garbage collector from deleting the photo #
    global video_frame
    global power_sel
    global lte_1_pic
    global bottom_frame
    global four_g_pic
    global three_g_pic
    global arrow_forward_button
    global gyro_frame
    global my_window
    global power_usage
    my_window.title("Exploration Robot Control Panel")
    # Use the following two lines for getting max screen resolution:
    width = my_window.winfo_screenwidth()
    height = my_window.winfo_screenheight()
    # width = 1450
    # height = 900
    my_window.geometry(f'{width}x{height}')
    my_window.iconbitmap('media/IoTER_icon.ico')
    my_window.configure(background='grey')
    my_window.grid_rowconfigure(1, weight=1)
    my_window.grid_columnconfigure(0, weight=1)
    # Background Photo Setup (needs to be done first otherwise it wont be put at the back) #
    bg_photo = PhotoImage(file="media/bg_main_window.png")
    bg_photo_label = Label(my_window, image=bg_photo)
    bg_photo_label.place(x=0, y=0)

    # Organise sections of GUI into frames #
    # top_frame = Frame(my_window, bg='gray')
    bottom_frame = Frame(my_window, bg="dim gray")
    # video_frame = Frame(my_window, bg="dim gray")
    left_frame = Frame(my_window, bg="dim gray")
    joystick_frame = Frame(my_window, bg="gray40")
    left_crane_control_frame = Frame(my_window, bg="dim gray")
    right_frame = Frame(my_window, bg="dim gray")
    gyro_frame = Frame(my_window, bg="gray40")
    # video_option_frame = Frame(my_window, bg="dim gray")
    # Grid all the frames in place #
    # top_frame.grid(row=0, column=0, columnspan=3, sticky="n") # NOT USED ATM
    # video_frame.grid(row=1, column=0, sticky="n")
    # video_option_frame.grid(row=3, column=0, sticky="sw")
    left_frame.grid(row=0, column=0, sticky="nw")  # power usage stuff
    gyro_frame.grid(row=0, column=1, sticky="nw", rowspan=3)
    left_crane_control_frame.grid(row=0, column=5, sticky="ne", rowspan=3)  # crane input / output panel
    right_frame.grid(row=1, column=0, sticky="nw")  # power selecting thing
    joystick_frame.grid(row=0, column=2, sticky="nw")  # joystick / button widgets
    bottom_frame.grid(row=4, column=0, sticky="sw", columnspan=4)  # network status stuff

    # top_frame Widget Creation #

    # top_frame Widget Placement #

    # video_frame Widget Creation #

    # video_frame Widget Placement #

    # left_frame Widget Creation #
    bat_lvl_lab = Message(left_frame, text="Battery Level:", width=110, justify=CENTER, relief=RAISED, bg="Red")
    bat_lvl = Scale(left_frame, from_=100, to=0, orient=VERTICAL, width=30, relief=SUNKEN)
    bat_lvl.config(state='disabled')
    power_usage_lab = Message(left_frame, text="Power Usage:", width=60, justify=CENTER, relief=SUNKEN, bg="Green")
    power_in_lab = Message(left_frame, text="Power Input:", width=60, justify=CENTER, relief=SUNKEN, bg="Green")
    power_usage = Scale(left_frame, from_=100, to=0, orient=VERTICAL, width=15, relief=SUNKEN)
    power_in = Scale(left_frame, from_=100, to=0, orient=VERTICAL, width=15, relief=SUNKEN)
    power_in.config(state='disabled')
    power_eta_lab = Message(left_frame, text="ETA Battery: 2 Hours", width=90, justify=CENTER, relief=RAISED)

    # Crane Position Menu #
    crane_pos_get_but = Button(left_crane_control_frame, text="Get crane position values:", width=20, justify=CENTER,
                               relief=RAISED, bg="Orange", command=get_crane_pos)
    crane_rot_pos_label = Label(left_crane_control_frame, text="Current rotation value: ", width=30, justify=CENTER,
                                relief=RAISED, bg="dark orange")
    crane_CA_pos_label = Label(left_crane_control_frame, text="Current center_axis_1 value: ", width=30, justify=CENTER,
                               relief=RAISED,
                               bg="dark orange")
    crane_CA_2_pos_label = Label(left_crane_control_frame, text="Current center_axis_2 value: ", width=30,
                                 justify=CENTER, relief=RAISED,
                                 bg="dark orange")
    crane_FA_pos_label = Label(left_crane_control_frame, text="Current forearm value: ", width=30, justify=CENTER,
                               relief=RAISED,
                               bg="dark orange")
    crane_gripper_pos_label = Label(left_crane_control_frame, text="Current gripper value: ", width=30, justify=CENTER,
                                    relief=RAISED,
                                    bg="dark orange")
    crane_rot_pos_entry = Entry(left_crane_control_frame, textvariable=crane_rot_pos_var, justify=CENTER)
    crane_CA_pos_entry = Entry(left_crane_control_frame, textvariable=crane_CA_pos_var, justify=CENTER)
    crane_CA_2_pos_entry = Entry(left_crane_control_frame, textvariable=crane_CA_2_pos_var, justify=CENTER)
    crane_FA_pos_entry = Entry(left_crane_control_frame, textvariable=crane_FA_pos_var, justify=CENTER)
    crane_gripper_pos_entry = Entry(left_crane_control_frame, textvariable=crane_gripper_pos_var, justify=CENTER)
    crane_pos_default_append = Button(left_crane_control_frame, text="Set current crane pos to default", width=30,
                                      justify=CENTER, relief=RAISED,
                                      bg="Orange", command=append_crane_pos)

    send_new_crane_pos_button = Button(left_crane_control_frame, text="Send custom crane values", width=30,
                                       justify=CENTER,
                                       relief=RAISED, bg="white", command=send_new_crane_pos)

    # Crane Movement Constraints Menu #
    crane_con_get_but = Button(left_crane_control_frame, text="Get crane constraint vals:", width=20, justify=CENTER,
                               relief=RAISED, bg="Orange", command=get_crane_con)
    crane_rot_con_label = Label(left_crane_control_frame, text="Current rotation Constraint X/Y: ", width=30,
                                justify=CENTER,
                                relief=RAISED, bg="dark orange")
    crane_CA_con_label = Label(left_crane_control_frame, text="Current center_axis Constraint X/Y: ", width=30,
                               justify=CENTER,
                               relief=RAISED, bg="dark orange")
    crane_FA_con_label = Label(left_crane_control_frame, text="Current forearm Constraint X/Y: ", width=30,
                               justify=CENTER,
                               relief=RAISED, bg="dark orange")
    crane_gripper_con_label = Label(left_crane_control_frame, text="Current gripper Constraint X/Y: ", width=30,
                                    justify=CENTER, relief=RAISED, bg="dark orange")
    # x values
    crane_rot_con_x_entry = Entry(left_crane_control_frame, textvariable=crane_rot_con_x, justify=CENTER, width=9)
    crane_CA_con_x_entry = Entry(left_crane_control_frame, textvariable=crane_cen_con_x, justify=CENTER, width=9)
    crane_FA_con_x_entry = Entry(left_crane_control_frame, textvariable=crane_fa_con_x, justify=CENTER, width=9)
    crane_gripper_con_x_entry = Entry(left_crane_control_frame, textvariable=crane_gr_con_x, justify=CENTER, width=9)
    # y values
    crane_rot_con_y_entry = Entry(left_crane_control_frame, textvariable=crane_rot_con_y, justify=CENTER, width=9)
    crane_CA_con_y_entry = Entry(left_crane_control_frame, textvariable=crane_cen_con_y, justify=CENTER, width=9)
    crane_FA_con_y_entry = Entry(left_crane_control_frame, textvariable=crane_fa_con_y, justify=CENTER, width=9)
    crane_gripper_con_y_entry = Entry(left_crane_control_frame, textvariable=crane_gr_con_y, justify=CENTER, width=9)
    crane_con_default_append = Button(left_crane_control_frame, text="Set current constraints to default",
                                      width=30, justify=CENTER, relief=RAISED, bg="Orange", command=append_crane_con)
    send_new_crane_con_button = Button(left_crane_control_frame, text="Send custom constraint vals", width=30,
                                       justify=CENTER, relief=RAISED, bg="white", command=send_new_crane_constraints)

    # Crane Movement Speed Menu #
    crane_speed_get_but = Button(left_crane_control_frame, text="Get crane speed values:", width=20, justify=CENTER,
                                 relief=RAISED, bg="Orange", command=get_crane_speed)
    crane_rot_speed_label = Label(left_crane_control_frame, text="Current rotation speed: ", width=30, justify=CENTER,
                                  relief=RAISED, bg="dark orange")
    crane_CA_speed_label = Label(left_crane_control_frame, text="Current center_axis speed: ", width=30, justify=CENTER,
                                 relief=RAISED,
                                 bg="dark orange")
    crane_FA_speed_label = Label(left_crane_control_frame, text="Current forearm speed: ", width=30, justify=CENTER,
                                 relief=RAISED,
                                 bg="dark orange")
    crane_gripper_speed_label = Label(left_crane_control_frame, text="Current gripper speed: ", width=30,
                                      justify=CENTER,
                                      relief=RAISED,
                                      bg="dark orange")
    crane_rot_speed_entry = Entry(left_crane_control_frame, textvariable=crane_rot_speed_var, justify=CENTER)
    crane_CA_speed_entry = Entry(left_crane_control_frame, textvariable=crane_CA_speed_var, justify=CENTER)
    crane_FA_speed_entry = Entry(left_crane_control_frame, textvariable=crane_FA_speed_var, justify=CENTER)
    crane_gripper_speed_entry = Entry(left_crane_control_frame, textvariable=crane_gripper_speed_var, justify=CENTER)
    crane_speed_default_append = Button(left_crane_control_frame, text="Set current crane speed to default", width=30,
                                        justify=CENTER, relief=RAISED, bg="Orange", command=append_crane_speed)

    send_new_crane_speed_button = Button(left_crane_control_frame, text="Send custom speed values", width=30,
                                         justify=CENTER, relief=RAISED, bg="white", command=send_new_crane_speed)
    tank_current_msr_timer_lab = Label(left_crane_control_frame, text="Power usage update interval: ", width=35,
                                       justify=CENTER, relief=RAISED, bg="dark orange")
    tank_current_msr_timer_entry = Entry(left_crane_control_frame, textvariable=robot_current_meas_timing,
                                         justify=CENTER,
                                         width=9)
    tank_gyro_timer_lab = Label(left_crane_control_frame, text="Robot Gyroscope update interval: ", width=35,
                                justify=CENTER, relief=RAISED, bg="dark orange")
    tank_gyro_timer_entry = Entry(left_crane_control_frame, textvariable=robot_gyro_update_timing, justify=CENTER,
                                  width=9)
    send_new_timing_values_button = Button(left_crane_control_frame, text="Send new timing values", width=25,
                                           justify=CENTER, relief=RAISED, bg="white", command=send_new_timing_values)

    # left_frame Widget Placement #
    bat_lvl_lab.grid(row=0, column=0, columnspan=2, pady=(0, 5))
    bat_lvl.grid(row=1, column=0, sticky='news', columnspan=2)
    power_usage_lab.grid(row=3, column=0, pady=(20, 5))
    power_usage.grid(row=4, column=0)
    power_in_lab.grid(row=3, column=1, pady=(20, 5))
    power_in.grid(row=4, column=1)
    power_eta_lab.grid(row=5, column=0, columnspan=2, pady=(5, 0))

    # left_crane_menu_frame Widget Placement #
    # crane position:
    crane_pos_get_but.grid(row=6, column=0, columnspan=2, pady=(5, 0))
    crane_rot_pos_label.grid(row=7, column=0, columnspan=2, pady=(5, 0))
    crane_CA_pos_label.grid(row=8, column=0, columnspan=2, pady=(5, 0))
    crane_CA_2_pos_label.grid(row=9, column=0, columnspan=2, pady=(5, 0))
    crane_FA_pos_label.grid(row=10, column=0, columnspan=2, pady=(5, 0))
    crane_gripper_pos_label.grid(row=11, column=0, columnspan=2, pady=(5, 0))
    crane_pos_default_append.grid(row=12, column=0, columnspan=2, pady=(5, 0))
    send_new_crane_pos_button.grid(row=13, column=0, columnspan=2, pady=(5, 0))
    crane_rot_pos_entry.grid(row=7, column=2, columnspan=2, pady=(5, 0))
    crane_CA_pos_entry.grid(row=8, column=2, columnspan=2, pady=(5, 0))
    crane_CA_2_pos_entry.grid(row=9, column=2, columnspan=2, pady=(5, 0))
    crane_FA_pos_entry.grid(row=10, column=2, columnspan=2, pady=(5, 0))
    crane_gripper_pos_entry.grid(row=11, column=2, columnspan=2, pady=(5, 0))
    # crane constraint:
    crane_con_get_but.grid(row=14, column=0, columnspan=2, pady=(5, 0))
    crane_rot_con_label.grid(row=15, column=0, columnspan=2, pady=(5, 0))
    crane_CA_con_label.grid(row=16, column=0, columnspan=2, pady=(5, 0))
    crane_FA_con_label.grid(row=17, column=0, columnspan=2, pady=(5, 0))
    crane_gripper_con_label.grid(row=18, column=0, columnspan=2, pady=(5, 0))
    crane_con_default_append.grid(row=19, column=0, columnspan=2, pady=(5, 0))
    send_new_crane_con_button.grid(row=20, column=0, columnspan=2, pady=(5, 0))
    # x values:
    crane_rot_con_x_entry.grid(row=15, column=2, columnspan=1, pady=(5, 0))
    crane_CA_con_x_entry.grid(row=16, column=2, columnspan=1, pady=(5, 0))
    crane_FA_con_x_entry.grid(row=17, column=2, columnspan=1, pady=(5, 0))
    crane_gripper_con_x_entry.grid(row=18, column=2, columnspan=1, pady=(5, 0))
    # y values:
    crane_rot_con_y_entry.grid(row=15, column=3, columnspan=1, pady=(5, 0))
    crane_CA_con_y_entry.grid(row=16, column=3, columnspan=1, pady=(5, 0))
    crane_FA_con_y_entry.grid(row=17, column=3, columnspan=1, pady=(5, 0))
    crane_gripper_con_y_entry.grid(row=18, column=3, columnspan=1, pady=(5, 0))
    # crane speed:
    crane_speed_get_but.grid(row=21, column=0, columnspan=2, pady=(5, 0))
    crane_rot_speed_label.grid(row=22, column=0, columnspan=2, pady=(5, 0))
    crane_CA_speed_label.grid(row=23, column=0, columnspan=2, pady=(5, 0))
    crane_FA_speed_label.grid(row=24, column=0, columnspan=2, pady=(5, 0))
    crane_gripper_speed_label.grid(row=25, column=0, columnspan=2, pady=(5, 0))
    crane_speed_default_append.grid(row=26, column=0, columnspan=2, pady=(5, 0))
    send_new_crane_speed_button.grid(row=27, column=0, columnspan=2, pady=(5, 0))
    crane_rot_speed_entry.grid(row=22, column=2, columnspan=2, pady=(5, 0))
    crane_CA_speed_entry.grid(row=23, column=2, columnspan=2, pady=(5, 0))
    crane_FA_speed_entry.grid(row=24, column=2, columnspan=2, pady=(5, 0))
    crane_gripper_speed_entry.grid(row=25, column=2, columnspan=2, pady=(5, 0))

    tank_current_msr_timer_lab.grid(row=28, column=0, columnspan=2, pady=(5, 0))
    tank_current_msr_timer_entry.grid(row=28, column=2, columnspan=2, pady=(5, 0))
    tank_gyro_timer_lab.grid(row=29, column=0, columnspan=2, pady=(5, 0))
    tank_gyro_timer_entry.grid(row=29, column=2, columnspan=2, pady=(5, 0))
    send_new_timing_values_button.grid(row=30, column=0, columnspan=2, pady=(5, 0))

    # GyroFrame widget creation #
    gyro_yaw_label = Label(gyro_frame, text="Yaw: ", width=10, justify=CENTER, relief=RAISED, bg="dark orange")
    gyro_yaw_var_label = Entry(gyro_frame, textvariable=robot_gyro_yaw_val, justify=CENTER, width=9)
    gyro_pitch_label = Label(gyro_frame, text="Pitch: ", width=10, justify=CENTER, relief=RAISED, bg="dark orange")
    gyro_pitch_var_label = Entry(gyro_frame, textvariable=robot_gyro_pitch_val, justify=CENTER, width=9)
    gyro_rotation_label = Label(gyro_frame, text="Rotation: ", width=10, justify=CENTER, relief=RAISED,
                                bg="dark orange")
    gyro_rotation_var_label = Entry(gyro_frame, textvariable=robot_gyro_rot_val, justify=CENTER, width=9)

    gyro_yaw_label.grid(row=0, column=3, columnspan=1, pady=(5, 0), sticky="w")
    gyro_yaw_var_label.grid(row=0, column=3, columnspan=1, pady=(5, 0), sticky="e")
    gyro_pitch_label.grid(row=1, column=3, columnspan=1, pady=(5, 0), sticky="w")
    gyro_pitch_var_label.grid(row=1, column=3, columnspan=1, pady=(5, 0), sticky="e")
    gyro_rotation_label.grid(row=2, column=3, columnspan=1, pady=(5, 0), sticky="w")
    gyro_rotation_var_label.grid(row=2, column=3, columnspan=1, pady=(5, 0), sticky="e")

    # right_frame Widget Creation #
    power_sel_label = Label(right_frame, text="Performance:", justify=CENTER, relief=RAISED, font="bold")
    power_sel = OptionMenu(right_frame, power_val, "HIGH", "MED", "LOW")
    power_sel.config(bg="RED")
    light_toggle_button = Button(right_frame, text="Toggle Lights", bg="dim gray", command=light_toggle)
    ctrl_mode_sel_label = Label(right_frame, text="Controller Mode:", justify=CENTER, relief=RAISED, font="bold")
    ctrl_mode_sel = OptionMenu(right_frame, ctrl_mode_val, "Sticky", "Momentary", "Steering Wheel")
    ctrl_mode_sel.config(bg="GRAY")
    arrow_forward_pic = PhotoImage(file="media/arrow_forward.png")
    arrow_back_pic = PhotoImage(file="media/arrow_down.png")
    arrow_left_pic = PhotoImage(file="media/arrow_left.png")
    arrow_right_pic = PhotoImage(file="media/arrow_right.png")
    stop_sign_pic = PhotoImage(file="media/stop_sign.png")
    arrow_forward_button = Button(joystick_frame, image=arrow_forward_pic, bg="dim gray", command=forward)
    arrow_back_button = Button(joystick_frame, image=arrow_back_pic, bg="dim gray", command=back)
    arrow_left_button = Button(joystick_frame, image=arrow_left_pic, bg="dim gray", command=left)
    arrow_right_button = Button(joystick_frame, image=arrow_right_pic, bg="dim gray", command=right)
    stop_button = Button(joystick_frame, image=stop_sign_pic, bg="dim gray", command=stop)

    # right_frame Widget Placement #
    power_sel_label.grid(row=0, column=3)
    power_sel.grid(row=0, column=4)
    ctrl_mode_sel_label.grid(row=1, column=3)
    ctrl_mode_sel.grid(row=1, column=4)
    light_toggle_button.grid(row=2, column=3, pady=(0, 40))
    arrow_forward_button.grid(row=1, column=1)
    arrow_back_button.grid(row=3, column=1)
    arrow_left_button.grid(row=2, column=0)
    arrow_right_button.grid(row=2, column=2)
    stop_button.grid(row=2, column=1)

    # bottom_frame Widget Creation #
    net_stat_label = Label(bottom_frame, text="Network Status:", justify=CENTER, relief=RAISED, font="bold")
    ping_server_label = Message(bottom_frame, text=" Ping To Server: 500ms ", justify=CENTER, relief=RAISED, bg="black",
                                fg="white", width=190)
    ping_traverse_label = Message(bottom_frame, text=" Ping To ExpR: 800ms   ", justify=CENTER, relief=RAISED,
                                  bg="black", fg="white", width=190)
    bandwidth_stat_label = Label(bottom_frame, text="  Network Bandwidth:  ", justify=CENTER, relief=RAISED,
                                 font="bold")
    bandwidth_out_label = Message(bottom_frame, text=" Out: 30 bps     ", justify=CENTER, relief=RAISED, bg="black",
                                  fg="white", width=190)
    bandwidth_in_label = Message(bottom_frame, text=" In: 50 bps      ", justify=CENTER, relief=RAISED, bg="black",
                                 fg="white", width=190)
    signal_strength_label = Message(bottom_frame, text="Signal Strength:", justify=CENTER, relief=RAISED, bg="white",
                                    fg="black", width=190)
    lte_0_pic = PhotoImage(file="media/lte-0.png")
    lte_1_pic = PhotoImage(file="media/lte-1.png")
    lte_2_pic = PhotoImage(file="media/lte-2.png")
    lte_3_pic = PhotoImage(file="media/lte-3.png")
    lte_4_pic = PhotoImage(file="media/lte-4.png")
    signal_strength = Label(bottom_frame, image=lte_0_pic)
    signal_type_label = Message(bottom_frame, text="Connection Via:", justify=CENTER, relief=RAISED, bg="white",
                                fg="black", width=190)
    wifi_pic = PhotoImage(file="media/wifi_symbol_new.png")
    three_g_pic = PhotoImage(file="media/3g_symbol.png")
    four_g_pic = PhotoImage(file="media/4g_symbol_new.png")
    signal_type = Label(bottom_frame, image=wifi_pic)

    # bottom_frame Widget Placement #
    net_stat_label.grid(row=0, column=0, pady=(0, 0), padx=(0, 20), sticky='n')
    ping_server_label.grid(row=1, column=0, sticky='nw')
    ping_traverse_label.grid(row=2, column=0, sticky='nw', pady=(0, 40))
    bandwidth_stat_label.grid(row=0, column=1, pady=(0, 0), padx=(0, 0), sticky='n')
    bandwidth_out_label.grid(row=1, column=1, sticky='nw')
    bandwidth_in_label.grid(row=2, column=1, sticky='nw', pady=(0, 40))
    signal_strength_label.grid(row=0, column=2, sticky='nw', rowspan=2)
    signal_strength.grid(row=1, column=2, sticky='nw', rowspan=2)
    signal_type_label.grid(row=0, column=3, sticky='nw', rowspan=2)
    signal_type.grid(row=1, column=3, sticky='nw', rowspan=2)
    # Runs the main loop that updates the GUI #
    loop_main_window()


def loop_main_window():
    if online_mode:
        print("Starting in Online Mode")
    else:
        print("Starting in Offline Mode")
    my_window.mainloop()

#########################################################################
#                                                                       #
#                             Acknowledgments                           #
#                                                                       #
#########################################################################
#                                                                       #
# I decided to format my Tkinter widgets in the way I have because of   #
# what read in the following StackOverflow post...                      #
# https://stackoverflow.com/questions/34276663/tkinter-gui-layout-using #
#       -frames-and-grid                                                #
# I figured I needed some way or organising my Tkinter widgets because  #
# there is A LOT of widgets in my design.                               #
#########################################################################
