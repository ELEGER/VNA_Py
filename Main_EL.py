###############################################################
#                                                             #
#   Example Python 3 code                                     #
#   for controlling a Copper Mountain Technologies VNA        #
#                                                             #
#   Sets up the VNA and gets marker data                      #
#   Written By Brian Walker support@coppermountaintech.com    #
#                                                             #
###############################################################

import pyvisa as visa   #PyVisa is required along with NIVisa
import datetime
import os        
import numpy as np

import pandas as pd
import time
rm = visa.ResourceManager()

#Connect to a Socket on the local machine at 5025
#Use the IP address of a remote machine to connect to it instead
# à condition que ce port soit ouvert

try:
    CMT = rm.open_resource('TCPIP0::localhost::5025::SOCKET') 
except:
    print("Failure to connect to VNA!")
    print("Check network settings")
#The VNA ends each line with this. Reads will time out without this
CMT.read_termination='\n'

#Set a really long timeout period for slow sweeps
CMT.timeout = 100000

#Set up the start, stop, IFBW and number of points
values=[]

#Initialisation
CMT.write_ascii_values('SYSTem:PRESet\n',values)

#vider le registre
CMT.write_ascii_values('*CLS\n',values)

#lecture de l'identité du VNA
CMT.query('*IDN?\n')
#%%
#uint8(['SENSe1:FREQuency:STARt ', f1_hz, 'MHz']), nl]);
#uint8(['SENSe1:FREQuency:STOP ', f2_hz, 'MHz']), nl]);
#uint8(['SENSe1:SWEep:POInts ', num_points]), nl]);
#uint8(['SENSe1:SWEep:POInts ', num_points]), nl]);
#uint8(['SOURce1:POWer:LEVel:IMMediate ', power_level_dbm]), nl]);
#uint8('TRIGger:SEQuence:SOURce BUS'), nl]);

#%Execute the measurement
#   write(vna, [uint8('*WAI'), nl]);
#   pause(0.01);
#   write(vna, [uint8('TRIGger:SEQuence:SINGle'), nl]);
#   pause(0.01);

f_start_MHz = 200
f_stop_MHz  = 5000
bWidth_Hz   = 30000
nb_points   = 201 # 401 801 1601 

Specs=pd.DataFrame(columns=['f_start_MHz','f_stop_MHz','bWidth_Hz','nb_points'])
Specs['f_start_MHz']=[f_start_MHz]
Specs['f_stop_MHz']=[f_stop_MHz]
Specs['bWidth_Hz']=[bWidth_Hz]
Specs['nb_points']=[nb_points]


CMT.write_ascii_values('SENS1:FREQ:STAR ' + str(f_start_MHz) + ' MHZ\n',values)
CMT.write_ascii_values('SENS1:FREQ:STOP ' + str(f_stop_MHz) + ' MHZ\n',values)
CMT.write_ascii_values('SENS1:BWID ' + str(bWidth_Hz) +  ' HZ\n',values)
CMT.write_ascii_values('SENS1:SWE:POIN ' + str(nb_points) +  ' \n',values)
CMT.write_ascii_values('TRIG:SOUR BUS\n',values)

#Set up 1 trace, S11 in smith
CMT.write_ascii_values('CALC1:PAR:COUN 1\n',values) # 1 Traces
CMT.write_ascii_values('CALC1:PAR1:DEF S11\n',values) # Choose S11 for trace 1
CMT.write_ascii_values('CALC1:FORM SMith\n',values)  # smith SMIth

#définir un marqueur
CMT.write_ascii_values('CALC1:MARK1:STAT ON\n',values)  #Set a Marker at 2500 MHz
CMT.write_ascii_values('CALC1:MARK1:X 2500 MHZ\n',values) 

#There is no calibration yet
#You could use the next statement to call in VNA state with calibration
#Alternatively, code could be added to direct
#the user to perform calibration. Assume that test.cfg already exists
#in C:\VNA\TRVNA\State directory
#CMT.write_ascii_values('MMEM:LOAD "test"\n',values) #Get calibrated test state


datetime_object = datetime.datetime.now()
year   = datetime_object.year
month  = datetime_object.month
day    = datetime_object.day
hour   = datetime_object.hour
minute = datetime_object.minute

# nom du répértoire est la date-heure de mesure
Filename='Bloub'
directory_name = 'What_'+str(year) + '_' + str(month)+ '_' + str(day)+ '_' + str(hour)+ 'h_' + str(minute)+ '_min'

#création du dossier
os.getcwd()
os.mkdir(str(directory_name))
#os.chdir(str(directory_name))

# nombre de mesure à effectuer à chaque activation: 100
number_of_measurement= 1
data=pd.DataFrame(columns=['Freq','RS11','IS11','Time'])

delay=3 #3secondes...



#%%

Freq=[]
Freq_T=[]
S11_real_T=[]
S11_imag_T=[]
S11=[]
Timing=[]
Temps=0

number_of_measurement= 10**9
for o in range(int(number_of_measurement)):
    #Trigger a measurement
    CMT.write_ascii_values('TRIG:SEQ:SING\n',values) #Trigger a single sweep
    CMT.query('*OPC?\n') #Wait for measurement to complete
    Freq = CMT.query('SENS1:FREQ:DATA?\n') #Get data as string
    S11 = CMT.query('CALC1:TRAC1:DATA:FDAT?\n') #Get data as string
    #Get Marker measurment
    M1 = CMT.query('CALC1:MARK1:Y?\n') #Get the value at Marker 1
    M1 = M1.split(',') #Break the long string into a list with 2 members
    M1 = float(M1[0]) #Take the first member and turn it into a float
    print('Marker 1 is ',M1,' dB') #Print out the dB value at marker 1
    
    #split the long strings into a string list
    #also take every other value from magnitues since second value is 0
    #If complex data were needed we would use polar format and the second
    #value would be the imaginary part
    Freq_T=Freq_T+Freq.split(',')
    S11 = S11.split(',') # [partie réelle(1), partie imaginaire (1)...]
    S11_real_T=S11_real_T+S11[0::2]
    S11_imag_T=S11_imag_T+S11[1::2]
    Timing=Timing+(np.ones(nb_points)*Temps).tolist()
    #data['Freq']=Freq
    #data['RS11']=append(S11[0::2],ignore_index=True)
    #data['IS11']=data['RS11'].append(S11[1::2],ignore_index=True)
    #with open ('mesure' + str(o) + '.txt','w') as out_file:
    #    out_file.write('Frequency' + ',' +  'Real S11' + ',' +  'Imag S11' + '\n')
    #    for i in range(len(Freq)):#
    #        out_str = str(Freq[i]) + ',' +  str(S11_real[i]) + ',' +  str(S11_imag[i]) + '\n'
    #        out_file.write(out_str)
    #    out_file.close()
    print('Delay')
    time.sleep(delay)
    Temps=Temps+delay
#%% FAut sauver

data['Freq']=Freq_T
data['RS11']=S11_real_T
data['IS11']=S11_imag_T

data.to_csv('./'+directory_name+'/Data_'+Filename+'.csv',float_format='%.8f',index=False)
Specs.to_csv('./'+directory_name+'/Specs_'+Filename+'.csv',float_format='%.8f',index=False)