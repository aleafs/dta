__copyright__   = "Copyright 2011 SFCTA"
__license__     = """
    This file is part of DTA.

    DTA is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    DTA is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with DTA.  If not, see <http://www.gnu.org/licenses/>.
"""

USAGE = r"""

 USAGE
 python prepareCorridorPlots.py INPUT_DYNAMEQ_NET_DIR 
                                INPUT_DYNAMEQ_NET_PREFIX 
                                REPORTING_START_TIME
                                REPORTING_END_TIME
                                ROUTE_DEFINITION_FILE
                                COUNT_DIR
                                LINK_COUNT_FILE_15MIN 
                                MOVEMENT_COUNT_FILE_15MIN 
                                MOVEMENT_COUNT_FILE_5MIN
                                REPORTS_ROUTE_TRAVEL_TIME_FILE 
 
 e.g.
 
 python createDTAResults.py X:/Projects/ModelDev/dtaAnyway/validation2010.1/Reports/Scenarios/sf_jun8_420p/export 
                               sf_jun8_420p 
                               16:00
                               17:00
                               2011_LOS_Monitoring.csv 
                               X:/Projects/ModelDev/dtaAnyway/validation2010.1/input/ 
                               counts_links_15min_1600_1830.dat 
                               counts_movements_15min_1600_1830.dat 
                               counts_movements_5min_1600_1800.dat
                               ObsVsSimulatedRouteTravelTimes.csv
 

 exports each of the routes defined in the 2011_LOS_Monitoring.csv file to an image 
 
 Before running this script, you must export the loaded Dynameq network by going to 
 Network->Export->Dynameq Network.
"""


import sys
import dta
import csv
from dta.Logger import DtaLogger
from dta.Utils import Time
from dta.Path import Path
from dta.DtaError import DtaError

if __name__ == "__main__":
    
    if len(sys.argv) != 11:
        print USAGE
        sys.exit(2)

    INPUT_DYNAMEQ_NET_DIR                = sys.argv[1]
    INPUT_DYNAMEQ_NET_PREFIX             = sys.argv[2]
    REPORTING_START_TIME                 = sys.argv[3]
    REPORTING_END_TIME                   = sys.argv[4]
    ROUTE_DEFINITION_FILE                = sys.argv[5]
    COUNT_DIR                            = sys.argv[6]
    LINK_COUNT_FILE_15MIN                = sys.argv[7] 
    MOVEMENT_COUNT_FILE_15MIN            = sys.argv[8]
    MOVEMENT_COUNT_FILE_5MIN             = sys.argv[9]
    REPORTS_ROUTE_TRAVEL_TIME_FILE       = sys.argv[10]
    
    # The SanFrancisco network will use feet for vehicle lengths and coordinates, and miles for link lengths
    dta.VehicleType.LENGTH_UNITS= "feet"
    dta.Node.COORDINATE_UNITS   = "feet"
    dta.RoadLink.LENGTH_UNITS   = "miles"

    dta.setupLogging("visualizeDTAResults.INFO.log", "visualizeDTAResults.DEBUG.log", logToConsole=True)

    scenario = dta.DynameqScenario(dta.Time(0,0), dta.Time(23,0))
    scenario.read(INPUT_DYNAMEQ_NET_DIR, INPUT_DYNAMEQ_NET_PREFIX) 
    net = dta.DynameqNetwork(scenario)

    net.read(INPUT_DYNAMEQ_NET_DIR, INPUT_DYNAMEQ_NET_PREFIX)

    #magic numbers here. This information may (or may not) be somewhere in the .dqt files 
    simStartTime = 15 * 60 + 30
    simEndTime = 21 * 60 + 30
    simTimeStep = 5
    net.readSimResults(simStartTime, simEndTime, 5)

    reportStartTime = Time.readFromString(REPORTING_START_TIME).getMinutes()
    reportEndTime = Time.readFromString(REPORTING_END_TIME).getMinutes()

    routeTTOuput = open(REPORTS_ROUTE_TRAVEL_TIME_FILE, "w") 

    routeTTOuput.write("%s,%s,%s,%s\n" % ("RouteName", "SimTravelTimeInMin", "ObsTravelTimeInMin", "RouteLengthInMiles"))

    allRoutes = []
    for record in csv.DictReader(open(ROUTE_DEFINITION_FILE, "r")):

        name = record["RouteName"].strip()        
        if "/" in name:
            DtaLogger.error("Please remove / character from path %s from %s to %s" % (name, start, end))
            continue

        avgTTInMin = float(record["totalAvgTT"]) / 60.0
        end = record["End"].strip()
        start = record["Start"].strip()
        
        fullName = "%s from %s to %s" % (name, start, end)
        
        try: 
            path = Path.createPath(net, fullName, [[name, start], [name, end]], cutoff=0.7)
            DtaLogger.info("CREATED path %s from %s to %s" % (name, start, end))            
        except DtaError:
            DtaLogger.error("Failed to create path %s from %s to %s" % (name, start, end))
            continue            

        allRoutes.append(path)
        print "%s,%f,%f,%f\n" % ("%s from %s to %s" % (name, start, end), path.getSimTTInMin(reportStartTime, reportEndTime), avgTTInMin, path.getLengthInMiles())
        routeTTOuput.write("%s,%f,%f,%f\n" % ("%s from %s to %s" % (name, start, end), path.getSimTTInMin(16*60, 17*60), avgTTInMin, path.getLengthInMiles()))

        
        volumesVsCounts = dta.CorridorPlots.CountsVsVolumes(net, path, False)
        volumesVsCounts.writeVolumesVsCounts(reportStartTime, reportEndTime, record["RouteName"])

    Path.writePathsToShp(allRoutes, "allRoutes") 
    routeTTOuput.close()