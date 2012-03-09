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
import datetime
import dta
import os
import sys

USAGE = r"""

 python createSFNetworkFromCubeNetwork.py geary_dynameq_net_dir geary_dynameq_net_prefix sf_cube_net_dir
 
 e.g.
 
 python createSFNetworkFromCubeNetwork.py Y:\dta\nwSubarea\2008 Base2008 Y:\dta\SanFrancisco\2010
 
 This script reads the San Francisco Cube network (SanFranciscoSubArea_2010.net) 
 and converts it to a Dynameq network, writing it out to the current directory as sf_*.dqt.
 
  * Currently, it ignores the first two args (they are for the Geary DTA network, which we're skipping for now; leaving it there for future)
  * The third arg is the location of the San Francisco Cube network for conversion to a Dynameq DTA network, this is where
    the script finds:
    * `SanFranciscoSubArea_2010.net`, the actual Cube network
    * `turnspm.pen`, the prohibited turns file
    * `trueShapeExport\SanFranciscoSubArea_2010.shp`, the shapefile version of the Cube network (for additional
       road geometry information)
 
 """

def removeHOVStubs(sanfranciscoDynameqNet):
    """
    The San Francisco network has a few "HOV stubs" -- links intended to facilitate future coding of HOV lanes
    Find these and remove them
    """    
    nodesToRemove = []
    for node in sanfranciscoDynameqNet.iterNodes():
        # one incomine link, one outgoing link
        if node.getNumIncomingLinks() != 1: continue
        if node.getNumOutgoingLinks() != 1: continue
        
        removalCandidate = True
        # the incoming/outgoing links must each be a road link of facility type 6
        for link in node.iterAdjacentLinks():
            if not link.isRoadLink(): 
                removalCandidate = False
                break
            if link.getFacilityType() != 6:
                removalCandidate = False
                break
        
        if removalCandidate:
            nodesToRemove.append(node)
    
    for node in nodesToRemove:
        dta.DtaLogger.info("Removing HOV Stub node %d" % node.getId())
        sanfranciscoDynameqNet.removeNode(node)
 
