# !/usr/bin/env python

# Distributed under the MIT License.
# See LICENSE.txt for details.

from paraview.simple import *
import sys
import yaml
import numpy as np
import math
import argparse
# input file class
from InputFile import InputFile

#import common functions
from ReadWriteFunctions import *
from SetDisplayFunctions import *


def apply_clip(clip_properties, var, render_view, var_source):
    '''
    Apply the clip filter based on clip type chosen in Input file
    '''
    clip = Clip(Input=var_source)
    if clip_properties.pv_type == 'Plane':
        clip.ClipType = 'Plane'
        clip.Scalars = ['POINTS', var]
        clip.ClipType.Origin = clip_properties.pv_origin
        clip.ClipType.Normal = clip_properties.pv_normal
    elif clip_properties.pv_type == 'Box':
        clip.ClipType = 'Box'
        clip.Scalars = ['POINTS', var]
        clip.ClipType.Position = clip_properties.pv_position
        clip.ClipType.Rotation = clip_properties.pv_rotation
        clip.ClipType.Scale = clip_properties.pv_scale
    elif clip_properties.pv_type == 'Sphere':
        clip.ClipType = 'Sphere'
        clip.Scalars = ['POINTS', var]
        clip.ClipType.Center = clip_properties.pv_sphere_center
        clip.ClipType.Radius = clip_properties.pv_sphere_radius
    elif clip_properties.pv_type == 'Cylinder':
        clip.ClipType = 'Cylinder'
        clip.Scalars = ['POINTS', var]
        clip.ClipType.Center = clip_properties.pv_cylinder_center
        clip.ClipType.Radius = clip_properties.pv_cylinder_radius
        clip.ClipType.Axis = clip_properties.pv_axis
    # Hide previous data display before filter
    Hide(var_source, render_view)
    display = Show(clip, render_view)
    return render_view, clip, display


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


def main(args):
    '''
    :param args: command line arguments
    Render image(s) based on parameters specified
    '''
    
    # Disable automatic camera reset on 'Show'
    paraview.simple._DisableFirstRenderCameraReset()
    # Get data from file, set default camera properties
    input_file = load_input_file(args["input_file"])
    render_view, xdmf_reader, xdmf_reader_display = read_xdmf(
        input_file.pv_file_path)
    set_default_camera(render_view)
    
    # Set scalar and vector variables from input files
    # Create different source objects for scalar and vector rendering
    scalar_variable = input_file.pv_scalar_variable_properties.pv_variable_name
    vector_variable = input_file.pv_vector_variable_properties.pv_variable_name
    scalar_var_source = GetActiveSource()
    vector_var_source = GetActiveSource()
     
    # For vector variable properties:
    # Add vector field (glyphs on ParaView):
    if input_file.pv_vector_variable_properties.pv_add_vector_field:
        render_view, vector_var_display, vector_var_source =\
        add_vector_field(vector_variable, vector_var_source, render_view)
    
    #Apply filters 
    if input_file.pv_filters.pv_clip.pv_apply:
        render_view, scalar_var_filter, scalar_var_display=\
        apply_clip(input_file.pv_filters.pv_clip,
                   scalar_variable, render_view, scalar_var_source)
        if input_file.pv_vector_variable_properties.pv_add_vector_field:
            render_view, vector_var_filter, vector_var_display=\
            apply_clip(input_file.pv_filters.pv_clip,
                       vector_variable, render_view, vector_var_source)
    elif input_file.pv_filters.pv_slice.pv_apply:
        render_view, scalar_var_filter, scalar_var_display=\
        apply_slice(input_file.pv_filters.pv_slice,
                    scalar_variable, render_view, scalar_var_source)
        if input_file.pv_vector_variable_properties.pv_add_vector_field:
            render_view, vector_var_filter, vector_var_display=\
            apply_slice(input_file.pv_filters.pv_slice,
                        vector_variable, render_view, vector_var_source)
    render_view.Update()

    # Update Display for scalar var
    #render_view, scalar_var_display=tetrahedralize(scalar_var_source,
    #                                               render_view)

    render_view,scalar_var_display=set_representation(
        input_file.pv_scalar_variable_properties.pv_representation,render_view,
        scalar_var_display)
    scalar_var_display, render_view, variable_lookup_table=\
    set_color_map(scalar_variable, render_view, scalar_var_display,
                  input_file.pv_scalar_variable_properties.pv_color_map)


    render_view=\
    set_opacity(scalar_variable,
        input_file.pv_scalar_variable_properties.pv_opacity.pv_function_type,
        input_file.pv_scalar_variable_properties.pv_opacity.pv_value,
        render_view, scalar_var_source, variable_lookup_table)

    # Update Display for vector var:
    # Set color_map for vector field
    if input_file.pv_vector_variable_properties.pv_add_vector_field:
        render_view = set_vector_color_map(vector_var_display, vector_variable,
                        input_file.pv_vector_variable_properties.pv_color_map,
                        render_view)

    render_view.ResetCamera()
    # Save images
    save_images(render_view, xdmf_reader, args["save"])
    
    return None


if __name__ == "__main__":
    try:
        main(parse_cmd_line())
    except KeyboardInterrupt:
        pass
