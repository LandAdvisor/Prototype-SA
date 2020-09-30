#**********************************************************************
# Description:
# Attempting to create the summary shapefiles for the first iteration
# through the analysis (i.e. the values based onthe current data), rather
# than after the maximize-short-term-gains hueristic has simulated the
# conservation of some sites.
#**********************************************************************
# Standard error handling - put everything in a try/except block
#try:
# Import system modules
import sys, string, os, arcgisscripting
# Create the Geoprocessor object
gp = arcgisscripting.create()
# Path to custom toolbox...
scriptDir = os.path.dirname(sys.argv[0])
toolboxPath = scriptDir + "\\..\\toolbox\\LandscapeDST-LittleKaroo.tbx"
gp.AddToolbox(toolboxPath)

# Check out any necessary licenses...
gp.CheckOutExtension("spatial")

# Get input arguments - table name, field name
IterationNumber = sys.argv[1]
#field_found = fields.Next()
if IterationNumber == 0:
    gp.AddMessage("This is the first iteration") 
    gp.makesummaryshapefile
else:
    gp.AddMessage("This is not the first iteration, no shapefile being created"        
# Handle script errors
#except Exception, errMsg:
# If we have messages of severity error (2), we assume a GP tool raised it,
#  so we'll output that.  Otherwise, we assume we raised the error and the
#  information is in errMsg.
#
#if gp.GetMessages(2):   
#    gp.AddError(GP.GetMessages(2))
#else:
#    gp.AddError(str(errMsg))
