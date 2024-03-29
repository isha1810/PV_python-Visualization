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
    paraview.simple._DisableFirstRenderCameraReset()
    input_file = load_input_file(args["input_file"])
    scalar_variable = input_file.pv_scalar_variable_properties.pv_variable_name

    render_view1 = CreateRenderView()
    layout1 = GetLayout()
    render_view2 = CreateRenderView()
    set_default_camera(render_view1)
    set_default_camera(render_view2)
    # Assign views to Layout
    layout1.AssignView(1, render_view1)
    layout1.AssignView(2, render_view2)

    xdmf_reader = get_xdmf_reader(input_file.pv_file_path)
    
    # Images to render in first view
    SetActiveView(render_view1)
    display=tetrahedralize(xdmf_reader, render_view1)
    display=set_representation(
        input_file.pv_scalar_variable_properties.pv_representation,
        display)
    display, render_view, variable_lookup_table=\
        set_color_map(scalar_variable, render_view1, display,
                      input_file.pv_scalar_variable_properties.pv_color_map)
    render_view=\
    set_opacity(scalar_variable,
    input_file.pv_scalar_variable_properties.pv_opacity.pv_function_type,
            input_file.pv_scalar_variable_properties.pv_opacity.pv_value,
            render_view1, xdmf_reader, variable_lookup_table)
    render_view1.Update()
    render_view1.ResetCamera()

    #layout1 = GetLayout()
    #render_view2 = CreateRenderView()
    #set_default_camera(render_view2)
    # Images to render in second view
    SetActiveView(render_view2)
    # Assign views to Layout
    #layout1.AssignView(2, render_view2)
    #layout1.AssignView(1, render_view1)

    SaveScreenshot("new_image.png", layout1, SaveAllViews=1)

    # Save images
    #save_images(render_view, xdmf_reader, args["save"])
    
    return None


if __name__ == "__main__":
    try:
        main(parse_cmd_line())
    except KeyboardInterrupt:
        pass
