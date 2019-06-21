#### import the simple module from the paraview                                                                                             
from paraview.simple import *
import sys

#### disable automatic camera reset on 'Show'                                                      
paraview.simple._DisableFirstRenderCameraReset()

#copied from ParaviewGWRipple.py (point of view stuff)************
# ----------------------------------------------------------------
# Set up the point of view (location, angle, etc.)
# ----------------------------------------------------------------
renderView1 = CreateView('RenderView')
renderView1.ViewSize = [904, 501]
renderView1.AxesGrid = 'GridAxes3DActor'
renderView1.CenterOfRotation = [0.0, 0.0, -22.98529815673828]
renderView1.StereoType = 0
renderView1.CameraPosition = [-95.16305892510273, 754.3761479590994, 426.10491067642846]
renderView1.CameraFocalPoint = [43.11431452669897, 23.554652286151217, -46.78071794111179]
renderView1.CameraViewUp = [0.09790398117889891, -0.5275190119519493, 0.843882990999677]
renderView1.CameraParallelScale = 715.9367631158923
renderView1.Background = [0.0, 0.0, 0.0]

#****************************************************************
# Load data from Input file
#****************************************************************
Input_stream = open("InputVis_PV.yaml", 'r')
Input_data = yaml.load(Input_stream)

#--------------------Set some variables here---------------------
# From Variable_properties
var = Input_data['Variable_properties']['Variable_name']
color_map = Input_data['Variable_properties']['Color_map']
opacity_val = Input_data['Variable_properties']['Opacity']['Value']
N_points = 50 #used for setting varying opacities at different data points
# From Filter
contour_var = Input_data['Filter']['Contour']['Contour_variable'] 

#---------------------Input Error Handling-----------------------
#Need to ensure that the variables being checked for are not null - return error message
#Representation
if Input_data['Variable_properties']['Representation'] is None:
    sys.exit("No representation was specified")
if Input_data['Variable_properties']['Color_map'] is None:
    print("Using default color map")
    color_map = 'Viridis (matplotlib)'
if Input_data['Filter']['Contour']['Contour_variable']:
    sys.exit("Cannot color by and contour by same variable")
#Opacity
#Function_type
#Value
#Filter - check from Apply = true, string should be given 

#--------------------------Read XDMF-----------------------------
#Handle file not found error
try:
    xDMFReader1 = XDMFReader(FileNames=[Input_data['file_path']])
except FileNotFoundError:
    sys.exit("No such file at file location specified")

xDMFReader1 = GetActiveSource()
renderView1 = GetActiveViewOrCreate('RenderView')

#****************************************************************
# Set Variable Display
#****************************************************************
#--------------------- Set Representation------------------------
xDMFReader1_Display.SetRepresentationType(Input_data['Variable_properties']['Representation'])

#---------------------Set color map for var----------------------
psiLUT = GetColorTransferFunction(var)
psiLUT.ApplyPreset(color_map, True)

#-------------------------Set Opacity----------------------------
#Get range of var array
var_pointData = xDMFReader1.PointData.GetArray(var)
var_range = xDMFReader1.PointData.GetArray(var).GetRange()
 
if Input_data['Variable_properties']['Opacity']['Function_type'] == 1: #Constant Opacity
    psiLUT.EnableOpacityMapping = 1
    psiPWF.GetOpacityTransferFunction(var)
    psiPWF.Points = [var_range[0], opacity_val, 0.5, 0, var_range[1] , opacity_val, 0.5, 0]

elif Input_data['Variable_properties']['Opacity']['Function_type'] == 2: #Varying opacity
    psiLUT.EnableOpacityMapping = 1
    psiPWF.GetOpacityTransferFunction(var)
    var_pointData_norm =var_pointData / var_range[1] #to use as opacity value
    #Initialize variables for loop
    num = int(len(var_pointData_norm)/N_points) + 1
    psiPWF.Points = []
    count = 0
    #Creating list of opacitites for psiPWF.Points list using N_points
    for points in N_points-1:
        psiPWF.Points.append(var_pointData[count])
        psiPWF.Points.append(var_pointData_norm[count])
        psiPWF.Points.append(0.5)
        psiPWF.Points.append(0.0)
        count = count + num
    #maybe add last point as well to make sure
#Should be a better way to do this^^^^^^

#****************************************************************                                     
# Apply Filter
#****************************************************************
if Input_data['Filter']['Clip']['Apply'] is True: #For Clip
clip1 = Clip(Input=xDMFReader1)
    if Input_data['Filter']['Clip']['Clip_type'] is 'Plane':
        clip1.ClipType = 'Plane'
        clip1.Scalars = ['POINTS', var]
        clip1.ClipType.Origin = Input_data['Filter']['Clip']['Origin']
        clip1.ClipType.Normal = Input_data['Filter']['Clip']['Normal']
        xDMFReader1_Display = Show(clip1,renderView1)
    #Do for all clip types 
elif Input_data['Filter']['Slice']['Apply'] is True: #For Slice
    slice1 = Slice(Input=xDMFReader1)
    if Input_data['Filter']['Slice']['Slice_type'] is 'Plane':
        slice1.SliceType = 'Plane'
        slice1.SliceOffsetValues = [0.0]
        slice1.SliceType.Origin =Input_data['Filter']['Slice']['Origin']
        clip1.ClipType.Normal= Input_data['Filter']['Slice']['Normal']
        xDMFReader1_Display = Show(slice1,renderView1)
    #Do for all slice types                                
elif Input_data['Filter']['Contour']['Apply'] is True: #For Contour
    #make sure contour var and color var are different
    contour1 = Contour(Input=xDMFReader1)
    contour1.ContourBy = ['POINTS', contour_var]
    contour1.Isosurfaces = [0.0]
    contour1.PointMergeMethod = 'Uniform Binning'
    xDMFReader1_Display = Show(contour1,renderView1)

#****************************************************************
# Camera Movement
#****************************************************************

