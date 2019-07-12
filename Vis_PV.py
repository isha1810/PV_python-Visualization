#!/usr/bin/env python

# Distributed under the MIT License.
# See LICENSE.txt for details.

from paraview.simple import *
import sys
import yaml
import numpy as np
import math
import argparse
        

def parse_cmd_line():
    '''
    parse command-line arguments
    :return: dictionary of the command-line args, dashes are underscores
    '''
    parser = argparse.ArgumentParser(description='Visualization using Paraview',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--input-file', type=str, required=True,
                        help='provide path to yaml file containing visualization parameters')
    parser.add_argument('--save', type=str, required=True,
                        help='set to the name of output file you want written.\
                        For animations this saves an mp4 file and for stills, a png')
    return vars(parser.parse_args())


def set_default_camera(render_view):
    '''
    Set view and camera properties to a default 
    specified below
    '''
    render_view.AxesGrid = 'GridAxes3DActor'
    render_view.CenterOfRotation = [0.0, 0.0, -22.98529815673828]
    render_view.StereoType = 0
    render_view.CameraPosition = [-95.16305892510273, 754.3761479590994, 426.10491067642846]
    render_view.CameraFocalPoint = [43.11431452669897, 23.554652286151217, -46.78071794111179]
    render_view.CameraViewUp = [0.09790398117889891, -0.5275190119519493, 0.843882990999677]
    render_view.CameraParallelScale = 715.9367631158923
    render_view.Background = [0.0, 0.0, 0.0]
    return render_view


def load_input_file(input_file_name):
    '''
    Read data from yaml input file 
    Name/path of yaml file is specified in command line arguments
    '''
    Input_stream = open(input_file_name, 'r')
    Input_file = yaml.load(Input_stream)
    return Input_file


def read_xdmf(xdmf_file_path): 
    '''
    Read data from XDMF file specified in yaml file.
    '''
    try:
        xdmf_reader = XDMFReader(FileNames=xdmf_file_path)
    except FileNotFoundError:
        sys.exit("No such file at file location specified: " + xdmf_file_path)
    xdmf_reader = GetActiveSource()
    render_view = GetActiveViewOrCreate('RenderView')
    xdmf_reader_display = GetDisplayProperties(xdmf_reader, view=render_view)
    return render_view, xdmf_reader, xdmf_reader_display

def set_representation(representation, render_view, xdmf_reader_display):
    '''
    Set representation, for example, 'Surface' or 'Wireframe', 
    and update view 
    '''
    print("update display in representation function")
    xdmf_reader_display.Representation = representation
    render_view.Update()
    return render_view, xdmf_reader_display


def set_color_map(var, render_view, xdmf_reader_display, color_map):
    '''
    Set the color map to one of preset ParaView color maps.
    If color map entered is invalid, color map is set to 
    default.
    '''
    print("update display in color map function")
    ColorBy(xdmf_reader_display, ('POINTS', var))
    # ParaView returns a lookup table (LUT):
    variable_lookup_table = GetColorTransferFunction(var)
    variable_lookup_table.ApplyPreset(color_map, True)
    # Show the color bar for the variable being visualized:
    xdmf_reader_display.SetScalarBarVisibility(render_view, True)
    xdmf_reader_display.SetScaleArray = ['POINTS', var]
    xdmf_reader_display.ScaleTransferFunction = 'PiecewiseFunction'
    return xdmf_reader_display, render_view, variable_lookup_table 


def tetrahedralize(xdmf_reader, render_view):
    '''
    Apply tetrahedralize filter and update view
    '''
    tetrahedralize1 = Tetrahedralize(Input=xdmf_reader)
    Hide(xdmf_reader, render_view)
    xdmf_reader_display = Show(tetrahedralize1, render_view)
    render_view.Update()
    return render_view, xdmf_reader_display


