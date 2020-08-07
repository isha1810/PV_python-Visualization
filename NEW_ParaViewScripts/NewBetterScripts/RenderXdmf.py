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
    vector_variable = input_file.pv_vector_variable_properties.pv_variable_name
    render_view = CreateRenderView()
    xdmf_reader = get_xdmf_reader(input_file.pv_file_path)

    # Tetrahedralize
    display=tetrahedralize(xdmf_reader, render_view)

    # Update display properties
    display=set_representation(
        input_file.pv_scalar_variable_properties.pv_representation,
        display)
    display, render_view, variable_lookup_table=\
    set_color_map(scalar_variable, render_view, display,
                  input_file.pv_scalar_variable_properties.pv_color_map)
    render_view=\
    set_opacity(scalar_variable,
        input_file.pv_scalar_variable_properties.pv_opacity.pv_function_type,
        input_file.pv_scalar_variable_properties.pv_opacity.pv_value,
        render_view, xdmf_reader, variable_lookup_table)

    # Add a vector field (glyphs in ParaView) if specified in
    # input file
    if input_file.pv_vector_variable_properties.pv_add_vector_field:
        render_view, vector_field_display =\
        add_vector_field(vector_variable, xdmf_reader, render_view)
        # Update vector field display
        render_view = set_vector_field_color_map(vector_field_display,
                            vector_variable,
                            input_file.pv_vector_variable_properties.pv_color_map,
                            render_view)

    # Update the view
    render_view.Update()

    # Keep this for now until Camera properties added 
    # to input file
    render_view.ResetCamera()

    # Save images
    save_images(render_view, xdmf_reader, args["save"], 
                input_file.pv_save_properties.pv_image_resolution)
    
    return None


if __name__ == "__main__":
    try:
        main(parse_cmd_line())
    except KeyboardInterrupt:
        pass
