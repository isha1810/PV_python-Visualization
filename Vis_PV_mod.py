from paraview.simple import *
import sys
import yaml
import numpy as np
import math
#### disable automatic camera reset on 'Show'                                                      
paraview.simple._DisableFirstRenderCameraReset()

# From ParaviewGWRipple.py (camera view stuff)************
# Set up the point of view (location, angle, etc.)

def set_defaultCamera(renderView1):
    '''
    Add
    '''
   # renderView1 = CreateView('RenderView')
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
    Add 
    '''
    Input_stream = open("InputVis_PV.yaml", 'r')
    Input_data = yaml.load(Input_stream)
    return Input_data

def readData_Xdmf(xdmf_FilePath): 
    '''
    Add
    '''
    try:
        xDMFReader1 = XDMFReader(FileNames=xdmf_FilePath)
    except FileNotFoundError:
        sys.exit("No such file at file location specified")
    xDMFReader1 = GetActiveSource()
    renderView1 = GetActiveViewOrCreate('RenderView')
    xDMFReader1_Display = GetDisplayProperties(xDMFReader1, view=renderView1)
    #xDMFReader_Display = Show(xDMFReader1, renderView1)
    return renderView1, xDMFReader1, xDMFReader1_Display

def set_Representation(representation, renderView1, xDMFReader1_Display):
    '''
    Add
    '''
    xDMFReader1_Display.Representation = representation
    renderView1.Update()
    return renderView1, xDMFReader1_Display

def set_colorMap(var, renderView1, xDMFReader1_Display, color_map):
    '''
    Add
    '''
    ColorBy(xDMFReader1_Display, ('POINTS', var))
    Var_LUT = GetColorTransferFunction(var)
    Var_LUT.ApplyPreset(color_map, True)
    xDMFReader1_Display.SetScalarBarVisibility(renderView1, True)
    xDMFReader1_Display.SetScaleArray = ['POINTS', var]
    xDMFReader1_Display.ScaleTransferFunction = 'PiecewiseFunction'
    return xDMFReader1_Display, renderView1, Var_LUT 

    #Tetrahedralize
    #---------------------Tetrahedralize-----------------------------
    #tetrahedralize1 = Tetrahedralize(Input=xDMFReader1)
    #xDMFReader1_tetra = Show(tetrahedralize1, renderView1)
    #Hide(scalarWave3DPeriodicVol_dataxmf, renderView1)
    #xDMFReader1_Display.SetScalarBarVisibility(renderView1, True)
    
def set_Opacity(var, fn_type, opacity_val, renderView1, xDMFReader1, Var_LUT):
    '''
    Add
    '''
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

def apply_clip(clip_type, origin, normal, renderView1, xDMFReader1, xDMFReader1_Display):
    clip1 = Clip(Input=xDMFReader1)
    if clip_type == 'Plane':
        clip1.ClipType = 'Plane'
        clip1.Scalars = ['POINTS', var]
        clip1.ClipType.Origin = origin
        clip1.ClipType.Normal = normal
        #------Hide previous data display before filter-----------
        Hide(xDMFReader1, renderView1)
        xDMFReader1_Display = Show(clip1,renderView1)
    #Do for all clip types 
    return renderView1, xDMFReader1_Display

def apply_slice(slice_type, origin, normal, renderView1, xDMFReader1, xDMFReader1_Display):
    slice1 = Slice(Input=xDMFReader1)
    if slice_type == 'Plane':
        slice1.SliceType = 'Plane'
        slice1.SliceOffsetValues = [0.0]
        slice1.SliceType.Origin= origin
        slice1.SliceType.Normal= normal
        #------Hide previous data display before filter-----------                                                   
        Hide(xDMFReader1, renderView1)
        xDMFReader1_Display = Show(slice1,renderView1)
    #Do for all slice types                                
    return renderView1, xDMFReader1_Display

def apply_contour(contour_var, renderView1, xDMFReader1, xDMFReader1_Display):
    #make sure contour var and color var are different
    print('In contour')
    contour1 = Contour(Input=xDMFReader1)
    #print('created new contour object')
    contour1.ContourBy = ['POINTS', contour_var]
    #print(type(contour_var))
    #print('set contour by var')
    contour1.Isosurfaces = [0.0]
    #print('isosurfaces')
    contour1.PointMergeMethod = 'Uniform Binning'
    #print('point merge')
    #------Hide previous data display before filter-----------                                                    
    Hide(xDMFReader1,renderView1)
    xDMFReader1_Display = Show(contour1,renderView1)
    #print('show')
    xDMFReader1_Display.Representation = 'Surface'
    xDMFReader1_Display.ColorArrayName = ['POINTS', 'Psi']
    xDMFReader1_Display.LookupTable = psiLUT
    xDMFReader1_Display.ScaleTransferFunction = 'PiecewiseFunction'
    return renderView1, xDMFReader1_Display

#****************************************************************
# Camera Movement
#****************************************************************





#****************************************************************
# Warp
#****************************************************************
def apply_warp():
#if Input_data['Warp']['Add_warp'] == True:
    #tetrahedralize1 = Tetrahedralize(Input=xDMFReader1)
    #xDMFReader1_tetra = Show(tetrahedralize1, renderView1)
    Hide(xDMFReader1, renderView1)
#    Hide(xDMFReader1_Display, renderView1)
#    ColorBy(xDMFReader1, ('POINTS', var))
    slice1 = Slice(Input=xDMFReader1)
    slice1.SliceType = 'Plane'
    slice1.SliceOffsetValues = [0.0]
    slice1.SliceType.Origin = [3.141592653589793, 3.141592653589793, 3.141592653589793]
    slice1.SliceType.Normal = [0.0, 0.0, 1.0]
    #xDMFReader1_Display = Show(slice1, renderView1)
    xDMFReader1_Display.ColorArrayName = ['POINTS', var]
    #warp:
    warpByScalar1 = WarpByScalar(Input=slice1)
    warpByScalar1.Scalars = ['POINTS', var]
    xDMFReader1_Display = Show(warpByScalar1, renderView1)


#------------------Display Options------------------------------
#renderView1.Update()
#renderView1.ResetCamera()
#ColorBy(xDMFReader1_Display, ('POINTS', var))
#xDMFReader1_Display.SetScalarBarVisibility(renderView1, True)

#**************************************************************** 
# Save Image
#**************************************************************** 
#SaveScreenshot('image.png',renderView1)

def main():
    '''
    Add docstring
    '''
    print('Data Input')
    # Get data from file first
    Input_data = load_InputData()
    renderView1, xDMFReader1, xDMFReader1_Display = readData_Xdmf(Input_data['file_path'])
    set_defaultCamera(renderView1)
    # Apply filters 
    if Input_data['Filter']['Clip']['Apply'] == True:
        renderView1, xDMFReader1_Display = apply_clip(Input_data['Filter']['Clip']['Clip_type'], 
                                                      Input_data['Filter']['Clip']['Origin'],
                                                      Input_data['Filter']['Clip']['Normal'], renderView1, xDMFReader1, xDMFReader1_Display)
    elif Input_data['Filter']['Slice']['Apply'] == True:
        renderView1, xDMFReader1_Display = apply_slice(Input_data['Filter']['Slice']['Slice_type'], Input_data['Filter']['Slice']['Origin'],
                                                       Input_data['Filter']['Slice']['Normal'], renderView1, xDMFReader1, xDMFReader1_Display)
    elif Input_data['Filter']['Contour']['Apply'] == True:
        renderView1, xDMFReader1_Display = apply_contour(Input_data['Filter']['Contour']['Contour_variable'], renderView1, 
                                                         xDMFReader1, xDMFReader1_Display)

    renderView1.Update()
    print('Display Update')
    # Update Display
    renderView1, xDMFReader1_Display = set_Representation(Input_data['Variable_properties']['Representation'], renderView1, 
                                                          xDMFReader1_Display)
    xDMFReader1_Display, renderView1, Var_LUT = set_colorMap(Input_data['Variable_properties']['Variable_name'], renderView1, 
                                                             xDMFReader1_Display, Input_data['Variable_properties']['Color_map'])
    renderView1 = set_Opacity(Input_data['Variable_properties']['Variable_name'], 
                              Input_data['Variable_properties']['Opacity']['Function_type'], 
                              Input_data['Variable_properties']['Opacity']['Value'], renderView1, xDMFReader1, Var_LUT)
    renderView1.Update()
    renderView1.ResetCamera()
    print('Screenshot')
    SaveScreenshot('image.png',renderView1) 
    return None
    #---------------------Input Error Handling-----------------------                                              
    # Need to ensure that the variables being checked for are not null - return error message                      
    # Representation                                                                                               
    #if Input_data['Variable_properties']['Representation'] is None:
     #   sys.exit("No representation was specified")
    #if Input_data['Variable_properties']['Color_map'] is None:
     #   print("Using default color map")
     #   color_map = 'Viridis (matplotlib)'
    #if Input_data['Filter']['Contour']['Contour_variable'] == var:
     #   sys.exit("Cannot color by and contour by same variable")
    # Opacity                                                                                                      
    # Function_type                                                                                                
    # Value                                                                                                        
    # Filter - check from Apply = true, string should be given                                                     

    

    #renderView1.Update()
    #renderView1.ResetCamera()
    #ColorBy(xDMFReader1_Display, ('POINTS', var))
    #xDMFReader1_Display.SetScalarBarVisibility(renderView1, True)
    #xDMFReader1, xDMFReader1_Display = ReadData_Xdmf(Input_data['file_path'])
    #setVariableDisplay(Input_data['Variable_properties'], xDMFReader1_Display)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
