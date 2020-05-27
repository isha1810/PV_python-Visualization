#!/usr/bin/env python

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

# import common functions 
from ReadWriteFunctions import *
from SetDisplayFunctions import *


def volume_render(scalar_var_source, render_view):
    material_library = GetMaterialLibrary()
    #not sure what this is ^
    merge_blocks = MergeBlocks(Input=scalar_var_source)
    #Do not merge points
    merge_blocks.MergePoints = 0
    merge_blocks_display = Show(merge_blocks, render_view)
    Hide(scalar_var_source, render_view)
    merge_blocks_display.SetRepresentationType('Volume')
    render_view.Update()
    return merge_blocks_display, render_view


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
    
    # Do volume render
    scalar_var_display, render_view = volume_render(scalar_var_source, render_view)
    
    scalar_var_display, render_view, variable_lookup_table=\
        set_color_map(scalar_variable, render_view, scalar_var_display,
                      input_file.pv_scalar_variable_properties.pv_color_map)
    

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

