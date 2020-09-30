# Project: LandAdvisor-ITCP
# Credits: Islands Trust, John Gallo, Randal Greene
# Copyright 2012 Islands Trust
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
toolboxPath = scriptDir + "\\..\\toolbox\\LandAdvisor-ITCP.tbx"
gp.AddToolbox(toolboxPath)

# Check out any necessary licenses...
gp.CheckOutExtension("spatial")

# Script arguments...
# protectedAreaPairsTable = sys.argv[1]
protectedAreaPairsFeatureClass = sys.argv[1]
studyAreaRasterMask = sys.argv[2]
percentageCorridorValuesToKeep = sys.argv[3]
numPercentageCorridorValuesToKeep = float(percentageCorridorValuesToKeep)
permeabilityWeight = sys.argv[4]
corridorEnvelopeWeight = sys.argv[5]
lcpLengthWeight = sys.argv[6]
connectivityOutputRaster = sys.argv[7]
deleteTemps = sys.argv[8]

# Process each pair of Protected Areas - first pass
gp.addmessage("Started Processing Pairs of Protected Areas (pass 1) at: " + time.ctime())
impZonalStatsTempTable = "%scratchWorkspace%\\Scratch.gdb\\impzonsttbl"
stdZonalStatsTempTable = "%scratchWorkspace%\\Scratch.gdb\\stdzonsttbl"
# Determine overall min and max for use in second pass
minOverallLCPLength = 999999999999.0
maxOverallLCPLength = 0.0
minOverallImpermeability = 999999999999.0
maxOverallImpermeability = 0.0
# Remember PA pairs for use in second pass
pairList = []
#protectedAreaPairs = gp.SearchCursor(protectedAreaPairsTable)
protectedAreaPairs = gp.SearchCursor(protectedAreaPairsFeatureClass)
for protectedAreaPair in protectedAreaPairs:
    #paIDA = str(protectedAreaPair.IN_FID)
    paIDA = str(protectedAreaPair.TARGET_FID)
    protectedAreaTempRasterA = "%scratchWorkspace%\\parst" + paIDA
    costDistanceTempRasterA = "%scratchWorkspace%\\cdrst" + paIDA
    #paIDB = str(protectedAreaPair.NEAR_FID)
    paIDB = str(protectedAreaPair.JOIN_FID)
    costDistanceTempRasterB = "%scratchWorkspace%\\cdrst" + paIDB
    backlinkTempRasterB = "%scratchWorkspace%\\blrst" + paIDB
    corridorTempRaster = "%scratchWorkspace%\\" + "cor" + paIDA + "-" + paIDB
    # Calc Least Cost Path (LCP)
    lcpTempRaster = "%scratchWorkspace%\\" + "lcp" + paIDA + "-" + paIDB
    gp.CostPath_sa(protectedAreaTempRasterA, costDistanceTempRasterB, backlinkTempRasterB, lcpTempRaster, "BEST_SINGLE", "VALUE")
    # Estimate LCP Length as LCP Cell Count (potential to improve this) and Compare to Overall
    # Also get Path Cost
    lcpLength = 1.0
    pathCost = 1.0
    lcpTable = gp.SearchCursor(lcpTempRaster)
    for lcpRow in lcpTable:
        if lcpRow.COUNT > lcpLength:
            lcpLength = lcpRow.COUNT
        if lcpRow.PATHCOST > pathCost:
            pathCost = lcpRow.PATHCOST
    if lcpLength < minOverallLCPLength:
        minOverallLCPLength = lcpLength
    if lcpLength > maxOverallLCPLength:
        maxOverallLCPLength = lcpLength
    # Calc Standardized Corridor as Corridor divided by Path Cost
    stdTempRaster = "%scratchWorkspace%\\" + "std" + paIDA + "-" + paIDB
    gp.SingleOutputMapAlgebra_sa(corridorTempRaster + " / " + str(pathCost), stdTempRaster)
    # Create Corridor Envelope by eliminating higher values from Standardized Corridor using percentageCorridorValuesToKeep
    gp.ZonalStatisticsAsTable_sa(studyAreaRasterMask, "Value", stdTempRaster, stdZonalStatsTempTable, "DATA")
    stdZonalStatsRows = gp.SearchCursor(stdZonalStatsTempTable)
    for stdZonalStatsRow in stdZonalStatsRows:
        # only one row; don't really need for loop
        envTempRaster = "%scratchWorkspace%\\" + "env" + paIDA + "-" + paIDB
        cutoff = stdZonalStatsRow.MIN + ((stdZonalStatsRow.MAX - stdZonalStatsRow.MIN) * (numPercentageCorridorValuesToKeep / 100))
        gp.Con_sa(stdTempRaster, stdTempRaster, envTempRaster, "", "VALUE < " + str(cutoff))
    # Extract Corridor cells only within Corridor Envelope
    creTempRaster = "%scratchWorkspace%\\" + "cre" + paIDA + "-" + paIDB
    gp.ExtractByMask_sa(corridorTempRaster, envTempRaster, creTempRaster)
    # Calc Impermeability as Extracted Corridor divided by LCP Length
    impTempRaster = "%scratchWorkspace%\\" + "imp" + paIDA + "-" + paIDB
    gp.SingleOutputMapAlgebra_sa(creTempRaster + " / " + str(lcpLength), impTempRaster)
    # Get Min and Max Impermeability and Compare to Overall
    gp.ZonalStatisticsAsTable_sa(studyAreaRasterMask, "Value", impTempRaster, impZonalStatsTempTable, "DATA")
    impZonalStatsRows = gp.SearchCursor(impZonalStatsTempTable)
    for impZonalStatsRow in impZonalStatsRows:
        # only one row; don't really need for loop
        # RG - debugging start
        gp.addmessage(impTempRaster + ": " + str(impZonalStatsRow.MIN) + " - " + str(impZonalStatsRow.MAX))
        # RG - debugging end
        if impZonalStatsRow.MIN < minOverallImpermeability:
            minOverallImpermeability = impZonalStatsRow.MIN
        if impZonalStatsRow.MAX > maxOverallImpermeability:
            maxOverallImpermeability = impZonalStatsRow.MAX
    # Remember Corridor's Protected Area Pair with LCP Length
    pairList.append([paIDA, paIDB, lcpLength])
    if deleteTemps == "true":
        gp.Delete_management(lcpTempRaster)
        gp.Delete_management(stdTempRaster)
        gp.Delete_management(stdZonalStatsTempTable)
        gp.Delete_management(creTempRaster)
        gp.Delete_management(impZonalStatsTempTable)
