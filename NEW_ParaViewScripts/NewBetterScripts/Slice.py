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
    return render_view, display


def main(args):
    '''
    :param args: command line arguments
    Render image(s) based on parameters specified
    '''
    
    # Disable automatic camera reset on 'Show'
    paraview.simple._DisableFirstRenderCameraReset()
    # Get data from file, set default camera properties
    
    input_file = load_input_file(args["input_file"])
    scalar_variable = input_file.pv_scalar_variable_properties.pv_variable_name
    xdmf_reader= get_xdmf_reader(input_file.pv_file_path)
    render_view = create_render_view()
    set_default_camera(render_view)
    #Apply filters 
    render_view, display=\
            apply_slice(input_file.pv_filters.pv_slice,
                        scalar_variable, render_view, xdmf_reader)

    # Update Display for scalar var
    #render_view, scalar_var_display=tetrahedralize(scalar_var_source,
    #                                               render_view)

    display=set_representation(
        input_file.pv_scalar_variable_properties.pv_representation,display)
    display, render_view, variable_lookup_table=\
    set_color_map(scalar_variable, render_view, display,
                  input_file.pv_scalar_variable_properties.pv_color_map)
    render_view=\
    set_opacity(scalar_variable,
        input_file.pv_scalar_variable_properties.pv_opacity.pv_function_type,
        input_file.pv_scalar_variable_properties.pv_opacity.pv_value,
        render_view, xdmf_reader, variable_lookup_table)

    # Update the view
    update_view(render_view)

    # Keep this for now until Camera properties added
    # to input file
    render_view.ResetCamera()

    # Save images
    save_images(render_view, xdmf_reader, args["save"])
    
    return None


if __name__ == "__main__":
    try:
        main(parse_cmd_line())
    except KeyboardInterrupt:
        pass
