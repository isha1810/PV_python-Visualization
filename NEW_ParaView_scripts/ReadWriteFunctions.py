#!/usr/bin/env python

# Distributed under the MIT License.
# See LICENSE.txt for details.

from paraview.simple import *
import argparse
import sys
import yaml
import numpy as np
# input file class
from InputFile import InputFile


def parse_cmd_line():
    '''
    parse command-line arguments
    :return: dictionary of the command-line args, dashes are underscores
    '''
    parser = argparse.ArgumentParser(description='Visualization using Paraview',
                                     formatter_class=\
                                     argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--input-file', type=str, required=True,
                        help="provide path to"
                        "yaml file containing visualization parameters")
    parser.add_argument('--save', type=str, required=True,
                        help="set to the name of output file to be written."
                        "For animations this saves a png file at each timestep"
                        "and for stills, a png")
    return vars(parser.parse_args())
    

def load_input_file(input_file_name):
    '''
    Read data from yaml input file
    Name/path of yaml file is specified in command line arguments
    '''
    # Check yaml file existence:
    try:
        input_stream = open(input_file_name, 'r')
        print("reading data from input file")
    except FileNotFoundError:
        sys.exit("Input file was not found at location: " + input_file_name)
    # Try for error in Yaml formatting
    # If an error is found, the mark is returned and printed
    try:
        input_dictionary = yaml.load(input_stream)
    except yaml.YAMLError, exc:
        print("The input file cannot be parsed because of a syntax error.")
        if hasattr(exc, 'problem_mark'):
            mark = exc.problem_mark
            sys.exit("The syntax error was encountered at row %s column %s"
                      % (mark.line + 1, mark.column + 1))
    # Create instance of InputFile class and load data
    input_file = InputFile(input_dictionary)
    return input_file


def read_xdmf(xdmf_file_path):
    '''
    Read data from XDMF file specified in yaml file.
    Set source and view variables.
    '''
    try:
        xdmf_reader = XDMFReader(FileNames=xdmf_file_path)
    except FileNotFoundError:
        sys.exit("No such file at file location specified: " + xdmf_file_path)
    xdmf_reader = GetActiveSource()
    render_view = GetActiveViewOrCreate('RenderView')
    xdmf_reader_display = GetDisplayProperties(xdmf_reader, view=render_view)
    return render_view, xdmf_reader, xdmf_reader_display


def save_images(render_view, xdmf_reader, save):
    '''
    Saves single image or multiple images based on number of
    time steps in data. One image is saved per time step.
    '''
    time_steps = xdmf_reader.TimestepValues  # list of timesteps
    render_view.ViewSize = [1920, 1080]
    #Check if there a multiple timesteps
    #VectorProperty below is a paraview type vector object 
    if type(time_steps) is paraview.servermanager.VectorProperty:
        number_of_time_steps = len(time_steps)
    else:
        number_of_time_steps = 1
        time_steps = [time_steps]
    
    if number_of_time_steps == 1:
        SaveScreenshot(save + '.png', render_view)
    elif number_of_time_steps > 1:
        anim = GetAnimationScene()
        anim.PlayMode = 'Snap To TimeSteps'
        for time_step_index in range(number_of_time_steps):
            print('Rendering time step', time_step_index)
            anim.AnimationTime = time_steps[time_step_index]
            current_view = GetRenderView()
            #Add time step value to window
            display_time(xdmf_reader, current_view)
            #Generating 6-digit index for image name for ex 000001 instead of 1
            time_step_index_str = str(time_step_index)
            time_step_index_str =\
                    (6-len(time_step_index_str))*"0" + time_step_index_str
            SaveScreenshot(save + '_' + time_step_index_str +
                           '.png', current_view)
    return None


def display_time(xdmf_reader, render_view):
    '''
    Prints current time to images rendered in save_images
    '''
    annotate_time = AnnotateTimeFilter(xdmf_reader)
    annotate_time.Format = 'Time: %f s'
    annotate_time_display = Show(annotate_time, render_view)
    annotate_time_display.WindowLocation = 'UpperCenter'
    annotate_time_display.FontFamily = 'Courier'
    annotate_time_display.FontSize = 13
    render_view.Update()
    return None


            