gp.addmessage("Finished Processing Pairs of Protected Areas (pass 1) at: " + time.ctime())

# Process each pair of Protected Areas - second pass
gp.addmessage("Started Processing Pairs of Protected Areas (pass 2) at: " + time.ctime())
# Avoid divide by 0!
impermeabilityDifference = maxOverallImpermeability - minOverallImpermeability
if impermeabilityDifference < 1:
    impermeabilityDifference = 1
lengthDifference = maxOverallLCPLength - minOverallLCPLength
if lengthDifference < 1:
    lengthDifference = 1
pairConnectivityRasterList = ""
# RG - debugging start
gp.addmessage("maxOverallImpermeability: " + str(maxOverallImpermeability))
gp.addmessage("minOverallImpermeability: " + str(minOverallImpermeability))
gp.addmessage("impermeabilityDifference: " + str(impermeabilityDifference))
gp.addmessage("maxOverallLCPLength: " + str(maxOverallLCPLength))
gp.addmessage("minOverallLCPLength: " + str(minOverallLCPLength))
gp.addmessage("lengthDifference: " + str(lengthDifference))
# RG - debugging end
for pair in pairList:
    paIDA = pair[0]
    paIDB = pair[1]
    lcpLength = pair[2]
    # Invert/Normalize Impermeability based on overall min and max (A - permeability from the wildlife perspective is desirable)
    # Could develop a new Generic tool or modify existing "Max Score Inverted Normalization from Raster" tool to take an external parm for Max
    impTempRaster = "%scratchWorkspace%\\" + "imp" + paIDA + "-" + paIDB
    prxTempRaster = "%scratchWorkspace%\\" + "prx" + paIDA + "-" + paIDB
    gp.SingleOutputMapAlgebra_sa("(" + str(maxOverallImpermeability) + " - " + impTempRaster + ") / " + str(impermeabilityDifference), prxTempRaster)
    prmTempRaster = "%scratchWorkspace%\\" + "prm" + paIDA + "-" + paIDB
    gp.toolbox = toolboxPath
    gp.SetNoDataTo0(prxTempRaster, prmTempRaster)
    # Invert/Normalize Corridor Envelope (B - crucial corridors between core areas need to be considered, even if they have low permeability)
    envTempRaster = "%scratchWorkspace%\\" + "env" + paIDA + "-" + paIDB
    nenTempRaster = "%scratchWorkspace%\\" + "nen" + paIDA + "-" + paIDB
    gp.toolbox = toolboxPath
    gp.MaxScoreInvertedNormalizationFromRaster(envTempRaster, studyAreaRasterMask, nenTempRaster)
    # Invert/Normalize LCP Length based on overall min and max (C - shorter corridors are better than longer corridors of the same permeability)
    # Then make a constant raster covering Envelope from Normalized LCP Length
    nrmLCPLength = float(maxOverallLCPLength - lcpLength) / float(lengthDifference)
    nleTempRaster = "%scratchWorkspace%\\" + "nle" + paIDA + "-" + paIDB
    gp.SingleOutputMapAlgebra_sa(envTempRaster + " - " + envTempRaster + " + " + str(nrmLCPLength), nleTempRaster)
    nllTempRaster = "%scratchWorkspace%\\" + "nll" + paIDA + "-" + paIDB
    gp.toolbox = toolboxPath
    gp.SetNoDataTo0(nleTempRaster, nllTempRaster)
    # Calc Pair Connectivity as Weighted Sum of A, B, C
    pcnTempRaster = "%scratchWorkspace%\\" + "pcn" + paIDA + "-" + paIDB
    #gp.toolbox = toolboxPath
    #gp.WeightedSumWithMaxScoreNormalization(prmTempRaster + " Value " + permeabilityWeight + "; " + nenTempRaster + " Value " + corridorEnvelopeWeight + "; " + nllTempRaster + " Value " + lcpLengthWeight, studyAreaRasterMask, pcnTempRaster)
    gp.SingleOutputMapAlgebra_sa("(" + prmTempRaster + " * " + permeabilityWeight + ") + (" + nenTempRaster + " * " + corridorEnvelopeWeight + ") + (" + nllTempRaster + " * " + lcpLengthWeight + ")", pcnTempRaster)
    # Add to raster list for use in next step
    if len(pairConnectivityRasterList) > 0:
        pairConnectivityRasterList = pairConnectivityRasterList + ";"
    pairConnectivityRasterList = pairConnectivityRasterList + "'" + pcnTempRaster + "'"
    if deleteTemps == "true":
        gp.Delete_management(impTempRaster)
        gp.Delete_management(prxTempRaster)
        gp.Delete_management(prmTempRaster)
        gp.Delete_management(envTempRaster)
        gp.Delete_management(nenTempRaster)
        gp.Delete_management(nleTempRaster)
        gp.Delete_management(nllTempRaster)
