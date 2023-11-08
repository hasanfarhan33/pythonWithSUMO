import time
import pytz
import datetime
import traci
import pandas as pd


def getdatetime():
    utc_now = pytz.utc.localize(datetime.datetime.utcnow())
    currentDt = utc_now.astimezone(pytz.timezone("Europe/Dublin"))
    DATIME = currentDt.strftime("%Y-%m-%d %H:%M:%S")
    return DATIME


def flatten_list(_2d_list):
    flat_list = []
    for element in _2d_list:
        if type(element) is list:
            for item in element:
                flat_list.append(item)
        else:
            flat_list.append(element)
    return flat_list


sumoCmd = ["sumo", "-c", "osm.sumocfg"]
traci.start(sumoCmd)

packVehicleData = []
packTLSData = []
packBigData = []

while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()

    vehicles = traci.vehicle.getIDList()
    trafficLights = traci.trafficlight.getIDList()

    # Getting Vehicles Info
    for i in range(0, len(vehicles)):
        vehicleID = vehicles[i]
        x, y = traci.vehicle.getPosition(vehicleID)
        coord = [x, y]
        lon, lat = traci.simulation.convertGeo(x, y)
        gpsCoord = [lon, lat]
        speed = round(traci.vehicle.getSpeed(vehicleID)*3.6, 2)
        edge = traci.vehicle.getRoadID(vehicleID)
        lane = traci.vehicle.getLaneID(vehicleID)
        displacement = round(traci.vehicle.getDistance(vehicleID), 2)
        turnAngle = round(traci.vehicle.getAngle(vehicleID), 2)
        nextTLS = traci.vehicle.getNextTLS(vehicleID)

        # Packing all the data for export to CSV / XLSX
        vehicleList = [getdatetime(), vehicleID, coord, gpsCoord,
                       speed, edge, lane, displacement, turnAngle, nextTLS]

        print("Vehicle: ", vehicleID, " at datetime: ", getdatetime())
        print(vehicleID, ">>> Position: ", coord, " | GPS Position: ", gpsCoord,
              " Speed: ", speed, "km/h | ",
              " Edge ID of the vehicle: ", edge, " | ",
              " Lane ID of the vehicle: ", lane,
              " Distance of the vehicle: ", displacement, "m | ",
              " Vehicle Orientation: ", turnAngle, "degrees | ",
              "Upcoming Traffic Lights: ", nextTLS)

        tlsList = []

        # Getting Traffic Light Info
        for k in range(0, len(trafficLights)):
            # Checking if the lane ID is controlled by traffic lights
            if lane in traci.trafficlight.getControlledLanes(trafficLights[k]):
                tflight = trafficLights[k]
                tl_state = traci.trafficlight.getRedYellowGreenState(tflight)
                tl_phase_duration = traci.trafficlight.getPhaseDuration(
                    tflight)
                tl_lanes_controlled = traci.trafficlight.getControlledLanes(
                    tflight)
                tl_program = traci.trafficlight.getCompleteRedYellowGreenDefinition(
                    tflight)
                tl_next_switch = traci.trafficlight.getNextSwitch(tflight)

                tlsList = [tflight, tl_state, tl_phase_duration,
                           tl_lanes_controlled, tl_program, tl_next_switch]

                print(trafficLights[k], " ----> ",
                      "TL State: ", tl_state, " | ",
                      "TL Phase Duration: ", tl_phase_duration, " | ",
                      "TL Lanes Controlled: ", tl_lanes_controlled, " | ",
                      "TL Program: ", tl_program, " | ",
                      "TL Next Switch: ", tl_next_switch, " | ",
                      )

        packBigDataLine = flatten_list([vehicleList, tlsList])
        packBigData.append(packBigDataLine)

        # MACHINE LEARNING / FUNCTIONS CODE HERE

        # CONTROL Vehicles and Traffic Lights

        # Set function for vehicles
        NEWSPEED = 15  # Value is in meters per second
        if vehicles[i] == "veh2":
            traci.vehicle.setSpeedMode("veh2", 0)
            traci.vehicle.setSpeed("veh2", NEWSPEED)

        # TODO: Try and understand the set functions for the traffic light.
        # Set function for traffic lights
        trafficLightDuration = [5, 37, 5, 35, 6, 3]
        trafficSignal = ["rrrrrrGGgGGGrrrrr", "yyyyyyyyrrrrrr", "rrrrrrrGGGGGGGGGrrrrr", "rrrrrrrYYYYYYYrrrrr",
                         "GrrrrrrrrrGGGGGGg", "yrrrrrrrrrrrYYYY"]

traci.close()

# Generate excel file
columnNames = ['dateAndTime', "vehicleID", "coord", "gpsCoord", "speed", "edge", "lane",
               "displacement", "turnAngle", "nextTLS", "tflight", "tl_state", "tl_phase_duration",
               "tl_lanes_controlled", "tl_program", "tl_next_switch"]

dataset = pd.DataFrame(packBigData, index=None, colums=columnNames)
dataset.to_excel("output.xlsx", index=False)
time.sleep(5)
