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
    render_view = CreateRenderView()
    set_default_camera(render_view)

    # Do volume render
    display = volume_render(xdmf_reader, render_view)
    
    # Set color map
    display, render_view, variable_lookup_table=\
        set_color_map(scalar_variable, render_view, display,
                      input_file.pv_scalar_variable_properties.pv_color_map)
    
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

