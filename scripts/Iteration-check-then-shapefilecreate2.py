#**********************************************************************
# Description:
# Attempting to create the summary shapefiles for the first iteration
# through the analysis (i.e. the values based onthe current data), rather
# than after the maximize-short-term-gains hueristic has simulated the
# conservation of some sites.
# Thanks to John Shaeffer of JuniperGIS for giving me the skeleton of this s
# script from one of his class modules
#**********************************************************************
# Import system modules
import sys, string, os, arcgisscripting, arcpy
# Create the Geoprocessor object
gp = arcgisscripting.create()
# Path to custom toolbox...
scriptDir = os.path.dirname(sys.argv[0])
toolboxPath = scriptDir + "\\..\\toolbox\\LandAdvisor-LittleKaroo.tbx"
gp.AddToolbox(toolboxPath)

# Check out any necessary licenses...
gp.CheckOutExtension("spatial")

# Get input arguments - table name, field name
IterationNumber = sys.argv[1]
Outputmessage = sys.argv[2]

# Local variables:
PROTECTED_AREAS_DISSOLVED_shp = "%scratchworkspace%\\PROTECTED_AREAS_DISSOLVED.shp"
composition = "%workspace%\\composition"
connectivity = "%workspace%\\connectivity"
bookhab_mv = "%workspace%\\bookhab_mv"
PROTECTED_AREAS_DISSOLVED_FirstIteration_shp = "%workspace%\\PROTECTED_AREAS_DISSOLVED_FirstIteration.shp"
connectivity1 = "%workspace%\\connectivity1"
composition1 = "%workspace%\\composition1"
bookhab_mv1 = "%workspace%\\bookhab_mv1"

#Check to see what iteration number the model is on, and act accordingly
if IterationNumber == "0":
    gp.AddMessage("This is the first iteration") 
    gp.makesummaryshapefile()
    # Process: Copy Features
    arcpy.CopyFeatures_management(PROTECTED_AREAS_DISSOLVED_shp, PROTECTED_AREAS_DISSOLVED_FirstIteration_shp, "", "0", "0", "0")
    # Process: Copy Raster
    arcpy.CopyRaster_management(connectivity, connectivity1, "", "", "", "NONE", "NONE", "")
    # Process: Copy Raster (2)
    arcpy.CopyRaster_management(composition, composition1, "", "", "", "NONE", "NONE", "")
    # Process: Copy Raster (2)
    arcpy.CopyRaster_management(bookhab_mv, bookhab_mv1, "", "", "", "NONE", "NONE", "")
else:
    gp.AddMessage("This is not the first iteration, no shapefile being created")

#have an output variable so that the script tool can be linked as a precondition to another model
gp.AddMessage("OutputMessage")