def set_opacity(var, function_type, opacity_val, render_view, xdmf_reader, var_lut):#change this function
    '''
    Set opacity based on option chosen in yaml input file:
    'Constant': some value between 0 and 1
    'Proportional': opacity set proportional to the variable being visualized,
    (Under 'Variable_name' in 'Variable_properties')
    '''
    print("update display in opacity function")
    if function_type!='Constant' and function_type!='Proportional':
        sys.exit("The Opacity option specified in the input file is invalid. Enter either 'Constant' or 'Proportional' for the function type")
    # Get range of var array
    var_range = xdmf_reader.PointData.GetArray(var).GetRange()
    # Set variables to construct gaussians
    var_max = var_range[1]
    var_min = var_range[0]

    if function_type == 'Constant': #Constant Opacity
        var_lut.EnableOpacityMapping = 1
        Var_PWF = GetOpacityTransferFunction(var)
        Var_PWF.Points = [var_min, opacity_val, 0.5, 0.0, var_max , opacity_val, 0.5, 0.0]

    elif function_type == 'Proportional': #Varying opacity
        var_lut.EnableOpacityMapping = 1
        Var_PWF = GetOpacityTransferFunction(var)
        num_points = 200 #Number of points to evaluate opacity function
        num_gauss = 5 #Number of points to evaluate gaussians
        var_values = np.asarray(np.linspace(var_min, var_max, num_points)) #Array of var values
        center_values = np.asarray(np.linspace(var_min, var_max, num_gauss)) #centersof gaussian
        amplitude_values = abs(center_values)/max(abs(var_max), abs(var_min)) #amplitudes of gaussians
        sigma = (var_values[1] - var_values[0])*2 

        gaussians = []
        gaussians = [np.asarray([center_values[i], amplitude_values[i]]) for i in range(num_gauss)]
        opacity_function = np.zeros(len(var_values))
        for gaussian in gaussians:
            opacity_function += gaussian[1] * np.exp(-1 * np.square(var_values - gaussian[0])/(2*math.pow(sigma,2)))
        #Create opacity list with var_values, opacity function and 0.0, 0.5
        opacity_list = []
        for point in range(num_points):
            opacity_list += [var_values[point],opacity_function[point], 0.5, 0.0]
        Var_PWF.Points = opacity_list
    render_view.Update()
    return render_view


def apply_clip(clip_properties, var, render_view, filter1):
    '''
    Add
    '''
    clip1 = Clip(Input=filter1)
    if clip_properties['Clip_type'] == 'Plane':
        clip1.ClipType = 'Plane'
        clip1.Scalars = ['POINTS', var]
        clip1.ClipType.Origin = clip_properties['Origin']
        clip1.ClipType.Normal = clip_properties['Normal']
    elif clip_properties['Clip_type'] == 'Box':
        clip1.ClipType = 'Box'
        clip1.Scalars = ['POINTS', var]
        clip1.ClipType.Position = clip_properties['Position']
        clip1.ClipType.Rotation = clip_properties['Rotation']
        clip1.ClipType.Scale = clip_properties['Scale']
    elif clip_properties['Clip_type'] == 'Sphere':
        clip1.ClipType = 'Sphere'
        clip1.Scalars = ['POINTS', var]
        clip1.ClipType.Center = clip_properties['Center_s']
        clip1.ClipType.Radius = clip_properties['Radius_s']
    elif clip_properties['Clip_type'] == 'Cylinder':
        clip1.ClipType = 'Cylinder'
        clip1.Scalars = ['POINTS', var]
        clip1.ClipType.Center = clip_properties['Center_c']
        clip1.ClipType.Radius = clip_properties['Radius_c']
        clip1.ClipType.Axis = clip_properties['Axis']
    #Hide previous data display before filter
    Hide(filter1, render_view)
    xdmf_reader_display = Show(clip1,render_view)
    return render_view, clip1, xdmf_reader_display


def apply_slice(slice_properties, var, render_view, filter1):
    '''
    Add
    '''
    slice1 = Slice(Input=filter1)
    if slice_properties['Slice_type'] == 'Plane':
        slice1.SliceType = 'Plane'
        slice1.SliceOffsetValues = [0.0]
        slice1.SliceType.Origin= slice_properties['Origin']
        slice1.SliceType.Normal= slice_properties['Normal']
    elif slice_properties['Slice_type'] == 'Box':
        slice1.SliceType = 'Box'
        slice1.SliceOffsetValues = [0.0]
        slice1.SliceType.Position= slice_properties['Position']
        slice1.SliceType.Rotation= slice_properties['Rotation']
        slice1.SliceType.Scale= slice_properties['Scale']
    elif slice_properties['Slice_type'] == 'Sphere':
        slice1.SliceType = 'Sphere'
        slice1.SliceOffsetValues = [0.0]
        slice1.SliceType.Center = slice_properties['Center_s']
        slice1.SliceType.Radius = slice_properties['Radius_s']
    elif slice_properties['Slice_type'] == 'Cylinder':
        slice1.SliceType = 'Cylinder'
        slice1.SliceOffsetValues = [0.0]
        slice1.SliceType.Center = slice_properties['Center_c']
        slice1.SliceType.Radius = slice_properties['Radius_c']
        slice1.SliceType.Axis = slice_properties['Axis']
    #Hide previous data display before filter
    Hide(filter1, render_view)
    xdmf_reader_display = Show(slice1,render_view)
    return render_view, slice1, xdmf_reader_display


