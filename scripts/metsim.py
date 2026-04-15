import pandas as pd
import typing
import numpy as np
import monetio as mio
import monet
import xarray as xr
import scipy as scipy
import time


def vp(t: float) -> float:
    '''
    t in K based on Rogers (1996)
    '''
    return 2.53*1E9*np.exp(-5.42*1E3/t) # in hPa

# Load the data from Sao Paulo Mirante meteorological station
# The data is available at: http://www.inmet.gov.br/portal/index.php?r=bdmep/bdmep

def load_inmet_data(filepath: str, 
                      sep: str = ';', 
                      decimal: str = ',', 
                      to_csv: bool = True) -> pd.DataFrame:
    
    start_date = '2024-08-01 00:00:00'
    end_date   = '2024-09-30 23:00:00'

    date_range = pd.date_range(start=start_date, end=end_date, 
                               freq='h', tz='America/Sao_Paulo')
    date_comp = pd.DataFrame(date_range, columns=['date'])
    
    mira = pd.read_csv(filepath, comment = '#', sep = sep, decimal = decimal)
    mira['Data'] = pd.to_datetime(mira['Data'], format='%d/%m/%Y')
    mira['hour'] = pd.to_datetime(mira['Hora (UTC)']/100, format='%H').dt.time
    mira['date'] = pd.to_datetime(mira['Data'].astype(str) + ' ' + mira['hour'].astype(str))
    mira['date'] = pd.to_datetime(mira['date'], format='%Y-%m-%d %H:%M:%S')
    mira['date'] = mira['date'].dt.tz_localize('UTC')
    mira['date'] = mira['date'].dt.tz_convert('America/Sao_Paulo')

    df = date_comp.merge(mira, how='left', left_on='date', right_on='date')
    df.drop(columns=['Data', 'hour', "Hora (UTC)"], inplace=True)
    df.rename(columns={"Temp. Ins. (C)": "tc", "Pto Orvalho Ins. (C)": "td",
                       "Umi. Ins. (%)":"rh",
                       "Pressao Ins. (hPa)":"pr", "Vel. Vento (m/s)":"ws",
                       "Dir. Vento (m/s)":"wd", "Chuva (mm)":"rr"}, 
              inplace=True)

    #df['rh'] = ((vp(df['td'] + 273.15)/vp(df['tc'] + 273.15))*100).round(2)

    columns = ['date', 'tc', 'rh', 'pr', 'rr', 'ws', 'wd']
    comment2 = "# date,°C,%,hPa,mm,m/s,degree"
    comment1 = "# Sao Paulo Mirante (A701), -23.496289, -46.620067, 785.64 m"
    df = df.loc[:, columns].set_index('date')
    # Export to CSV with comments:
    if to_csv:
        with open('../post/mirante_aug_sep_2024.csv', 'w') as f:
            f.write(comment1 + '\n')
            f.write(comment2 + '\n')
            df.to_csv(f, index=True, header=True)    
    return df
