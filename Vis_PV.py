from paraview.simple import *
import sys
import yaml
import numpy as np
import math
#### disable automatic camera reset on 'Show'                                                      
paraview.simple._DisableFirstRenderCameraReset()

# Set up the point of view (location, angle, etc.)

def set_defaultCamera(renderView1):
    '''
    Set view and camera properties to a default 
    specified below
    '''
    renderView1.ViewSize = [904, 501]
    renderView1.AxesGrid = 'GridAxes3DActor'
    renderView1.CenterOfRotation = [0.0, 0.0, -22.98529815673828]
    renderView1.StereoType = 0
    renderView1.CameraPosition = [-95.16305892510273, 754.3761479590994, 426.10491067642846]
    renderView1.CameraFocalPoint = [43.11431452669897, 23.554652286151217, -46.78071794111179]
    renderView1.CameraViewUp = [0.09790398117889891, -0.5275190119519493, 0.843882990999677]
    renderView1.CameraParallelScale = 715.9367631158923
    renderView1.Background = [0.0, 0.0, 0.0]
    return renderView1

def load_InputData():
    '''
    Read data from yaml input file
    '''
    Input_stream = open("InputVis_PV.yaml", 'r')
    Input_data = yaml.load(Input_stream)
    return Input_data

def readData_Xdmf(xdmf_FilePath): 
    '''
    Read data from XDMF file specified in 
    yaml file.
    '''
    try:
        xDMFReader1 = XDMFReader(FileNames=xdmf_FilePath)
    except FileNotFoundError:
        sys.exit("No such file at file location specified")
    xDMFReader1 = GetActiveSource()
    renderView1 = GetActiveViewOrCreate('RenderView')
    xDMFReader1_Display = GetDisplayProperties(xDMFReader1, view=renderView1)
    return renderView1, xDMFReader1, xDMFReader1_Display

def set_Representation(representation, renderView1, xDMFReader1_Display):
    '''
    Set representation and update view 
    '''
    xDMFReader1_Display.Representation = representation
    renderView1.Update()
    return renderView1, xDMFReader1_Display

def set_colorMap(var, renderView1, xDMFReader1_Display, color_map):
    '''
    Set color map to one of preset ParaView color maps.
    If color map entered is invalid, color map is set to 
    default.
    '''
    ColorBy(xDMFReader1_Display, ('POINTS', var))
    Var_LUT = GetColorTransferFunction(var)
    try:
        Var_LUT.ApplyPreset(color_map, True)
    except:
        print('Using default color map')
        Var_LUT.ApplyPreset('Viridis (matplotlib)', True)
    xDMFReader1_Display.SetScalarBarVisibility(renderView1, True)
    xDMFReader1_Display.SetScaleArray = ['POINTS', var]
    xDMFReader1_Display.ScaleTransferFunction = 'PiecewiseFunction'
    return xDMFReader1_Display, renderView1, Var_LUT 

def tetrahedralize(xDMFReader1, renderView1):
    '''
    Apply tetrahedralize filter and update view
    '''
    tetrahedralize1 = Tetrahedralize(Input=xDMFReader1)
    Hide(xDMFReader1, renderView1)
    xDMFReader1 = Show(tetrahedralize1, renderView1)
    renderView1.Update()
    return xDMFReader1, renderView1

def set_Opacity(var, fn_type, opacity_val, renderView1, xDMFReader1, Var_LUT):
    '''
    Set opacity based on option chosen in yaml input file:
    1 : Set to constant opacity specified by user
    2 : vary opacity as a function of variable (the variable 
        specified in yaml input file as Variable_name
    '''
    if fn_type!=1 and fn_type!=2:
        sys.exit("The Opacity  option specified in the input file is invalid. Enter 1 or 2 for type of function")
    #Get range of var array
    var_range = xDMFReader1.PointData.GetArray(var).GetRange()
    max = var_range[0]
    min = var_range[1]
    N_points = 10

    if fn_type == 1: #Constant Opacity
        Var_LUT.EnableOpacityMapping = 1
        Var_PWF = GetOpacityTransferFunction(var)
        Var_PWF.Points = [var_range[0], opacity_val, 0.5, 0, var_range[1] , opacity_val, 0.5, 0]

    elif fn_type == 2: #Varying opacity
        Var_LUT.EnableOpacityMapping = 1
        Var_PWF = GetOpacityTransferFunction(var)
    
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
        Var_PWF.Points = opacity_list
    renderView1.Update()
    return renderView1