def apply_warp(var, xdmf_reader, render_view):
    '''
    Add
    '''
    slice1 = Slice(Input=xdmf_reader)
    slice1.SliceType = 'Plane'
    slice1.SliceOffsetValues = [0.0]
    slice1.SliceType.Origin = [np.pi, np.pi, np.pi]
    slice1.SliceType.Normal = [0.0, 0.0, 1.0]
    warp_by_scalar = WarpByScalar(Input=slice1)
    warp_by_scalar.Scalars = ['POINTS', var]
    Hide(xdmf_reader, render_view)
    xdmf_reader_display = Show(warp_by_scalar, render_view)
    return render_view


def save_images(render_view, xdmf_reader, save):
    '''
    Saves single image or multiple images based on number of 
    time steps in data. One image per time step saved
    '''
    print("save ims in function")
    time_steps = xdmf_reader.TimestepValues #list of timesteps
    print(time_steps)
    print(type(time_steps))
    render_view.ViewSize = [1920, 1080]
    if type(time_steps) is paraview.servermanager.VectorProperty:
        number_of_time_steps = len(time_steps)
    else:
        number_of_time_steps = 1
        time_steps = [time_steps]

    if number_of_time_steps == 1:
        SaveScreenshot(save +'.png', render_view)
    elif number_of_time_steps > 1:
        anim = GetAnimationScene()
        anim.PlayMode = 'Snap To TimeSteps'
        for time_step_index in range(number_of_time_steps):
            print('Rendering time step',time_step_index)
            anim.AnimationTime = time_steps[time_step_index]
            current_view = GetRenderView()
            SaveScreenshot(save +'_'+ str(time_step_index) +'.png', current_view)
    return None


def main(args):
    '''
    :param args: command line arguments
    Render image(s) based on parameters specified 
    '''

    # Disable automatic camera reset on 'Show'
    paraview.simple._DisableFirstRenderCameraReset()
    print("get data set camera defaults")
    # Get data from file, set default camera properties
    input_file = load_input_file(args["input_file"])
    render_view, xdmf_reader, xdmf_reader_display = read_xdmf(input_file['file_path'])
    set_default_camera(render_view)
    # variable name to 'variable_to_render'
    variable_to_render = input_file['Variable_properties']['Variable_name']
    print("apply filters")
    # Apply filters
    filter1 = GetActiveSource()

    if input_file['Filter']['Clip']['Clip_type'] == input_file['Filter']['Slice']['Slice_type']:
        sys.exit('Clip type and Slice type chosen cannot be applied simulatneously')
    else:
        if input_file['Filter']['Clip']['Apply']:
            render_view, filter1, xdmf_reader_display = apply_clip(input_file['Filter']['Clip'],
                                                                   variable_to_render, render_view, filter1)
        elif input_file['Filter']['Slice']['Apply']:
            render_view, filter1, xdmf_reader_display = apply_slice(input_file['Filter']['Slice'],
                                                                    variable_to_render, render_view, filter1)
    # Update outside of apply_clip and apply_slice so that both a clip and a slice could be done simultaneously in the future
    render_view.Update()
    print("update display")
    # Update Display
    #render_view, xdmf_reader_display = tetrahedralize(xdmf_reader, render_view)
    render_view, xdmf_reader_display = set_representation(input_file['Variable_properties']['Representation'], render_view,
                                                          xdmf_reader_display)
    xdmf_reader_display, render_view, variable_lookup_table = set_color_map(variable_to_render, render_view, xdmf_reader_display, 
                                                             input_file['Variable_properties']['Color_map'])
    render_view = set_opacity(variable_to_render, input_file['Variable_properties']['Opacity']['Function_type'], 
                              input_file['Variable_properties']['Opacity']['Value'], render_view, xdmf_reader, variable_lookup_table)

    if input_file['Warp']['Add_warp']:
        renderView1 = apply_warp(variable_lookup_table, xdmf_reader, render_view)
    render_view.Update()
    render_view.ResetCamera()
    print("save ims")
    # Save images
    save_images(render_view, xdmf_reader, args["save"])

    return None


if __name__ == "__main__":
    try:
        main(parse_cmd_line())
    except KeyboardInterrupt:
        pass
