from pyepw.epw import EPW
import csv
import re
import json
import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import os
import plotly.graph_objs as go
import pandas as pd

## read epw file names
def ReadFileNameInCsv(dir):
    '''
    This function reads the file names stored in a .csv file
    :param dir: This is the path to the directory in which the csv files are located (relative to the working directory)
    :return: A list object in which each element is a file name as a string
    '''
    with open(dir, 'rt') as f:
        filename_list = []
        for i in csv.reader(f):
            for j in i:
                filename_list.append(j)
                if j is None: break
            if i is None: break
        return filename_list
def CalTempHoursInRanges(thresh1:float, thresh2, thresh3, thresh4, drybulb):
        Hour1, Hour2, Hour3, Hour4, Hour5 = 0, 0, 0, 0, 0
        for DBT in drybulb:
            if DBT < thresh1:
                Hour1 += 1
            elif DBT < thresh2:
                Hour2 += 1
            elif DBT < thresh3:
                Hour3 += 1
            elif DBT < thresh4:
                Hour4 += 1
            else:
                Hour5 += 1
        hourlist ={}
        hourlist[str(thresh1)]= Hour1
        hourlist[str(thresh2)] = Hour2
        hourlist[str(thresh3)] = Hour3
        hourlist[str(thresh4)] = Hour4
        return hourlist
def CddHddCal(drybulb, Tbase):
    '''
    This function calculates the cdd and hdd from hourly drybulb temperature, in this case, the hourly data are derived from epw files
    :param drybulb: the hourly drybulb temperature data
    :param Tbase: The base temperature to calculate the cdd hdd results
    :return: This function returns a dictionary of cdd and hdd results
    '''
    Hdd = 0.0
    Cdd = 0.0
    Tmax = []
    Tmin = []
    DegreeDay = {}
    for i in range(0,365):
        dailydb = []
        for j in range(0,24):
            dailydb.append(drybulb[i*24+j])
        Tmax.append(max(dailydb))
        Tmin.append(min(dailydb))
        #print (Tmax[i])
        if Tmin[i] > Tbase :
            Hdd += 0.0
            Cdd += (Tmax[i] +Tmin[i])/2.0 - Tbase
        elif (Tmin[i] + Tmax[i])/2.0 > Tbase:
            Hdd += (Tbase -Tmin[i])/4.0
        elif Tmax[i]>=Tbase:
            Hdd +=(Tbase-Tmin[i])/2.0-(Tmax[i]-Tbase)/4.0
        elif Tmax[i] < Tbase:
            Hdd += Tbase- (Tmax[i]+Tmin[i])/2.0

        if Tmax[i]<Tbase:
            Cdd += 0.0
        elif (Tmax[i]+Tmin[i])/2.0<Tbase:
            Cdd += (Tmax[i]-Tbase)/4.0
        elif Tmin[i]<= Tbase:
            Cdd += (Tmax[i]-Tbase)/2.0-(Tbase - Tmin[i])/4.0
    DegreeDay['Hdd'] = Hdd/5*9+32
    DegreeDay['Cdd'] = Cdd/5*9+32
    return DegreeDay

##This part calculates the Hdd and Cdd from epw hourly dry-bulb temperature data, the base temperature
# is 18.3333C(65F) in this script. Some codes in pyepw package are changed to succussfully read some weather data
# in extremely climates(some ranges broadened to avoid error)

