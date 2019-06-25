#### import the simple module from the paraview                                                                                             
from paraview.simple import *
import sys
import yaml
import numpy as np
import math
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
N_points = 10 #used for setting varying opacities at different data points
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
xDMFReader1_Display = Show(xDMFReader1, renderView1)

#****************************************************************
# Set Variable Display
#****************************************************************
#--------------------- Set Representation------------------------
xDMFReader1_Display.SetRepresentationType(Input_data['Variable_properties']['Representation'])
ColorBy(xDMFReader1_Display, ('POINTS', var))
#---------------------Set color map for var----------------------
psiLUT = GetColorTransferFunction(var)
psiLUT.ApplyPreset(color_map, True)

#-------------------------Set Opacity----------------------------
#Get range of var array
var_range = xDMFReader1.PointData.GetArray(var).GetRange()
max = var_range[0]
min = var_range[1]

if Input_data['Variable_properties']['Opacity']['Function_type'] == 1: #Constant Opacity
    psiLUT.EnableOpacityMapping = 1
    psiPWF = GetOpacityTransferFunction(var)
    psiPWF.Points = [var_range[0], opacity_val, 0.5, 0, var_range[1] , opacity_val, 0.5, 0]

elif Input_data['Variable_properties']['Opacity']['Function_type'] == 2: #Varying opacity
    psiLUT.EnableOpacityMapping = 1
    psiPWF = GetOpacityTransferFunction(var)
    
    x_range = np.linspace(min, max, N_points*10)
    x_0_list = x_range[min:max:10]

    sigma = x_range[1] - x_range[0] #width  
    opacity_list = []
    opacity = []
    for i in range(len(x_range)):
        if x_range[i] in x_0_list:
            x_vals = np.linspace(x_range[i]-(2*sigma), x_range[i]+(2*sigma), 5)
            for x in x_vals:
                gauss = math.exp(-1*math.pow(x-x_range[i], 2)/(2*math.pow(sigma,2)))
                opacity.append(abs(x_range[i]*gauss / max))
                opacity_list.append(x)
                opacity_list.append(opacity[-1])
                opacity_list.append(0.5)
                opacity_list.append(0)
        elif x_range[i] not in x_0_list and len(opacity)==i-1:
            opacity_list.append(x_range[i])
            opacity_list.append(0)
            opacity_list.append(0.5)
            opacity_list.append(0)
    opacity_list.append(x_range[i])
    opacity_list.append(0)
    opacity_list.append(0.5)
    opacity_list.append(0)
    
    psiPWF.Points = opacity_list

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

#**************************************************************** 
# Save Image
#**************************************************************** 
xDMFReader1_Display.SetScalarBarVisibility(renderView1, True)
renderView1.Update()
renderView1.ResetCamera()
SaveScreenshot('image.png',renderView1)