def apply_clip(clip_Properties, var, renderView1, xDMFReader1, xDMFReader1_Display):
    clip1 = Clip(Input=xDMFReader1)
    if clip_Properties['Clip_type'] == 'Plane':
        clip1.ClipType = 'Plane'
        clip1.Scalars = ['POINTS', var]
        clip1.ClipType.Origin = clip_Properties['Origin']
        clip1.ClipType.Normal = clip_Properties['Normal']
    elif clip_Properties['Clip_type'] == 'Box':
        clip1.ClipType = 'Box'
        clip1.Scalars = ['POINTS', var]
        clip1.ClipType.Position = clip_Properties['Position']
        clip1.ClipType.Rotation = clip_Properties['Rotation']
        clip1.ClipType.Scale = clip_Properties['Scale']
    elif clip_Properties['Clip_type'] == 'Sphere':
        clip1.ClipType = 'Sphere'
        clip1.Scalars = ['POINTS', var]
        clip1.ClipType.Center = clip_Properties['Center_s']
        clip1.ClipType.Radius = clip_Properties['Radius_s']
    elif clip_Properties['Clip_type'] == 'Cylinder':
        clip1.ClipType = 'Cylinder'
        clip1.Scalars = ['POINTS', var]
        clip1.ClipType.Center = clip_Properties['Center_c']
        clip1.ClipType.Radius = clip_Properties['Radius_c']
        clip1.ClipType.Axis = clip_Properties['Axis']
    #--Hide previous data display before filter--
    Hide(xDMFReader1, renderView1)
    xDMFReader1_Display = Show(clip1,renderView1)
    return renderView1, xDMFReader1_Display

def apply_slice(slice_Properties, var, renderView1, xDMFReader1, xDMFReader1_Display):
    slice1 = Slice(Input=xDMFReader1)
    if slice_Properties['Slice_type'] == 'Plane':
        slice1.SliceType = 'Plane'
        slice1.SliceOffsetValues = [0.0]
        slice1.SliceType.Origin= slice_Properties['Origin']
        slice1.SliceType.Normal= slice_Properties['Normal']
    elif slice_Properties['Slice_type'] == 'Box':
        slice1.SliceType = 'Box'
        slice1.SliceOffsetValues = [0.0]
        slice1.SliceType.Position= slice_Properties['Position']
        slice1.SliceType.Rotation= slice_Properties['Rotation']
        slice1.SliceType.Scale= slice_Properties['Scale']
    elif slice_Properties['Slice_type'] == 'Sphere':
        slice1.SliceType = 'Sphere'
        slice1.SliceOffsetValues = [0.0]
        slice1.SliceType.Center = slice_Properties['Center_s']
        slice1.SliceType.Radius = slice_Properties['Radius_s']
    elif slice_Properties['Slice_type'] == 'Cylinder':
        slice1.SliceType = 'Cylinder'
        slice1.SliceOffsetValues = [0.0]
        slice1.SliceType.Center = slice_Properties['Center_c']
        slice1.SliceType.Radius = slice_Properties['Radius_c']
        slice1.SliceType.Axis = slice_Properties['Axis']
    #--Hide previous data display before filter--
    Hide(xDMFReader1, renderView1)
    xDMFReader1_Display = Show(slice1,renderView1)
    return renderView1, xDMFReader1_Display

