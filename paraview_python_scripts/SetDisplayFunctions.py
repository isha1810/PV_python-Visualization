#!/usr/bin/env python

# Distributed under the MIT License.
# See LICENSE.txt for details.

from paraview.simple import *
import sys
import yaml
import numpy as np

# First few functions modify display properties

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


def set_representation(representation, display):
    '''
    Set representation, for example, 'Surface' or 'Wireframe'
    and update view 
    '''
    display.Representation = representation
    #render_view.Update()
    print("Changed representation, update view")
    return display
    

def add_vector_field(vector_variable, vector_var_source, render_view):
    '''
    Adds a vector field (glyph) of variable specified in input file.
    '''
    vector_field = Glyph(Input=vector_var_source, GlyphType="Arrow")
    vector_field.OrientationArray = ['POINTS', vector_variable]
    vector_field.ScaleArray = ['POINTS', vector_variable]
    # Set shape, size of arrow (glyph)
    # Change ScaleFactor if arrows are not visible/too big
    vector_field.ScaleFactor = 10
    vector_field.GlyphType.TipResolution = 6
    vector_field.GlyphType.TipRadius = 0.2
    vector_field.GlyphType.TipLength = 0.3
    vector_field.GlyphType.ShaftResolution = 3
    vector_field.GlyphType.ShaftRadius = 0.05
    vector_field.GlyphMode = 'Uniform Spatial Distribution'
    vector_field.Seed = 10339
    vector_field.MaximumNumberOfSamplePoints = 100
    # Glyph display
    vector_var_display = Show(vector_field, render_view)
    return render_view, vector_var_display


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
        #Just added ********
        var_lookup_table.RescaleTransferFunction(var_min, var_max)
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
        sigma = (var_values[1] - var_values[0]) * 10.0

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
        #Just added ******************
        var_lookup_table.RescaleTransferFunction(var_min, var_max)
        var_pointwise_function.Points = opacity_list
        var_pointwise_function.RescaleTransferFunction(var_min, var_max)
    render_view.Update()
    return render_view

# Next few functions apply filters on the source

def tetrahedralize(scalar_var_source, render_view):
    '''
    Apply tetrahedralize filter and update view 
    '''
    tetrahedralize = Tetrahedralize(Input=scalar_var_source)
    Hide(scalar_var_source, render_view)
    scalar_var_display = Show(tetrahedralize, render_view)
    return scalar_var_display


def apply_clip(clip_properties, var, render_view, var_source):
    '''
    Apply the clip filter based on clip type chosen in Input file
    '''
    pv_clip = Clip(Input=var_source)
    if clip_properties.pv_type == 'Plane':
        pv_clip.ClipType = 'Plane'
        pv_clip.Scalars = ['POINTS', var]
        pv_clip.ClipType.Origin = clip_properties.pv_origin
        pv_clip.ClipType.Normal = clip_properties.pv_normal
    elif clip_properties.pv_type == 'Box':
        pv_clip.ClipType = 'Box'
        pv_clip.Scalars = ['POINTS', var]
        pv_clip.ClipType.Position = clip_properties.pv_position
        pv_clip.ClipType.Rotation = clip_properties.pv_rotation
        pv_clip.ClipType.Scale = clip_properties.pv_scale
    elif clip_properties.pv_type == 'Sphere':
        pv_clip.ClipType = 'Sphere'
        pv_clip.Scalars = ['POINTS', var]
        pv_clip.ClipType.Center = clip_properties.pv_sphere_center
        pv_clip.ClipType.Radius = clip_properties.pv_sphere_radius
    elif clip_properties.pv_type == 'Cylinder':
        pv_clip.ClipType = 'Cylinder'
        pv_clip.Scalars = ['POINTS', var]
        pv_clip.ClipType.Center = clip_properties.pv_cylinder_center
        pv_clip.ClipType.Radius = clip_properties.pv_cylinder_radiu
        pv_clip.ClipType.Axis = clip_properties.pv_axis
    # Hide previous data display before filter
    Hide(var_source, render_view)
    display = Show(pv_clip, render_view)
    return render_view, pv_clip, display


def apply_slice(slice_properties, var, render_view, var_source):
    '''
    Apply slice filter based on slice type chosen in Input file
    '''
    slice_pv = Slice(Input=var_source)
    if slice_properties.pv_type == 'Plane':
        slice_pv.SliceType = 'Plane'
        slice_pv.SliceOffsetValues = [0.0]
        slice_pv.SliceType.Origin = slice_properties.pv_origin
        slice_pv.SliceType.Normal = slice_properties.pv_normal
    elif slice_properties.pv_type == 'Box':
        slice_pvSliceType = 'Box'
        slice_pv.SliceType.Position = slice_properties.pv_position
        slice_pv.SliceType.Rotation = slice_properties.pv_rotation
        slice_pv.SliceType.Scale = slice_properties.pv_scale
    elif slice_properties.pv_type == 'Sphere':
        slice_pv.SliceType = 'Sphere'
        slice_pv.SliceOffsetValues = [0.0]
        slice_pv.SliceType.Center = slice_properties.pv_sphere_center
        slice_pv.SliceType.Radius = slice_properties.pv_sphere_radius
    elif slice_properties.pv_type == 'Cylinder':
        slice_pv.SliceType = 'Cylinder'
        slice_pv.SliceOffsetValues = [0.0]
        slice_pv.SliceType.Center = slice_properties.pv_cylinder_center
        slice_pv.SliceType.Radius = slice_properties.pv_cylinder_radius
        slice_pv.SliceType.Axis = slice_properties.pv_axis
    # Hide previous data display before filter
    Hide(var_source, render_view)
    display = Show(slice_pv, render_view)
    return render_view, slice_pv, display