gp.addmessage("Finished Processing Pairs of Protected Areas (pass 2) at: " + time.ctime())

# Calc Overall Connectivity as Max of all Pair Connectivity rasters
gp.addmessage("Started Calculating Overall Connectivity at: " + time.ctime())
connTempRaster1 = "%scratchWorkspace%\\conntmprst1"
gp.CellStatistics_sa(pairConnectivityRasterList, connTempRaster1, "MAXIMUM")
# Because corridor rasters only kept highest X percent of values, renormalize using non-0 min and max values
connTempRaster2 = "%scratchWorkspace%\\conntmprst2"
gp.SetNull_sa(connTempRaster1, connTempRaster1, connTempRaster2, "VALUE = 0")
gp.toolbox = toolboxPath
connTempRaster3 = "%scratchWorkspace%\\conntmprst3"
gp.ScoreRangeNormalizationFromRaster(connTempRaster2, studyAreaRasterMask, connTempRaster3)
gp.SetNoDataTo0(connTempRaster3, connectivityOutputRaster)
if deleteTemps == "true":
    gp.Delete_management(connTempRaster1)
    gp.Delete_management(connTempRaster2)
    gp.Delete_management(connTempRaster3)
gp.addmessage("Finished Calculating Overall Connectivity at: " + time.ctime())

# Cleanup
if deleteTemps == "true":
    gp.addmessage("Started Cleanup at: " + time.ctime())
    for pair in pairList:
        paIDA = pair[0]
        paIDB = pair[1]
        pcnTempRaster = "%scratchWorkspace%\\" + "pcn" + paIDA + "-" + paIDB
        gp.Delete_management(pcnTempRaster)
        corTempRaster = "%scratchWorkspace%\\" + "cor" + paIDA + "-" + paIDB
        gp.Delete_management(corTempRaster)
    protectedAreasTempRaster = "%scratchWorkspace%\\parst"
    protectedAreas = gp.SearchCursor(protectedAreasTempRaster)
    for protectedArea in protectedAreas:
        paID = str(protectedArea.Value)
        protectedAreaTempRaster = "%scratchWorkspace%\\parst" + paID
        gp.Delete_management(protectedAreaTempRaster)
        costDistanceTempRaster = "%scratchWorkspace%\\cdrst" + paID
        gp.Delete_management(costDistanceTempRaster)
        backlinkTempRaster = "%scratchWorkspace%\\blrst" + paID
        gp.Delete_management(backlinkTempRaster)
    gp.Delete_management(protectedAreasTempRaster)
    gp.addmessage("Finished Cleanup at: " + time.ctime())
