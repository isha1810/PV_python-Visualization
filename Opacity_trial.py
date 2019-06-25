#Read from file and set variables
import yaml
import numpy as np
import math
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from paraview.simple import *
if __name__ == '__main__':

    stream = open("InputVis_PV.yaml", 'r')
    Input_data = yaml.load(stream)
var = 'Psi'
xDMFReader1 = XDMFReader(FileNames=[Input_data['file_path']])
xDMFReader1 = GetActiveSource()
renderView1 = GetActiveViewOrCreate('RenderView')
var_range = xDMFReader1.PointData.GetArray(var).GetRange()

opacity = []

N_points = 10
#Also set opacity to 0 by appending opacity at min and max
# Try Opacity using Gaussians at different points: Start with 50
max = var_range[0]
min = var_range[1]  

x_range = np.linspace(min, max, N_points*10)
x_range_array = np.asarray(x_range) #domain of values 

x_0_list = x_range[min:max:10]
x_0_array = np.asarray(x_0_list) #points being used to construct the gaussians
                                                                      
sigma = x_range[1] - x_range[0] #width                                                                                                               

opacity = []
for i in range(len(x_range_array)):
    if x_range_array[i] in x_0_array:
        x_vals = np.linspace(x_range_array[i]-(2*sigma), x_range_array[i]+(2*sigma), 5)
        for x in x_vals:
            gauss = math.exp(-1*math.pow(x-x_range_array[i], 2)/(2*math.pow(sigma,2)))
            opacity.append(abs(x_range_array[i]*gauss / max))
    elif x_range_array[i] not in x_0_array and len(opacity)== i-1:
        opacity.append(0)
opacity.append(0)

print(len(x_range))
print(len(opacity))

plt.plot(x_range, opacity)
plt.savefig("opacityplot.png")
        
        