def volume_render(scalar_var_source, render_view):
    '''
    
    '''
    material_library = GetMaterialLibrary()
    # not sure what this is for ^
    merge_blocks = MergeBlocks(Input=scalar_var_source)
    # Do not merge points
    merge_blocks.MergePoints = 0
    merge_blocks_display = Show(merge_blocks, render_view)
    merge_blocks_display.SetRepresentationType('Volume')
    return merge_blocks_display


# Functions used for warp
def create_neg_scalar_var(scalar_var, var_source):
    '''
    Create a negative scalar array for downward warp
    '''
    calculator = Calculator(Input=var_source)
    negative_scalar_var = 'negative_'+ scalar_var #setting name of new variable array
    calculator.ResultArrayName = negative_scalar_var
    calculator.Function = '-1*abs('+ scalar_var+')'
    return negative_scalar_var, calculator


def create_log_scalar_var(scalar_var, var_source):
    '''
    Create a log scalar array to warp for large ranges of scalar var values
    '''
    calculator = Calculator(Input=var_source)
    negative_log_scalar_var = 'negative_log_'+scalar_var
    calculator.ResultArrayName = negative_log_scalar_var
    calculator.Function = '-1*abs(log10('+scalar_var+'))'
    return negative_log_scalar_var, calculator
    

def add_scalar_warp(scalar_var, var_source, scale_type, scale_factor,
                    render_view):
    '''
    Create a surface warp.
    Warps by variable being visualized
    '''
    if scale_type == 'Linear':
        scaling_scalar_var, calculator = create_neg_scalar_var(scalar_var,
                                                           var_source)
    elif scale_type == 'Log':
        scaling_scalar_var, calculator = create_log_scalar_var(scalar_var,
                                                               var_source)
    tetrahedralize = Tetrahedralize(Input=calculator)
    slice_pv = Slice(Input=tetrahedralize)
    slice_pv.SliceType = 'Plane'
    slice_pv.SliceOffsetValues = [0.0]
    slice_pv.SliceType.Origin = [3.14, 3.14, 3.14]
    slice_pv.SliceType.Normal = [0.0, 0.0, 1.0]
    # Warp slice
    warp_by_scalar = WarpByScalar(Input=slice_pv)
    warp_by_scalar.Scalars = ['POINTS', scaling_scalar_var]
    warp_by_scalar.ScaleFactor = scale_factor
    warp_by_scalar.UseNormal = 1
    warp_by_scalar_display = GetDisplayProperties(warp_by_scalar, render_view)
    return render_view, warp_by_scalar_display


def add_vector_warp(vector_var, scalar_var, var_source, scale_type,
                    scale_factor, render_view):
    '''
    Add vector warp to show vector field along with scalar warp
    '''
    # First construct negative var array
    # for downward warp
    if scale_type == 'Linear':
        scaling_scalar_var, calculator = create_neg_scalar_var(scalar_var,
                                                               var_source)
    elif scale_type == 'Log':
        scaling_scalar_var, calculator = create_log_scalar_var(scalar_var,
                                                               var_source)
    slice_pv = Slice(Input=calculator)
    slice_pv.SliceType = 'Plane'
    slice_pv.SliceOffsetValues = [0.0]
    slice_pv.SliceType.Origin = [0, 0, 0]
    slice_pv.SliceType.Normal = [0.0, 0.0, 1.0]
    # Get vector field on slice
    vectors_slice = Glyph(Input=slice_pv, GlyphType='2D Glyph')
    vectors_slice.OrientationArray = ['POINTS', vector_var]
    vectors_slice.ScaleArray = ['POINTS', 'SpatialVelocity']
    vectors_slice.ScaleFactor = scale_factor
    vectors_slice.MaximumNumberOfSamplePoints = 100
    vectors_slice_display = GetDisplayProperties(vectors_slice,view=render_view)
    vectors_slice_display.LineWidth = 3.0
    Hide(vectors_slice, render_view)
    # Warp slice
    warp_by_scalar = WarpByScalar(Input=vectors_slice)
    warp_by_scalar.Scalars = ['POINTS', scaling_scalar_var]
    warp_by_scalar.ScaleFactor = 10
    warp_by_scalar.UseNormal = 1
    warp_by_scalar_display = GetDisplayProperties(warp_by_scalar, view=render_view)
    ColorBy(warp_by_scalar_display, ('POINTS', vector_var, 'Magnitude'))
    return render_view


     
