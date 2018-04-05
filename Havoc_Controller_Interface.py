import bcolors
import pygame.joystick
import serial
import time

pygame.init()
j = pygame.joystick.Joystick(0)
j.init()
print 'Initialized Joystick : %s' % j.get_name()

bus = serial.Serial(baudrate=9600, port="COM3", timeout=1)

x1_index = 0
y1_index = 1
x2_index = 2
y2_index = 3
xbtn_index = 4
abtn_index = 5
bbtn_index = 6
ybtn_index = 7
back_index = 12
start_index = 13

armed = False
discon = False
disabled = False
connected = False

max_speed = 0


def set_max_speed():
    global max_speed

    accepted = False

    while not accepted:
        max_speed = input(bcolors.BLUE + "[REQUIRED] - SET MAX SPEED (0-100): " + bcolors.ENDC)

        if 0 <= max_speed <= 100:
            accepted = True
        else:
            print bcolors.FAIL + "[FAIL] - ERROR NOT WITHIN RANGE! RETRY!" + bcolors.ENDC

    print bcolors.PASS + "[ACCEPTED] - SETTING MAX MOTOR SPEED TO " + str(max_speed) + "%" + bcolors.ENDC
    max_speed /= 100.0


def check_connected():
    global connected

    msg = receive()

    if "Arduino" in msg:
        connected = True
    else:
        connected = False
    # print connected  # Debug


def check_armed(data):
    """
    Checks if user wants robot to be armed. Joystick positions for arming are down and inside corners
    (Left joystick - Quadrant 4, Right joystick - Quadrant 3). Values read at those positions are 0.75, 1.0, -0.75, 1.0
    :param data: the data from the controller
    :return: robot armed as a boolean
    """
    # print "Armed data:", data  # Debug
    deadzone = 0.35
    joy1_x = data[0]
    joy1_y = data[1]
    joy2_x = data[2]
    joy2_y = data[3]

    x1_arm = .75 + deadzone > joy1_x > .75 - deadzone  # Checks if x1 is 0.75 +/- dz
    # print "x1 armed:", x1_arm  # Debug
    y1_arm = .75 + deadzone > joy1_y > .75 - deadzone  # Checks if y1 is 1.0 +/- dz
    # print "y1 armed:", y1_arm  # Debug
    x2_arm = -.75 + deadzone > joy2_x > -.75 - deadzone  # Checks if x2 is -0.75 +/- dz
    # print "x2 armed:", x2_arm  # Debug
    y2_arm = .75 + deadzone > joy2_y > .75 - deadzone  # Checks if y2 is 1.0 +/- dz
    # print "y2 armed:", y2_arm  # Debug

    if x1_arm and y1_arm and x2_arm and y2_arm:
        # print "Armed..."  # Debug
        return True
    else:
        return False


def check_disconnected():
    global discon, armed

    pygame.joystick.quit()
    pygame.joystick.init()

    joystick_count = pygame.joystick.get_count()

    for i in range(joystick_count):
        joystick = pygame.joystick.Joystick(i)
        joystick.init()

    if not joystick_count:
        if not discon:
            print bcolors.FAIL + "[FAIL] - CONTROLLER DISCONNECTED!" + bcolors.ENDC
            discon = True
            armed = False
        time.sleep(2)
        check_disconnected()
    else:
        discon = False
        # print "reconnected..."  # Debug


def check_disabled(data):
    global disabled, armed

    usr_disable = False

    check_disconnected()

    if data[back_index] == 1 and data[start_index] == 1:
        usr_disable = True

    if usr_disable or discon:
        armed = False
        return True

    return False


def get():
    out = []
    it = 0  # iterator
    pygame.event.pump()

    # Read input from the two joysticks
    for i in range(0, j.get_numaxes()):
        out.append(round(j.get_axis(i), 2))
        it += 1
    # Read input from buttons
    for i in range(0, j.get_numbuttons()):
        out.append(j.get_button(i))
        it += 1
        
    return out


def send(data):
    """
    Sends data to Arduino
    :param data: joystick data as a String
    """
    bus.write(data)
    print "Sent data...", data  # Debug


def receive():
    rdata = bus.readline()
    print "rdata:", rdata  # Debug
    return rdata


def parse_data(arr):
    """
    Takes in data and parses it to a string to be interpreted
    :param arr: the data array
    :return: the data array as a String
    """
    data_str = str(arr)
    bad_chars = " []"

    for char in bad_chars:
        if data_str.find(char) == -1:
            continue
        else:
            data_str = data_str.replace(char, "")

    return "<" + str(max_speed) + "," + data_str + ">"


def operate():
    global armed

    while not connected:
        check_connected()

    if not armed:
        send("<" + str(max_speed) + ",0,0,0,0>")
        delay = .125
        itr = 0

        while itr < 8:
            data = get()
            # print itr  # Debug

            if check_armed(data):
                itr += 1
            else:
                itr = 0

            time.sleep(delay)
        armed = True
        print bcolors.WARN + "[WARNING] - ROBOT IS ARMED!" + bcolors.ENDC

    while armed and connected:
        data = get()

        # Limit joystick inputs to max motor speed
        for i in range(0, 4):
            data[i] *= max_speed
        
        data_parsed = parse_data(data)
        check_disabled(data)

        if not armed:
            print bcolors.WARN + "[WARNING] - ROBOT DISABLED!" + bcolors.ENDC

            break

        send(data_parsed)
        receive()
        # time.sleep(.125)
        # print "testing..."  # Debug


if __name__ == "__main__":
    set_max_speed()
        
    try:
        while True:
            operate()
    except (KeyboardInterrupt):
        send("<" + str(max_speed) + ",0,0,0,0>")