if __name__ == '__main__':
    
    if len(sys.argv) != 4:
        print USAGE
        sys.exit(2)
    
    GEARY_DYNAMEQ_NET_DIR       = sys.argv[1] 
    GEARY_DYNAMEQ_NET_PREFIX    = sys.argv[2]
    SF_CUBE_NET_DIR             = sys.argv[3]   # TODO: change this to cube net name 
    #SF_CUBE_TURN_PROHIBITIONS   = sys.argv[4]
    #SF_CUBE_SHAPEFILE           = ""


    
    # The SanFrancisco network will use feet for vehicle lengths and coordinates, and miles for link lengths
    dta.VehicleType.LENGTH_UNITS= "feet"
    dta.Node.COORDINATE_UNITS   = "feet"
    dta.RoadLink.LENGTH_UNITS   = "miles"

    dta.setupLogging("dtaInfo.log", "dtaDebug.log", logToConsole=True)
    
    # The Geary network was created in an earlier Phase of work, so it already exists as
    # a Dynameq DTA network.  Initialize it from the Dynameq text files.
    #gearyScenario = dta.DynameqScenario(datetime.datetime(2010,1,1,0,0,0), 
    #                                    datetime.datetime(2010,1,1,4,0,0))

    #gearyScenario.read(dir=GEARY_DYNAMEQ_NET_DIR, file_prefix=GEARY_DYNAMEQ_NET_PREFIX) 
    #gearynetDta = dta.DynameqNetwork(scenario=gearyScenario)
    #gearynetDta.read(dir=GEARY_DYNAMEQ_NET_DIR, file_prefix=GEARY_DYNAMEQ_NET_PREFIX)
    
    # The rest of San Francisco currently exists as a Cube network.  Initialize it from
    # the Cube network files (which have been exported to dbfs.)
    sanfranciscoScenario = dta.DynameqScenario(datetime.datetime(2010,1,1,0,0,0), 
                                               datetime.datetime(2010,1,1,4,0,0))

    # We will have 4 vehicle classes: Car_NoToll, Car_Toll, Truck_NoToll, Truck_Toll 
    # We will provide demand matrices for each of these classes
    sanfranciscoScenario.addVehicleClass("Car_NoToll")
    sanfranciscoScenario.addVehicleClass("Car_Toll")
    sanfranciscoScenario.addVehicleClass("Truck_NoToll")
    sanfranciscoScenario.addVehicleClass("Truck_Toll")
    
    # length is in feet (from above), response time is in seconds, maxSpeed is in mi/hour
    # We have only 2 vehicle types                      Type        VehicleClass    Length  RespTime    MaxSpeed    SpeedRatio
    sanfranciscoScenario.addVehicleType(dta.VehicleType("Car",      "Car_NoToll",   14,     1,          100.0,      100.0))
    sanfranciscoScenario.addVehicleType(dta.VehicleType("Car",      "Car_Toll",     14,     1,          100.0,      100.0))
    sanfranciscoScenario.addVehicleType(dta.VehicleType("Truck",    "Truck_NoToll", 30,     1.6,        70.0,       90.0))
    sanfranciscoScenario.addVehicleType(dta.VehicleType("Truck",    "Truck_Toll",   30,     1.6,        70.0,       90.0))
    # Generic is an implicit type

    # VehicleClassGroups
    allVCG =                                  dta.VehicleClassGroup(dta.VehicleClassGroup.ALL,        dta.VehicleClassGroup.CLASSDEFINITION_ALL,          "#bebebe") 
    sanfranciscoScenario.addVehicleClassGroup(allVCG)
    sanfranciscoScenario.addVehicleClassGroup(dta.VehicleClassGroup(dta.VehicleClassGroup.PROHIBITED, dta.VehicleClassGroup.CLASSDEFINITION_PROHIBITED,   "#ffff00"))
    sanfranciscoScenario.addVehicleClassGroup(dta.VehicleClassGroup(dta.VehicleClassGroup.TRANSIT,    dta.VehicleClassGroup.TRANSIT,                      "#55ff00"))
    sanfranciscoScenario.addVehicleClassGroup(dta.VehicleClassGroup("Toll",                           "Car_Toll|Truck_Toll",                              "#0055ff"))
    
    # Generalized cost
    # TODO: Make this better!?!
    sanfranciscoScenario.addGeneralizedCost("Expression_0", # name
                                            "Seconds",      # units
                                            "ptime+(left_turn_pc*left_turn)+(right_turn_pc*right_turn)", # turn_expr
                                            "0",            # link_expr
                                            ""              # descr
                                            )
    
    # Read the Cube network
    sanfranciscoCubeNet = dta.CubeNetwork(sanfranciscoScenario)
    sanfranciscoCubeNet.readNetfile \
      (netFile=os.path.join(SF_CUBE_NET_DIR,"SanFranciscoSubArea_2010.net"),
       nodeVariableNames=["N","X","Y"],
       linkVariableNames=["A","B","TOLL","USE",
                          "CAP","AT","FT","STREETNAME","TYPE",
                          "MTYPE","SPEED","DISTANCE","TIME",
                          "LANE_AM","LANE_OP","LANE_PM",
                          "BUSLANE_AM","BUSLANE_OP","BUSLANE_PM",
                          "TOLLAM_DA","TOLLAM_SR2","TOLLAM_SR3",
                          "TOLLPM_DA","TOLLPM_SR2","TOLLPM_SR3",
                          "TOLLEA_DA","TOLLEA_SR2","TOLLEA_SR3",
                          "TOLLMD_DA","TOLLMD_SR2","TOLLMD_SR3",
                          "TOLLEV_DA","TOLLEV_SR2","TOLLEV_SR3 ",
                          "VALUETOLL_FLAG","PASSTHRU",
                          "BUSTPS_AM","BUSTPS_OP","BUSTPS_PM",
                          ],
       centroidIds                      = range(1,999),
       nodeGeometryTypeEvalStr          = "Node.GEOMETRY_TYPE_INTERSECTION",
       nodeControlEvalStr               = "RoadNode.CONTROL_TYPE_SIGNALIZED",
       nodePriorityEvalStr              = "RoadNode.PRIORITY_TEMPLATE_NONE",
       nodeLabelEvalStr                 = "None",
       nodeLevelEvalStr                 = "None",
       linkReverseAttachedIdEvalStr     = "None", #TODO: fix?
       linkFacilityTypeEvalStr          = "int(FT)",
       linkLengthEvalStr                = "float(DISTANCE)",
       linkFreeflowSpeedEvalStr         = "float(SPEED)",
       linkEffectiveLengthFactorEvalStr = "1",
       linkResponseTimeFactorEvalStr    = "1.05",
       linkNumLanesEvalStr              = "2 if isConnector else (int(LANE_PM) + (1 if int(BUSLANE_PM)>0 else 0))",
       linkRoundAboutEvalStr            = "False",
       linkLevelEvalStr                 = "None",
       linkLabelEvalStr                 = '(STREETNAME if STREETNAME else "") + (" " if TYPE and STREETNAME else "") + (TYPE if TYPE else "")'
       )
    
    # create the movements for the network for all vehicles
    sanfranciscoCubeNet.addAllMovements(allVCG, includeUTurns=False)
    
    # Apply the turn prohibitions
    sanfranciscoCubeNet.applyTurnProhibitions(os.path.join(SF_CUBE_NET_DIR, "turnspm.pen"))
    
    # Read the shape points so curvy streets look curvy
    sanfranciscoCubeNet.readLinkShape(os.path.join(SF_CUBE_NET_DIR, "trueShapeExport", "SanFranciscoSubArea_2010.shp"),
                                      "A", "B")
    
    # Convert the network to a Dynameq DTA network
    sanfranciscoDynameqNet = dta.DynameqNetwork(scenario=sanfranciscoScenario)
    sanfranciscoDynameqNet.deepcopy(sanfranciscoCubeNet)
    
    # Why would we want to do this?
    # sanfranciscoDynameqNet.removeShapePoints()
    
    # Add virtual nodes and links between Centroids and RoadNodes; required by Dynameq
    sanfranciscoDynameqNet.insertVirtualNodeBetweenCentroidsAndRoadNodes(startVirtualNodeId=9000000, startVirtualLinkId=9000000,
                                                                         distanceFromCentroid=50)
    
    # Move the centroid connectors from intersection nodes to midblock locations
    # TODO: for dead-end streets, is this necessary?  Or are the midblocks ok?
    sanfranciscoDynameqNet.removeCentroidConnectorsFromIntersections(splitReverseLinks=True)

    # TODO: Fold into handleOverlappingLinks() and revisit the way this works; not sure random movements are the way to go
    # sanfranciscoDynameqNet.moveVirtualNodesToAvoidOverlappingLinks(maxDistToMove=100)

    # TODO: why is this necessary?  Where these duplicate connectors came from?
    # sanfranciscoDynameqNet.removeDuplicateConnectors()
    
    # TODO: I think this isn't necessary; but discuss if the soln below is ok
    # sanfranciscoDynameqNet.moveVirtualNodesToAvoidShortConnectors(1.05*sanfranciscoScenario.maxVehicleLength(),
    #                                                              maxDistToMove=100) # feet

    # the San Francisco network has a few "HOV stubs" -- links intended to facilitate future coding of HOV lanes
    removeHOVStubs(sanfranciscoDynameqNet)

    # right now this warns; I think some of the handling above might be joined into this (especially if this
    # is the problem the method is meant to solve)
    sanfranciscoDynameqNet.handleOverlappingLinks(warn=True)
    
    # finally -- Dynameq requires links to be longer than the longest vehicle
    sanfranciscoDynameqNet.handleShortLinks(1.05*sanfranciscoScenario.maxVehicleLength()/5280.0,
                                            warn=True,
                                            setLength=True)

    # if we have too many nodes for the license 10
    if sanfranciscoDynameqNet.getNumRoadNodes() > 12500:
        sanfranciscoDynameqNet.removeUnconnectedNodes()
    sanfranciscoDynameqNet.write(dir=r".", file_prefix="sf")
    exit(0)
    
    # Merge them together
    sanfranciscoNet = gearynetDta
    sanfranciscoNet.merge(sanfranciscoCubeNet)
    
    # Write the result.  sanfrancisco_dta is a DynameqNetwork
    sanfranciscoNet.write(dir = ".", file_prefix="SanFrancisco_")
    
