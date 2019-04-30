# -*- coding: utf-8 -*-
"""
Created on Mon Oct 01 08:26:00 2018

@author: s267636
"""
import time
import lmfit
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import fnmatch
#from datetime import datetime
import git
import datetime

print str(datetime.datetime.now())
#%%
drive='z'
book='1'
page='199'

start=200
stop=600
#This sets the range of the data to be looked at for finding the peak of the Lorentzian fit.



Number_Of_Tubes=3

Number_Of_Cycles=2
 #How many ramps in each run?



#dirpath ='C:\Users\s267636\Desktop\B1P'
#
dirpath= drive + ':\Data\BookBOOK\\bBOOKp'
#dirpath= 'C:\Data\BookBOOK\\bBOOKp'
dirpath=dirpath.replace('BOOK',str(book))
#dirpath= 'C:\\Data\\b1p'

#%%

def LineFitter(signal,cutoff=0.1, spacing=2):
    x=np.arange(1,(len(signal)+1))
    a=int(len(x)*cutoff)     
    b=spacing*a
    c=int(len(x)*(1-(spacing*cutoff)))
    d=int(len(x)*(1-cutoff))
    Fitted_y=np.arange(float(1),(len(signal)+1))
    Delta_y = np.arange(float(1),(len(signal)+1))
    Normalised_y = np.arange(float(1),(len(signal)+1))
    Filtered_y=np.append(signal[a:b], signal[c:d])
    Filtered_x=np.append(x[a:b], x[c:d])
 

    mod=lmfit.models.LinearModel()
    params=params=mod.guess(Filtered_y, x=Filtered_x)
    Line_Fit=mod.fit(Filtered_y,params, x=Filtered_x)
    Best_Fit=mod.fit(Filtered_y,params, x=Filtered_x).best_fit
    Fitted_slope=Line_Fit.params['slope'].value
    Fitted_intercept=Line_Fit.params['intercept'].value

    def StraightLine(x):
        y=(Fitted_slope*x)+Fitted_intercept
        return(y)
          
    Fitted_y=np.fromfunction(StraightLine,(len(signal),))
    Delta_y = Fitted_y - signal
    Normalised_y = Delta_y / Fitted_y
    #Normalised_y=pd.DataFrame(data=Normalised_y)
    
    #return Normalised_y
    return pd.Series([Fitted_y, Delta_y, Normalised_y], index=['Fitted_y', 'Delta_y', 'Normalised_y'])



def GaussGetter(newlist):
    
    inputdata=np.array(newlist)
    Filtered_x=np.array(range(len(newlist)))
    mod=lmfit.models.GaussianModel()
    params=mod.guess(inputdata,x=Filtered_x)
    Gaussian_Output=mod.fit(inputdata,params, x=Filtered_x)
    outputheight=Gaussian_Output.params['height'].value
    centre=Gaussian_Output.params['center'].value
    outputheight=Gaussian_Output.params['height'].value
    Guassian_Fit=mod.fit(inputdata,params, x=Filtered_x).best_fit
    #outputheight=pd.Series(outputheight)
    
    return outputheight ##Gaussian_Output, centre, Guassian_Fit, Filtered_x);
    

def Splitter(data,Number_of_Chunks):
    
    chunklength=int(len(data)/Number_of_Chunks)
    Split_Data = zip(*[iter(data)]*chunklength)
    
    return (Split_Data)

def Average(data, loops):
    
    chunklength=int(len(data)/loops)
    Split_Data = np.array(zip(*[iter(data)]*chunklength))
    average=np.mean(Split_Data, axis=0)
    average=pd.Series(average)
    
    return(average)    
    
def Split_Then_Gauss(data,Number_of_Tubes):
      
    chunklength=int(len(data)/Number_of_Tubes)
    Split_Data = zip(*[iter(data)]*chunklength)
    GaussHeights=map(GaussGetter,Split_Data)
    
    return(GaussHeights)


def LorentzGetter(newlist,start=150,stop=200):
    
    inputdata=np.array(newlist[start:stop])
    Filtered_x=np.array(range(start,stop))
    
    mod=lmfit.models.LorentzianModel()
    mod.set_param_hint('center', value=((start-stop)/2)+start)
    params=mod.guess(inputdata,x=Filtered_x)
    Gaussian_Output=mod.fit(inputdata,params, x=Filtered_x)
   
    centre=Gaussian_Output.params['center'].value
    Outputheight=Gaussian_Output.params['height'].value
    Lorentzian_Fit=mod.fit(inputdata,params, x=Filtered_x).best_fit        
    
    return pd.Series([ Lorentzian_Fit, Filtered_x, Outputheight], index=['Fitted_y', 'Filtered_x', 'Gauss_Height'])

start_time= time.time()# Initial set up: Clear all the previous graphs from the screen. 

#%%

plt.close('all')



rootPath = dirpath + page

pattern = '*_amplitude.csv' 

Collated_Normalised_Absorption=pd.DataFrame()
List_of_filenames = []


#my_csv=pd.read_csv('Z:\\Data\\Book1\\b1p199\\b1p199_00034\\Amp\\b1p199_00034_amplitude.csv', header=0)
for root, dirs, files in os.walk(rootPath):
    for filename in fnmatch.filter(files, pattern):
        dirlist = ( os.path.join(root, filename))
        with open(dirlist, 'r') as f:
            print filename
            timea=time.time()
            my_csv=pd.read_csv(f) 
            amplitudes=my_csv.drop(my_csv.columns[0], axis = 1 )
            Intensities=amplitudes

            
            heights = Intensities.apply(Split_Then_Gauss, axis=1, args=[Number_Of_Tubes])
            print 'Heights done'
            heights = heights.apply(pd.Series)
            heights.columns=['Calculated Intensity ' + str(int(col+1)) for col in heights.columns]
            consolidateddata=pd.concat([my_csv, heights],axis=1)


            consolidatedroot = root[:-4]
            consolidated_data_filename = consolidatedroot + 'consolidated_data.csv'
            consolidateddata.to_csv(consolidated_data_filename)
            timeb=time.time()
            
            print (" %s seconds " % (timeb - timea)) +' this loop'
            print(" %s seconds " % (time.time() - start_time)) +' so far'
            print(" %s minutes " % ((time.time() - start_time)/60)) +' so far'  
            
             
    
  
#%%    
repo = git.Repo(search_parent_directories=True)
sha = repo.head.object.hexsha


readme='Date of creation: ' +str(datetime.datetime.today().strftime('%Y-%m-%d')) +'\nGit Hash of Software Used: ' +str(sha) + '\nRepositoryAddress: https://github.com/DonalbainTiresias/Three_Tube_TDLS_Graphs.git'  
print readme
textfilename=dirpath+book+'\\'+book+'RRI_to_MetaData.txt'

with open(textfilename, "w") as text_file:
    text_file.write(readme)




