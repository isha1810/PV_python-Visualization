#!/usr/bin/env python

# Distributed under the MIT License.
# See LICENSE.txt for details.

from paraview.simple import *
import sys
import yaml
import numpy as np
import math
import argparse
import os
# input file class
from InputFile import InputFile

# import common functions
from ReadWriteFunctions import *
from SetDisplayFunctions import *


def create_neg_scalar_var(scalar_var, var_source):
    '''
    Create a negative scalar array for downward warp
    '''
    calculator = Calculator(Input=var_source)
    neg_scalar_var = 'negative_'+ scalar_var #setting name of new variable array
    calculator.ResultArrayName = neg_scalar_var
    calculator.Function = '-1*abs('+ scalar_var+')'
    return neg_scalar_var, calculator


def create_log_scalar_var(scalar_var, var_source):
    '''
    Create a log scalar array to warp for large ranges of scalar var values
    '''
    calculator = Calculator(Input=var_source)
    neg_log_scalar_var = 'negative_log_'+scalar_var
    calculator.ResultArrayName = neg_log_scalar_var
    calculator.Function = '-1*abs(log10('+scalar_var+'))'
    return neg_log_scalar_var, calculator


def translate_var(warp_by_scalar, var_source, render_view):
    '''
    Translate warp to a point below the
    object in view
    '''
    transform = Transform(Input=warp_by_scalar)
    transform.Transform = 'Transform'
    transform.Transform.Translate = [0.0, 0.0, -15.0]
    Hide(warp_by_scalar, render_view)
    return transform, render_view


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
    slice_pv = Slice(Input=calculator)
    slice_pv.SliceType = 'Plane'
    slice_pv.SliceOffsetValues = [0.0]
    slice_pv.SliceType.Origin = [3.14, 3.14, 3.14]
    slice_pv.SliceType.Normal = [0.0, 0.0, 1.0]
    # Warp slice
    warp_by_scalar = WarpByScalar(Input=slice_pv)
    warp_by_scalar.Scalars = ['POINTS', scaling_scalar_var]
    warp_by_scalar.ScaleFactor = scale_factor
    warp_by_scalar.UseNormal = 1
    # Translate the warp 
    #transform, render_view = translate_var(warp_by_scalar, var_source,
    #                                       render_view)
    # Color translated warp by scalar_var
    warp_by_scalar_display = GetDisplayProperties(warp_by_scalar, render_view)
    ColorBy(warp_by_scalar_display, ('POINTS', scalar_var))
    Show()
    render_view.Update()
    Hide(calculator, render_view)
    Hide(var_source, render_view)
    return render_view


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
    # Translate the warp
    transform, render_view = translate_var(warp_by_scalar, var_source,
                                           render_view)
    transform_display = Show(transform, render_view)
    Hide(warp_by_scalar, render_view)
    ColorBy(transform_display, ('POINTS', vector_var, 'Magnitude'))
    render_view.Update()
    return render_view


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
  
    Hide(xdmf_reader, render_view)
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
        
    # Update Display for scalar var
    render_view, scalar_var_display=tetrahedralize(scalar_var_source,
                                                   render_view)
    render_view,scalar_var_display=set_representation(
        input_file.pv_scalar_variable_properties.pv_representation,render_view,
        scalar_var_display)
    scalar_var_display, render_view, variable_lookup_table=\
    set_color_map(scalar_variable, render_view, scalar_var_display,
                  input_file.pv_scalar_variable_properties.pv_color_map)
    
    # Update Display for vector var:
    # Set color_map for vector field
    if input_file.pv_vector_variable_properties.pv_add_vector_field:
        render_view = set_vector_color_map(vector_var_display, vector_variable,
                    input_file.pv_vector_variable_properties.pv_color_map,
                    render_view)

    # For Warp
    if input_file.pv_warp.pv_add_warp:
        render_view = add_scalar_warp(
            scalar_variable, scalar_var_source, input_file.pv_warp.pv_scale_type,
            input_file.pv_warp.pv_scale_factor, render_view)
        if input_file.pv_vector_variable_properties.pv_add_vector_field:
            render_view = add_vector_warp(vector_variable, scalar_variable,
                vector_var_source, input_file.pv_warp.pv_scale_type,
                input_file.pv_warp.pv_scale_factor, render_view)

    Hide(scalar_var_source, render_view)
    render_view.ResetCamera()
    # Save images
    save_images(render_view, xdmf_reader, args["save"])
    
    return None
    
    
if __name__ == "__main__":
    try:
        main(parse_cmd_line())
    except KeyboardInterrupt:
        pass
    