#****************************************************************
# Warp - not done yet-
#****************************************************************
def apply_warp(var, xDMFReader1, renderView1):
    '''
    Add
    '''
    slice1 = Slice(Input=xDMFReader1)
    slice1.SliceType = 'Plane'
    slice1.SliceOffsetValues = [0.0]
    slice1.SliceType.Origin = [3.141592653589793, 3.141592653589793, 3.141592653589793]
    slice1.SliceType.Normal = [0.0, 0.0, 1.0]
    #xDMFReader1_Display.ColorArrayName = ['POINTS', var]
    warpByScalar1 = WarpByScalar(Input=slice1)
    warpByScalar1.Scalars = ['POINTS', var]
    Hide(xDMFReader1, renderView1)
    xDMFReader1_Display = Show(warpByScalar1, renderView1)
    return renderView1 

def save_images(renderView1, xDMFReader1):
    '''
    Saves single image or multiple images based on number of 
    time steps in data. One image per time step saved
    '''
    time_steps = xDMFReader1.TimestepValues
    try:
        n_steps = len(time_steps)
    except:
        n_steps = 1
        time_steps = [time_steps]
    if n_steps ==1:
        SaveScreenshot('image.png', renderView1)
    elif n_steps > 1:
        anim = GetAnimationScene()
        anim.PlayMode = 'Snap To TimeSteps'
        for n in range(n_steps):
            print('loop',n)
            anim.AnimationTime = time_steps[n]
            view = GetRenderView()
            SaveScreenshot('image_%s.png' %n, view)
    return None

def main():
    '''
    Render image(s) based on parameters specified 
    '''
    # Get data from file, set default camera properties
    Input_data = load_InputData()
    renderView1, xDMFReader1, xDMFReader1_Display = readData_Xdmf(Input_data['file_path'])
    set_defaultCamera(renderView1)
    # variable name to 'var'
    var = Input_data['Variable_properties']['Variable_name']

    # Apply filters
    try:
        if Input_data['Filter']['Clip']['Apply'] == True:
            renderView1, xDMFReader1_Display = apply_clip(Input_data['Filter']['Clip'], 
                                                          var, renderView1, xDMFReader1, xDMFReader1_Display)
        if Input_data['Filter']['Slice']['Apply'] == True:
            renderView1, xDMFReader1_Display = apply_slice(Input_data['Filter']['Slice'], 
                                                           var, renderView1, xDMFReader1, xDMFReader1_Display)
    except Input_data['Filter']['Clip']['Clip_type'] == Input_data['Filter']['Slice']['Slice_type']:
        sys.exit('Clip type and Slice type chosen cannot be applied simulatneously')
    # Not working 
    #elif Input_data['Filter']['Contour']['Apply'] == True:
    #    renderView1, xDMFReader1_Display = apply_contour(Input_data['Filter']['Contour']['Contour_variable'], renderView1, 
    #                                                     xDMFReader1, xDMFReader1_Display)
    renderView1.Update()

    # Update Display
    renderView1, xDMFReader1_Display = set_Representation(Input_data['Variable_properties']['Representation'], renderView1, 
                                                          xDMFReader1_Display)
    xDMFReader1_Display, renderView1, Var_LUT = set_colorMap(var, renderView1, xDMFReader1_Display, 
                                                             Input_data['Variable_properties']['Color_map'])
    renderView1 = set_Opacity(var, Input_data['Variable_properties']['Opacity']['Function_type'], 
                              Input_data['Variable_properties']['Opacity']['Value'], renderView1, xDMFReader1, Var_LUT)
    #xDMFReader1, renderView1 = tetrahedralize(xDMFReader1, renderView1)
    if Input_data['Warp']['Add_warp'] == True:
        renderView1 = apply_warp(var, xDMFReader1, renderView1)
    renderView1.Update()
    renderView1.ResetCamera()

    # Save images
    save_images(renderView1, xDMFReader1)

    return None


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
