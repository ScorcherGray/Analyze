import sys
import array # Use array.array instead of list objects to hold data
import glob
import matplotlib.pyplot as plt
import numpy as np

def FindPulse(data, rawData, parameters):
    global datfiles
    print(datfiles[0])
    vt = int(parameters['vt'][0]) # Pulse parameters gained from .ini file at startup: (all are necessary, enforce these numbers)
    width = int(parameters['width'][0])
    pulse_delta = int(parameters['pulse_delta'][0])
    drop_ratio = float(parameters['drop_ratio'][0])
    below_drop_ratio = int(parameters['below_drop_ratio'][0])
    pulseStart = []
    areas = []
    peakloc = []
    move = False
    for i in range(len(data)-2):
        if move:
            if data[i+1] < data[i] and movepoint <= i + 2:#After finding a pulse, move forward through the data starting at yi+2 until the samples start to decrease before looking for the next pulse.
                move = False
        elif data[i+2] - data[i] > vt:# Detecting pulses: look for rise over three consecutive points -- y[i], y[i+1] and y[i+2]
            pulseStart.append(i)
            move = True
            movepoint = i
    for i in range(len(pulseStart)): # If a .dat file has no pulses, ignore it. If pulses: report start position and areas
        area = 0
        peak = 0
        if i == len(pulseStart)-1:
            limit = width
        elif width < pulseStart[i+1] - pulseStart[i]:# Area is merely the sum of the values starting at the pulse start and going for width samples(an input parameter 'width')
            limit = width
        else: # Or, until the start of the next pulse, whichever is first.
            limit = pulseStart[i+1] - pulseStart[i]
        for j in range(pulseStart[i], pulseStart[i]+limit): # Use original data to compute area, not the smoothed.
            area = area + rawData[j] 
            if rawData[j] > rawData[j-1]:
                peak = j
        peakloc.append(peak)
        areas.append(area)
    for i in range(len(pulseStart)):
        count = 0
        if i == len(pulseStart)-1:
            pass                        # pulse_delta = gap between pulses to look for piggybacks
        elif pulseStart[i+1] - pulseStart[i] <= pulse_delta and pulseStart[i+1] - peakloc[i] > 0: # When adjacent pulses begin within pulse_delta positions,
            for j in range(pulseStart[i+1] - peakloc[i]):# find how many points between the peak of the first and start of the second fall below drop_ratio * first peak
                if rawData[peakloc[i]+j] < rawData[peakloc[i]] * drop_ratio: # To distinguish 'piggyback' pulses: drop_ratio = a number < 1, below_drop_ratio = number of values < drop_ratio
                    count = count + 1
                    if count > below_drop_ratio: # If that number exceeds below_drop_ratio, omit the first pulse from consideration - it is not of interest
                        print(f"Found piggyback at {pulseStart[i]}")
                        pulseStart[i] = 0
                        break
    for i in range(len(pulseStart)):
        if pulseStart[i] > 0:
            print(f"{pulseStart[i]} ({areas[i]})") # Print out where pulses are found, and 'area' under the pulse.
    #end def FindPulse

args = sys.argv
# Use sys.argv to get name of the ini file from command $ python3 analyze.py gage2scope.ini
with open(args[1], 'r') as gage2scope:
    config = gage2scope.readlines()
params = []
for line in config: 
    if '#' not in line:
        params.append(line.split('='))
paradict = {}
for a, b in params:
    paradict.setdefault(a, []).append(b)
# print(vt, width, pulse_delta) # used to test

datfiles = glob.glob('*.dat') # Write program that processes all files with a ".dat" extension in current directory.
# Arbitrary number of files and arbitrary number of data values in each file.
for i in range(len(datfiles)):
    with open(datfiles[0], 'r') as datfile:
        datalist = datfile.readlines()
        datalist = [int(i) for i in datalist]
        data_array = array.array('i', datalist)
        smoothData = np.arange(len(data_array))
        for j in range(len(data_array)):# Must negate all values before using data
            data_array[j] = -data_array[j]
        for j in range(len(data_array)):
            if j < 3 or j >= len(data_array) - 3: # First and last 3 data values are unchanged from originals
                smoothData[j] = data_array[j]
            else: # The 'smoothed' data is set as p[i] = (p[i-3] + 2*p[i-1] + 3*p[i] + 3*p[i+1] + 2*p[i+2] + p[i+3])//15
                smoothData[j] = ((data_array[j-3] + 2*data_array[j-1] + 3*data_array[j] + 3*data_array[j+1] + 2*data_array[j+2] + data_array[j+3])/15)
        x = np.arange(len(data_array))
        fig1 = plt.figure() # Plot both raw and smoothed data using matplotlib, saving in a .pdf file
        plt.plot(x,data_array)
        plt.title(datfiles[0])
        fig1.savefig(datfiles[0] + '.pdf')
        fig2 = plt.figure()
        plt.plot(x,smoothData)
        plt.title(datfiles[0] + ' Smoothed')
        fig2.savefig(datfiles[0] + 'smooth' + '.pdf')
        #plt.show() # Beautiful
        FindPulse(smoothData, data_array, paradict)
        datfiles.remove(datfiles[0])
