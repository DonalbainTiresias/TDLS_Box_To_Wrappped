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
from datetime import datetime


print str(datetime.now())
#%%

book='2'
page='22'

start=200
stop=600
#This sets the range of the data to be looked at for finding the peak of the Lorentzian fit.



Number_Of_Tubes=3

Number_Of_Cycles=4
 #How many ramps in each run?



#dirpath ='C:\Users\s267636\Desktop\B1P'
#dirpath = 'C:\Users\s267636\Desktop\SandBox\\B1P'

dirpath= 'Z:\Data\BookBOOK\\bBOOKp'
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
            Intensities=amplitudes*amplitudes
            Intensities=Intensities[1:]
            times=my_csv['Time[s]']
            times.columns=['Time[s]']
            
            heights = Intensities.apply(Split_Then_Gauss, axis=1, args=[Number_Of_Tubes])
            print 'Heights done'
            heights = heights.apply(pd.Series)

            averages= heights.apply(Average, axis=0, args=[Number_Of_Cycles])
            a=[]
            for i in range(len(averages)-1):
                q=abs(averages[0][i]-averages[0][i+1])
                a.append(q)
            cutpoint=a.index(max(a))

            
            #wrapped=averages[averages[0].idxmax():].append(averages[:averages[0].idxmax()]).reset_index(drop=True)
            wrapped=averages[cutpoint:].append(averages[:cutpoint]).reset_index(drop=True)


            print 'Wrapping Done'
            LineFit_Data=wrapped.apply(LineFitter, axis=0)
            Residuals=pd.DataFrame(LineFit_Data.loc['Delta_y'].to_frame().T)
            FittedLine=pd.DataFrame(LineFit_Data.loc['Fitted_y'].to_frame().T)
            #print'All is well'
            Normalised_Data=pd.DataFrame(LineFit_Data.loc['Normalised_y'].to_frame().T)
            #Normalised_Data=pd.DataFrame(Normalised_Data.loc['Normalised Absorption'].to_frame().T)
            Normalised_And_Reframed=pd.DataFrame()
            Residuals_And_Reframed=pd.DataFrame()
            Fitted_And_Reframed=pd.DataFrame()
            
            for z in range(Number_Of_Tubes):
    
                
                q=Normalised_Data[z].apply(pd.Series).T
                w=pd.DataFrame(data=q)
                w.columns=['Normalised Tube ' +str(z+1)]
    
                
                Normalised_And_Reframed = pd.concat([Normalised_And_Reframed,w],axis=1)
            
            for z in range(Number_Of_Tubes):
    
                
                q=Residuals[z].apply(pd.Series).T
                w=pd.DataFrame(data=q)
                w.columns=['Residuals Tube ' +str(z+1)]
    
                
                Residuals_And_Reframed = pd.concat([Residuals_And_Reframed,w],axis=1)
            
            for z in range(Number_Of_Tubes):
    
                
                q=FittedLine[z].apply(pd.Series).T
                w=pd.DataFrame(data=q)
                w.columns=['Fitted Tube ' +str(z+1)]

                Fitted_And_Reframed=pd.concat([Fitted_And_Reframed,w],axis=1)
            
            Residuals =    Residuals_And_Reframed
            FittedLine= Fitted_And_Reframed
                
            
            
            PeakHeight=Normalised_And_Reframed.apply(LorentzGetter, args=[start,stop])
            Normalised_Absorption = pd.DataFrame(PeakHeight.loc['Gauss_Height'].to_frame().T)
            
            Normalised_Absorption['Run']=int(filename[-19:-14])
            #print'testing'
            fakearray=np.array(Normalised_Absorption)
            Collated_Normalised_Absorption=Collated_Normalised_Absorption.append(Normalised_Absorption, ignore_index = True)
            List_of_filenames.append(str(filename.replace('_amplitude.csv','')[-5:]))
            

            
            
#            Residuals.columns=['Residuals ' + str(int(col)) for col in Residuals.columns ]
#            FittedLine.columns=['Fitted Line ' + str(int(col)) for col in FittedLine.columns]
            averages.columns=['Averaged Intensity ' + str(int(col+1)) for col in averages.columns] 
            heights.columns=['Calculated Intensity ' + str(int(col+1)) for col in heights.columns]
            wrapped.columns=['Wrapped Intensity ' + str(int(col+1)) for col in wrapped.columns]
#            Normalised_Absorption.columns=['Normalised Absorption ' + str(int(col)) for col in Normalised_Absorption.columns]
            
            gathered_data=pd.concat([times,amplitudes,heights,averages,wrapped,Residuals,FittedLine, Normalised_Absorption],axis=1)
            consolidatedroot = root[:-4]
            consolidated_data_filename = consolidatedroot + 'consolidated_data.csv'
            gathered_data.to_csv(consolidated_data_filename)
            timeb=time.time()
            
            print (" %s seconds " % (timeb - timea)) +' this loop'
            print(" %s seconds " % (time.time() - start_time)) +' so far'
            print(" %s minutes " % ((time.time() - start_time)/60)) +' so far'  
            
            
    
            

                



howmanycolumns=len(Collated_Normalised_Absorption.columns)-1

z=[('Tube ' +str (col+1)) for col in range(howmanycolumns)]
z.append('Run Number')
#print z
Collated_Normalised_Absorption.columns=z
print Collated_Normalised_Absorption

heightsfilename=str('Z:\\Data\\BookBOOK\\bBOOKpPAGE\\bBOOKpPAGE_Heights.csv')
heightsfilename=heightsfilename.replace('PAGE', str(page))
heightsfilename=heightsfilename.replace('BOOK', str(book))

Collated_Normalised_Absorption.to_csv(heightsfilename)
print("--- %s seconds ---" % (time.time() - start_time))
  
    





