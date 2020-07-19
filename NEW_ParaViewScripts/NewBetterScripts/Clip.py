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
    xdmf_reader = get_xdmf_reader(input_file.pv_file_path)
    render_view = create_render_view()
    set_default_camera(render_view)
    
    #Apply filters 
    render_view, clip, display=\
        apply_clip(input_file.pv_filters.pv_clip,
                   scalar_variable, render_view, xdmf_reader)

    # Update Display for scalar var
    #display=tetrahedralize(clip, render_view)

    display=set_representation(
        input_file.pv_scalar_variable_properties.pv_representation, display)
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
