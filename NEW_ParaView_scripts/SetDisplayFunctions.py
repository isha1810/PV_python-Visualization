#!/usr/bin/env python

# Distributed under the MIT License.
# See LICENSE.txt for details.

from paraview.simple import *
import sys
import yaml
import numpy as np



def set_default_camera(render_view):
    '''
    Set view and camera properties to a default
    specified below
    '''
    render_view.AxesGrid = 'GridAxes3DActor'
    render_view.CenterOfRotation = [0.0, 0.0, -22.98529815673828]
    render_view.StereoType = 0
    render_view.CameraPosition = [-95.16305892510273,
                                  754.3761479590994, 426.10491067642846]
    render_view.CameraFocalPoint = [
        43.11431452669897, 23.554652286151217, -46.78071794111179]
    render_view.CameraViewUp = [
        0.09790398117889891, -0.5275190119519493, 0.843882990999677]
    render_view.CameraParallelScale = 715.9367631158923
    render_view.Background = [0.0, 0.0, 0.0]
    return render_view


def set_representation(representation, render_view, display):
    '''
    Set representation, for example, 'Surface' or 'Wireframe'
    and update view 
    '''
    display.Representation = representation
    render_view.Update()
    print("Changed representation, update view")
    return render_view, display
    

def set_color_map(var, render_view, display, color_map):
    '''
    Set the color map to one of preset ParaView color maps
    '''
    ColorBy(display, ('POINTS', var))
    # ParaView returns a lookup table (LUT):
    variable_lookup_table = GetColorTransferFunction(var)
    variable_lookup_table.ApplyPreset(color_map, True)
    # Show the color bar for the variable being visualized:
    display.SetScalarBarVisibility(render_view, True)
    display.SetScaleArray = ['POINTS', var]
    display.ScaleTransferFunction = 'PiecewiseFunction'
    return display, render_view, variable_lookup_table


def set_vector_color_map(vector_var_display, vector_variable, color_map,
                         render_view):
    '''
    Sets color_map for vector field
    '''
    ColorBy(vector_var_display, ('POINTS', vector_variable, 'Magnitude'))
    var_lookup_table = GetColorTransferFunction(vector_variable)
    var_lookup_table.ApplyPreset(color_map,True)
    vector_var_display.SetScalarBarVisibility(render_view, True)
    vector_var_display.RescaleTransferFunctionToDataRange(True, False)
    render_view.Update()
    return render_view


def set_opacity(var, function_type, opacity_val, render_view,\
                scalar_var_source, var_lookup_table):
    '''
    Set opacity based on option chosen in yaml input file:
    'Constant': some value between 0 and 1 
    'Proportional': opacity set proportional to the variable being visualized,
    (Under 'Scalar_variable_properties')
    '''
    # Get range of var array
    var_range = scalar_var_source.PointData.GetArray(var).GetRange()
    # Set variables to construct gaussians
    var_max = var_range[1]
    var_min = var_range[0]
    
    if function_type == 'Constant':  # Constant Opacity
        var_lookup_table.EnableOpacityMapping = 1
        var_pointwise_function = GetOpacityTransferFunction(var)
        var_pointwise_function.Points = [var_min, opacity_val, 0.5,
                                         0.0, var_max, opacity_val, 0.5, 0.0]
        
    elif function_type == 'Proportional':  # Varying opacity
        var_lookup_table.EnableOpacityMapping = 1
        var_pointwise_function = GetOpacityTransferFunction(var)
        num_points = 200  # Number of points to evaluate opacity function 
        num_gauss = 5  # Number of gaussians
        var_values = np.asarray(np.linspace(
            var_min, var_max, num_points))  # Array of var values
        center_values = np.asarray(np.linspace(
            var_min, var_max, num_gauss))  # centers of gaussian
        # amplitudes of gaussians
        amplitude_values = abs(center_values)/max(abs(var_max), abs(var_min))
        sigma = (var_values[1] - var_values[0]) * 2.0

        gaussians = []
        gaussians = [np.asarray([center_values[i], amplitude_values[i]])
                     for i in range(num_gauss)]
        opacity_function = np.zeros(len(var_values))
        for gaussian in gaussians:
            opacity_function += gaussian[1] * np.exp(-1.0 * np.square(
                var_values - gaussian[0])/(2.0 * sigma**2))
        # Create opacity list with var_values, opacity function,
        # midpoint value, sharpness
        # Midpoint value used here is 0.5, sharpness value used is 0.0
        opacity_list = []
        for point in range(num_points):
            opacity_list += [var_values[point],
                             opacity_function[point], 0.5, 0.0]
        var_pointwise_function.Points = opacity_list
    render_view.Update()
    return render_view


def tetrahedralize(scalar_var_source, render_view):
    '''
    Apply tetrahedralize filter and update view 
    '''
    tetrahedralize = Tetrahedralize(Input=scalar_var_source)
    Hide(scalar_var_source, render_view)
    scalar_var_display = Show(tetrahedralize, render_view)
    render_view.Update()
    return render_view, scalar_var_display