'''
##Make a list of weather stations in USA, the scripts to download all the weather files is :https://gist.github.com/aahoo/b4aaeb179b51b69e342c5e324e305155
LocationLs = os.listdir('../Weatherfile/weather_files_ddy_epw/ddy/USA')

DirName = 'C:\\Users\\yueyue.zhou\\PycharmProjects\\eppy_energy-'
TempBaseline = (65-32)*5/9
#define the base temperature to calculate the cdd/hdd, usually 65F in US

czlist = []
Cdd, Hdd= {},{}
Station = {}
LocCddDICT = {}
LocHddDICT = {}
#list and dictionaries to store data

for i in range(0, len(LocationLs)):
    location = LocationLs[i][:LocationLs[i].rfind('.')]
    # Name of TMY file, usually contains the location name, station name and weather data type.
    
    epwpath = 'C:\\EnergyPlusV8-9-0\\WeatherData\\weather_files_ddy_epw_stat\\epw\\USA\\' + location + '.epw'
    statpath = 'C:\\EnergyPlusV8-9-0\\WeatherData\\weather_files_ddy_epw_stat\\stat\\USA\\' + location + '.stat'
    #path to read epw and stat files
    
    epw = EPW()
    epw.read(epwpath)
    drybulb = []
    for wd in epw.weatherdata:
        drybulb.append(wd.dry_bulb_temperature)
        # read the hourly dry bulb temperature
        
    # print(CddHddCal(drybulb, TempBaseline))

    with open(statpath, 'rt') as f:
        for lines in f.readlines():
            if 'Climate Zone' in lines:
                CZ = lines
                if len(re.findall('"([^"]*)"', CZ)) > 0:
                    CZdata = re.findall('"([^"]*)"', CZ)[0]
                    for i in CZdata:
                        if i.isdigit():
                            if CZdata not in czlist:
                                czlist.append(CZdata)
                                Cdd[CZdata], Hdd[CZdata], Station[CZdata] = [],[] ,[]
                                ##Parse the climate zone information in .stat, 
                                #and create new dictionaries for the climate zone
                                
                            LocCddDICT[location] = int(CddHddCal(drybulb, TempBaseline).get('Cdd'))
                            LocHddDICT[location] = int(CddHddCal(drybulb, TempBaseline).get('Hdd'))
                            ##Calculate the cdd and hdd for files with this information 
                            #and store the results in dictionaries
                            
                            Cdd[CZdata].append(LocCddDICT.get(location))
                            Hdd[CZdata].append(LocHddDICT.get(location))
                            Station[CZdata].append(location)
                            ##Add the results to dictionaries by climate zones               
    print('Reading and calculating ' + location+' done!')

##put data into Pandas DataFrame and output to .csv files
CddY, HddY, StationX,df = [],[],[],[]
for i in range(0,len(czlist)):
    CddY.append(Cdd.get(czlist[i]))
    HddY.append(Hdd.get(czlist[i]))
    StationX.append(Station.get(czlist[i]))
    Cddseries = Cdd.get(czlist[i])
    Hddseries = Hdd.get(czlist[i])
    StationSeries = pd.Series(StationX[i])
    dfitem = pd.DataFrame(dict(Cdd=Cddseries, Hdd=Hddseries), index=StationSeries)
    dfitemSort = dfitem.sort_values(by=['Hdd'])
    df.append( dfitemSort)
    dfitemSort.to_csv(path_or_buf='C:\\Users\\yueyue.zhou\\Desktop\\CddHdd-'+czlist[i]+'.csv')
print(df[2])
'''

##Read CddHdd files from .csv

path = 'C:\\Users\\yueyue.zhou\\Desktop\\CddHddByClimateZone\\'

#Read Climate Zone Names from FileNames, and put data to pds dataframe
CZLs = os.listdir(path)
CzList,df= [],[]
Headers = ['Station', 'Cdd','Hdd']
for FileName  in CZLs:
    CZInf = FileName.split('-')[-1]
    CZ = CZInf.split('.')[0]
    CzList.append(CZ)
    #parse the filename to get Climatezone names only
    labels = []
    #put data to pds dataframe
    dfitem = pd.read_csv(path + FileName,skiprows = 1, names = Headers, index_col=0)

    #Acsending the data in df by hdd( or cdd)
    dfitemSort = dfitem.sort_values(by=['Hdd'])
    #dfitemSort = dfitem.sort_values(by=['Cdd'])

    StationList = dfitemSort.index.tolist()
    for station in StationList:
        label = station.split('_')[1:-1]
        label2 = '.'.join(label)[:'.'.join(label).rfind('.')]
        if label2 not in labels:
            labels.append(label2)
        else:
            dfitemSort = dfitemSort.drop(station)
        ##Read and parse the station name, drop the repeating stations


    LabelCol = pd.Series(labels,index = dfitemSort.index)
    dfitemSort['Label'] = LabelCol
    df.append(dfitemSort)

##plot with Dash
app = dash.Dash()
app.layout = html.Div(children = [
    html.H1(children = 'HddCdd Data Visualization'),
    dcc.Graph(
            id='graph-with-slider'),
    html.Div(),
    dcc.Slider(
            id='ClimateZone-slider',
            min=1,
            max=len(CzList),
            value=1,
            step=1,
            marks={i: CzList[i-1] for i in range(1,len(CzList)+1)},
            included = False,
        )
])

@app.callback(
    dash.dependencies.Output('graph-with-slider', 'figure'),
    [dash.dependencies.Input('ClimateZone-slider', 'value')])
def update_figure(selected_CZ):
    filtered_df = df[selected_CZ-1]
    print(filtered_df)
    traces = []
    traces.append(go.Scatter(
        x= filtered_df['Label'],
        y= filtered_df['Cdd'],
        #text='Cooling Degree Days',
        #mode='markers',
        opacity=0.7,
        marker={
                'size': 10,
                'line': {'width': 0.5, 'color': 'white'}
            },
        name='Cooling Degree Days',
        ))
    traces.append(go.Scatter(
            x=filtered_df['Label'],
            y=filtered_df['Hdd'],
            #text='Heating Degree Days',
            #mode='markers',
            opacity=0.7,
            marker={
                'size': 10,
                'line': {'width': 0.5, 'color': 'white'}
            },
            name='Heating Degree Days',
        ))
    return {
        'data': traces,
        'layout': go.Layout(
            title = 'Hdd Cdd Data by Climate Zones',
            xaxis={'title': 'Station Name', 'autorange': True},
            yaxis={'title': 'Degree Days (Base Temperature: 65F)', 'autorange': True},
            margin={'l': 100, 'b': 250, 't': 50, 'r': 100},
            legend={'x': 0, 'y': 1.1},
            hovermode='closest',
            height = 800,
        )
    }

if __name__ == '__main__':
    app.run_server()
