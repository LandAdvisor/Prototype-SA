#**********************************************************************
# Description:
# Attempting to create the summary shapefiles for the final iteration.
# By John Gallo, April 7, 2012
#**********************************************************************
# Import system modules
import sys, string, os, arcgisscripting, arcpy
# Create the Geoprocessor object
gp = arcgisscripting.create()
# Path to custom toolbox...
scriptDir = os.path.dirname(sys.argv[0])
toolboxPath = scriptDir + "\\..\\toolbox\\LandscapeDST-LittleKaroo.tbx"
gp.AddToolbox(toolboxPath)

# Check out any necessary licenses...
gp.CheckOutExtension("spatial")

# Get input arguments - table name, field name
RowCount = sys.argv[1]
Outputmessage = sys.argv[2]
MinimumMngmtQuality = sys.argv[3]

# Local variables:
PROTECTED_AREAS_DISSOLVED_shp = "%scratchworkspace%\\PROTECTED_AREAS_DISSOLVED.shp"
composition = "%workspace%\\composition"
connectivity = "%workspace%\\connectivity"
PROTECTED_AREAS_DISSOLVED_FirstIteration_shp = "%workspace%\\PROTECTED_AREAS_DISSOLVED_FirstIteration.shp"
connectivity1 = "%workspace%\\connectivity1"
composition1 = "%workspace%\\composition1"

#Check to see what iteration number the model is on, and act accordingly
if RowCount == "0":
    gp.AddMessage("This is the final iteration") 
    gp.PrepforConnectivityScript(MinimumManagementQuality)
    # Process: Copy Features
    arcpy.CopyFeatures_management(PROTECTED_AREAS_DISSOLVED_shp, PROTECTED_AREAS_DISSOLVED_FinalIteration_shp, "", "0", "0", "0")
 
else:
    gp.AddMessage("The budget has not been met, no PROTECTED_AREAS_DISSOLVED_FinalIteration shapefile being created.  Note however, that this may be the maximum number of iterations allowed.  See JIRA Task ")

#have an output variable so that the script tool can be linked as a precondition to another model
gp.AddMessage("OutputMessage")




