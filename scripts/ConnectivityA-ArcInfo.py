# Project: LDST-ITCP
# Credits: Islands Trust, John Gallo, Randal Greene
# Copyright 2011 Islands Trust
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

# Import system modules...
import sys, string, os, arcgisscripting

# Create the Geoprocessor object...
gp = arcgisscripting.create()

# Path to custom toolbox...
scriptDir = os.path.dirname(sys.argv[0])
toolboxPath = scriptDir + "\\..\\toolbox\\LandscapeDST-ITCP.tbx"
gp.AddToolbox(toolboxPath)

# Check out any necessary licenses...
gp.CheckOutExtension("spatial")

# Script arguments...
compositionRaster = sys.argv[1]
roadsFeatureClass = sys.argv[2]
roadThreatMultiplier = sys.argv[3]
protectedAreasFeatureClass = sys.argv[4]
studyAreaRasterMask = sys.argv[5]
smallestProtectedArea = sys.argv[6]
maxProtectedAreaSeparation = sys.argv[7]
protectedAreaPairsTable = sys.argv[8]
deleteTemps = sys.argv[9]

# Generate Cost Surface from Composition and Roads Threat
gp.addmessage("Started Generating Cost Surface at: " + time.ctime())
# Invert Composition
costTempRaster1 = "%scratchWorkspace%\\costrst1"
gp.SingleOutputMapAlgebra_sa("1 - " + compositionRaster, costTempRaster1)
# Convert Roads Threat to Raster
roadsThreatTempRaster1 = "%scratchWorkspace%\\rdtht1"
gp.FeatureToRaster_conversion(roadsFeatureClass, "ROADS_THT", roadsThreatTempRaster1)
roadsThreatTempRaster2 = "%scratchWorkspace%\\rdtht2"
gp.toolbox = toolboxPath
gp.SetNoDataTo0(roadsThreatTempRaster1, roadsThreatTempRaster2)
# Add Roads to Cost Surface, assigning Roads a very high cost
costTempRaster2 = "%scratchWorkspace%\\costrst2"
gp.SingleOutputMapAlgebra_sa(costTempRaster1 + " + (" + roadThreatMultiplier + " * " + roadsThreatTempRaster2 + ")", costTempRaster2)
gp.addmessage("Finished Generating Cost Surface at: " + time.ctime())
if deleteTemps == "true":
    gp.Delete_management(costTempRaster1)
    gp.Delete_management(roadsThreatTempRaster1)
    gp.Delete_management(roadsThreatTempRaster2)

# Exclude small Protected Areas
gp.addmessage("Started Excluding Protected Areas at: " + time.ctime())
largeProtectedAreasTempFeatureClass = "%scratchWorkspace%\\Scratch.gdb\\lgpas"
gp.Select_analysis(protectedAreasFeatureClass, largeProtectedAreasTempFeatureClass, "Shape_Area > " + smallestProtectedArea)
gp.addmessage("Finished Excluding Protected Areas at: " + time.ctime())

# Convert Protected Areas to Raster
gp.addmessage("Started Converting Protected Areas at: " + time.ctime())
protectedAreasTempRaster = "%scratchWorkspace%\\parst"
gp.FeatureToRaster_conversion(largeProtectedAreasTempFeatureClass, "ObjectID_1", protectedAreasTempRaster)
gp.addmessage("Finished Converting Protected Areas at: " + time.ctime())

# Process each Protected Area
gp.addmessage("Started Processing Protected Areas at: " + time.ctime())
protectedAreas = gp.SearchCursor(protectedAreasTempRaster)
for protectedArea in protectedAreas:
    # Generate separate raster
    paID = str(protectedArea.Value)
    protectedAreaTempRaster = "%scratchWorkspace%\\parst" + paID
    gp.ExtractByAttributes_sa(protectedAreasTempRaster, '"VALUE" = ' + paID, protectedAreaTempRaster)
    # Calc Cost Distance with Backlinks
    costDistanceTempRaster = "%scratchWorkspace%\\cdrst" + paID
    backlinkTempRaster = "%scratchWorkspace%\\blrst" + paID
    gp.CostDistance_sa(protectedAreaTempRaster, costTempRaster2, costDistanceTempRaster, "", backlinkTempRaster)
if deleteTemps == "true":
    gp.Delete_management(costTempRaster2)
gp.addmessage("Finished Processing Protected Areas at: " + time.ctime())

# Determine the Distance between each pair of Protected Areas, limiting pairs to those at least as close as the maxProtectedAreaSeparation
gp.addmessage("Started Processing Protected Area Pair Distance at: " + time.ctime())
gp.GenerateNearTable_analysis(largeProtectedAreasTempFeatureClass, largeProtectedAreasTempFeatureClass, protectedAreaPairsTable, maxProtectedAreaSeparation, "LOCATION", "ANGLE", "ALL", 0)
gp.addmessage("Finished Processing Protected Area Pair Distance at: " + time.ctime())
if deleteTemps == "true":
    gp.Delete_management(largeProtectedAreasTempFeatureClass)

# Process each pair of Protected Areas, deleting self pairs, duplicates, and those that have no corridor
gp.addmessage("Started Processing Pairs of Protected Areas at: " + time.ctime())
corrZonalStatsTempTable = "%scratchWorkspace%\\Scratch.gdb\\corzonsttbl"
protectedAreaPairs = gp.UpdateCursor(protectedAreaPairsTable)
for protectedAreaPair in protectedAreaPairs:
    # Can't make a corridor to yourself; only need to process corridors in one direction
    if protectedAreaPair.IN_FID < protectedAreaPair.NEAR_FID:
        paIDA = str(protectedAreaPair.IN_FID)
        costDistanceTempRasterA = "%scratchWorkspace%\\cdrst" + paIDA
        paIDB = str(protectedAreaPair.NEAR_FID)
        costDistanceTempRasterB = "%scratchWorkspace%\\cdrst" + paIDB
        # Calc Corridor
        corridorTempRaster = "%scratchWorkspace%\\" + "cor" + paIDA + "-" + paIDB
        gp.Corridor_sa(costDistanceTempRasterA, costDistanceTempRasterB, corridorTempRaster)
        # Determine if there are any non-NoData cells in the corridor; this method is not particularly intuitive, but it performs well
        gp.ZonalStatisticsAsTable_sa(studyAreaRasterMask, "Value", corridorTempRaster, corrZonalStatsTempTable, "DATA")
        # zonalStatsTempTable will contain 0 rows if there are only NoData cells (no corridor) and 1 row if there any non-NoData cells (is a corridor)
        rowCount = 0
        corrZonalStatsRows = gp.SearchCursor(corrZonalStatsTempTable)
        for corrZonalStatsRow in corrZonalStatsRows:
            rowCount = 1
        if rowCount == 0:
            protectedAreaPairs.deleteRow(protectedAreaPair)
            if deleteTemps == "true":
                gp.Delete_management(corridorTempRaster)
        if deleteTemps == "true":
            gp.Delete_management(corrZonalStatsTempTable)
    else:
        protectedAreaPairs.deleteRow(protectedAreaPair)
gp.addmessage("Finished Processing Pairs of Protected Areas at: " + time.ctime())
