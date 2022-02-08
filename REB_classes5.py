# %%  REB classes
# Imports
import os as os
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import time
tic = time.perf_counter()
pd.options.mode.chained_assignment = None  # default='warn'

# region Retrieval
# Cleaning
def drop_all(df):
    df.drop(['Leg 3', 'Leg 4', 'Leg 3 Operating Airline',
            'Leg 4 Operating Airline'], axis='columns', inplace=True)

to_from_SIN = pd.read_excel(
    r'C:\Users\amrsa\REB\Data\SIN-SYD\to_from_SIN_6.xlsx', sheet_name=1)

# Import support documents
to_from_SIN_all = pd.read_csv('to_from_SIN_all.csv')
to_from_KUL_all = pd.read_csv('to_from_KUL_all.csv')

# Fixes
# KUL-JED MH was missing month 11. Average of month 10 and 12 was applied
to_from_KUL_all.loc[13277] = to_from_KUL_all[(to_from_KUL_all['Carrier Code'] == 'MH') & (
    to_from_KUL_all['Arr City Code'] == 'JED')].reset_index().copy().iloc[-3]
to_from_KUL_all.loc[13277, ['Frequency', 'Seats (Total)', 'Time series']] = [
    17, 7100, '2019-11-01']


############################################ Retrieval functions ##################################
def count_stops(row):
    """
    ss['Stops'] = ss.apply(lambda row: count_stops(row), axis = 1)
    This is how you use the count_stop() method on the df

    The apply method is already going through each row. Therefore you 
    create a function that goes through the rows accordingly
    and returns the values needed.
    """
    if row['Leg 2'] == '   ' and row['Leg 3'] == '   ' and row['Leg 4'] == '   ':
        return 0
    elif row['Leg 2'] != '   ' and row['Leg 3'] == '   ' and row['Leg 4'] == '   ':
        return 1
    elif row['Leg 2'] != '   ' and row['Leg 3'] != '   ' and row['Leg 4'] == '   ':
        return 2
    elif row['Leg 2'] != '   ' and row['Leg 3'] != '   ' and row['Leg 4'] != '   ':
        return 3


def D(df, name):
    """
    Find D feeder (distance) by merging on Origin Airport from to-from SIN. 
    D trunk is constant
    """

    if name[0:3] == 'SIN':
        ds = pd.read_csv('to_from_SIN_all.csv')
        ds.rename({'Dep Airport Code': 'Origin Airport',
                  'GCD (km)': 'D'}, axis=1, inplace=True)
        # You group by the column and then add a function.
        # It returns the column as the index
        # and the mean removes any categorical columns
        # Reseting the index allows for easier manageability
        ds = ds.groupby('Origin Airport').mean().reset_index()
        ds.drop(['Seats', 'Frequency', 'Seats (Total)'], axis=1, inplace=True)

        return pd.merge(df, ds, on='Origin Airport', how='left')

    else:
        ds = pd.read_csv('to_from_KUL_all.csv')
        ds.rename({'Dep Airport Code': 'Origin Airport',
                  'GCD (km)': 'D'}, axis=1, inplace=True)
        ds = ds.groupby('Origin Airport').mean().reset_index()
        ds.drop(['Seats', 'Frequency', 'Seats (Total)'], axis=1, inplace=True)

        return pd.merge(df, ds, on='Origin Airport', how='left')


def D_trunk(df, name):
    """
    Find D trunk (distance) by merging on Origin Airport from to-from SIN/KUL. 
    """

    if name[0:3] == 'SIN':
        ds = pd.read_csv('to_from_SIN_all.csv')
        ds.rename({'Dep Airport Code': 'Leg Origin Airport', 'GCD (km)': 'D_trunk',
                  'Arr Airport Code': 'Leg Destination Airport'}, axis=1, inplace=True)
        ds = ds.groupby(
            ['Leg Origin Airport', 'Leg Destination Airport']).mean().reset_index()
        ds.drop(['Seats', 'Frequency', 'Seats (Total)'], axis=1, inplace=True)

        return pd.merge(df, ds, on=['Leg Origin Airport', 'Leg Destination Airport'], how='left')

    else:
        ds = pd.read_csv('to_from_KUL_all.csv')
        ds.rename({'Dep Airport Code': 'Leg Origin Airport', 'GCD (km)': 'D_trunk',
                  'Arr Airport Code': 'Leg Destination Airport'}, axis=1, inplace=True)
        ds = ds.groupby(
            ['Leg Origin Airport', 'Leg Destination Airport']).mean().reset_index()
        ds.drop(['Seats', 'Frequency', 'Seats (Total)'], axis=1, inplace=True)

        return pd.merge(df, ds, on=['Leg Origin Airport', 'Leg Destination Airport'], how='left')


def Month(row):
    return int(str(row['Time series'])[4:])


def Month_csv(row):
    return int(str(row['Time series'].split('-')[1]))


def Hours(row):
    return int(str(row['Flying Time'])[0:2])


def Minutes(row):
    return int(str(row['Flying Time'])[3:])


def S_feeder(df, name):
    """
    Find S_feeder (average seats) by merging on Leg 1, Carrier and Month to find average number of seat a feeder aircraft flies
    """

    if name[0:3] == 'SIN':
        s = to_from_SIN_all
        s = s[s['Arr City Code'] == 'SIN']
        s.drop(['Arr City Name', 'Arr City Code', 'Flying Time',
               'Ground Time'], axis=1, inplace=True)
        s = s.groupby(['Carrier Code', 'Dep Airport Code',
                      'Time series']).agg(np.sum).reset_index()
        s['Weighted Average'] = s['Seats (Total)'] / s['Frequency']
        s.rename({'Dep Airport Code': 'Origin Airport', 'Carrier Code': 'Leg 1 Operating Airline',
                 'Weighted Average': 'S_feeder'}, axis=1, inplace=True)
        s['Month'] = s.apply(lambda row: Month_csv(row), axis=1)
        s.drop(['Time series', 'GCD (km)', 'Seats',
               'Seats (Total)', 'Frequency'], axis=1, inplace=True)

        return pd.merge(df, s, on=['Leg 1 Operating Airline', 'Origin Airport', 'Month'], how='left')

    else:
        s = to_from_KUL_all
        s = s[s['Arr City Code'] == 'KUL']
        s.drop(['Arr City Name', 'Arr City Code', 'Flying Time',
               'Ground Time'], axis=1, inplace=True)
        s = s.groupby(['Carrier Code', 'Dep Airport Code',
                      'Time series']).agg(np.sum).reset_index()
        s['Weighted Average'] = s['Seats (Total)'] / s['Frequency']
        s.rename({'Dep Airport Code': 'Origin Airport', 'Carrier Code': 'Leg 1 Operating Airline',
                 'Weighted Average': 'S_feeder'}, axis=1, inplace=True)
        s['Month'] = s.apply(lambda row: Month_csv(row), axis=1)
        s.drop(['Time series', 'GCD (km)', 'Seats',
               'Seats (Total)', 'Frequency'], axis=1, inplace=True)

        return pd.merge(df, s, on=['Leg 1 Operating Airline', 'Origin Airport', 'Month'], how='left')
    # Use Leg 1 Operating airline instead. More accurate.


def S_trunk(df, name):
    """
    Find S_trunk (average seats) by merging on Leg 1, Carrier and Month to find average number of seat a feeder aircraft flies
    """

    if name[0:3] == 'SIN':
        s = to_from_SIN_all
        s = s.groupby(['Carrier Code', 'Dep Airport Code',
                      'Arr Airport Code', 'Time series']).agg(np.sum).reset_index()
        s['Weighted Average'] = s['Seats (Total)'] / s['Frequency']
        s.rename({'Dep Airport Code': 'Leg Origin Airport', 'Carrier Code': 'Leg Operating Airline',
                 'Weighted Average': 'S_trunk', 'Arr Airport Code': 'Leg Destination Airport'}, axis=1, inplace=True)
        s['Month'] = s.apply(lambda row: Month_csv(row), axis=1)
        s.drop(['Time series', 'GCD (km)', 'Seats',
               'Seats (Total)', 'Frequency'], axis=1, inplace=True)
        return pd.merge(df, s, on=['Leg Operating Airline', 'Leg Origin Airport', 'Leg Destination Airport', 'Month'], how='left')

    else:
        s = to_from_KUL_all
        s = s.groupby(['Carrier Code', 'Dep Airport Code',
                      'Arr Airport Code', 'Time series']).agg(np.sum).reset_index()

        s['Weighted Average'] = s['Seats (Total)'] / s['Frequency']

        s.rename({'Dep Airport Code': 'Leg Origin Airport', 'Carrier Code': 'Leg Operating Airline',
                 'Weighted Average': 'S_trunk', 'Arr Airport Code': 'Leg Destination Airport'}, axis=1, inplace=True)
        # I renamed to Destination airport in order to merge on KUL which is the trunk, giving us trunk values for the Cost equations

        s['Month'] = s.apply(lambda row: Month_csv(row), axis=1)
        s.drop(['Time series', 'GCD (km)', 'Seats',
               'Seats (Total)', 'Frequency'], axis=1, inplace=True)

        return pd.merge(df, s, on=['Leg Operating Airline', 'Leg Origin Airport', 'Leg Destination Airport', 'Month'], how='left')


def A(gy):
    def ancillary(row):
        a = pd.read_excel(r'C:\Users\amrsa\OneDrive - University of Surrey\PhD\ATM\Frankie\Publication\Code\Data\Assumption.xlsx', sheet_name=1)
        a.rename({'Code': 'Leg Operating Airline'}, axis=1, inplace=True)
        a.drop(['Assumption', 'Revenue', 'Airline'], axis=1, inplace=True)
        if row['Leg Operating Airline'] == 'D7':
            return a.loc[a[a['Leg Operating Airline']=='D7'].index.values.astype(int)[0],'ARPP($)']
        elif row['Leg Operating Airline'] == 'TR':
            return a.loc[a[a['Leg Operating Airline']=='TR'].index.values.astype(int)[0],'ARPP($)']
        elif row['Cabin Class'] == 'Discount Coach':
            airline = row['Leg Operating Airline']
            if airline in 'SQ QF TR EK BA TR SV MH OD D7 CA NH JL JQ'.split():
                return a.loc[a[a['Leg Operating Airline']==airline].index.values.astype(int)[0],'ARPP($)']
            else:
                return 0
        else:
            return 0       

    gy['ARPP($)'] = gy.apply(lambda row: ancillary(row), axis=1)

    return gy

# def A(gy):
#     a = pd.read_excel(r'C:\Users\amrsa\OneDrive - University of Surrey\PhD\ATM\Frankie\Publication\Code\Data\Assumption.xlsx', sheet_name=1)
#     a.rename({'Code':'Leg Operating Airline'}, axis=1, inplace=True)
#     a.drop(['Assumption', 'Revenue', 'Airline'], axis=1, inplace=True)

#     return pd.merge(gy, a, on=['Leg Operating Airline'])


def t(gy):
    tax = pd.read_excel(
        r'C:\Users\amrsa\OneDrive - University of Surrey\PhD\ATM\Frankie\Publication\Code\Data\Assumption.xlsx', sheet_name=2)
    tax.rename({'Origin': 'Leg Origin Airport',
               'Destination': 'Leg Destination Airport', 'USD': 'Tax($)'}, axis=1, inplace=True)
    tax.drop(['SGD'], axis=1, inplace=True)

    return pd.merge(gy, tax, on=['Leg Origin Airport', 'Leg Destination Airport'], how='left')


def load_factor(gy, l_df):
    """ 
    Retrieve load factor of each airline each month (source: MIDT) onto gy
    """

    # here is where -L.csv goes in
    lf = l_df
    lf = lf.loc[:, 'Origin Airport':'Load Factor']
    lf.drop(['Year', 'Airline Share', 'Passengers',
            'PPDEW'], axis=1, inplace=True)
    lf.rename({'Origin Airport': 'Leg Origin Airport', 'Destination Airport': 'Leg Destination Airport',
              'Operating Airline': 'Leg Operating Airline'}, axis=1, inplace=True)
    lf['Load Factor'] = lf['Load Factor'] / 100

    return pd.merge(gy, lf, on=['Leg Origin Airport', 'Leg Destination Airport', 'Leg Operating Airline', 'Month'], how='left')


def S_total(gy, name):
    """
    Retrieve total seats flown per month (source: OAG)
    """ 

    if name[0:3] == 'SIN':
        s = to_from_SIN_all
        s = s.groupby(['Carrier Code', 'Dep Airport Code',
                      'Arr Airport Code', 'Time series']).agg(np.sum).reset_index()
        s = s[['Dep Airport Code', 'Arr Airport Code',
               'Carrier Code', 'Time series', 'Seats (Total)']]
        s['Month'] = s.apply(lambda row: Month_csv(row), axis=1)
        s.drop('Time series', axis=1, inplace=True)
        s.rename({'Dep Airport Code': 'Leg Origin Airport', 'Arr Airport Code': 'Leg Destination Airport',
                 'Carrier Code': 'Leg Operating Airline'}, axis=1, inplace=True)

        return pd.merge(gy, s, on=['Leg Origin Airport', 'Leg Destination Airport', 'Leg Operating Airline', 'Month'], how='left')

    else:
        s = to_from_KUL_all
        s = s.groupby(['Carrier Code', 'Dep Airport Code',
                      'Arr Airport Code', 'Time series']).agg(np.sum).reset_index()
        s = s[['Dep Airport Code', 'Arr Airport Code',
               'Carrier Code', 'Time series', 'Seats (Total)']]
        s['Month'] = s.apply(lambda row: Month_csv(row), axis=1)
        s.drop('Time series', axis=1, inplace=True)
        s.rename({'Dep Airport Code': 'Leg Origin Airport', 'Arr Airport Code': 'Leg Destination Airport',
                 'Carrier Code': 'Leg Operating Airline'}, axis=1, inplace=True)

        return pd.merge(gy, s, on=['Leg Origin Airport', 'Leg Destination Airport', 'Leg Operating Airline', 'Month'], how='left')


def SBE(gy, name):
    if name[0:3] == 'SIN':
        sbe = to_from_SIN_all.copy()
        sbe['Month'] = sbe.apply(lambda row: Month_csv(row), axis=1)
        sbe['Hours'] = sbe.apply(lambda row: Hours(row), axis=1)
        sbe['Minutes'] = sbe.apply(lambda row: Minutes(row), axis=1)
        sbe['B'] = sbe['Hours'] + sbe['Minutes']/60
        sbe['Specific Aircraft Code'] = sbe['Specific Aircraft Code'].astype(str)

        e = pd.read_excel(
            r'C:\Users\amrsa\OneDrive - University of Surrey\PhD\ATM\Frankie\Publication\Code\Data\Assumption.xlsx', sheet_name=5)
        e = e[['Specific Aircraft Code', '# of e-seats']]
        e['Specific Aircraft Code'] = e['Specific Aircraft Code'].astype(str)

        sbe = pd.merge(sbe, e, on=['Specific Aircraft Code'], how='left')
        sbe['e'] = sbe['# of e-seats'] / sbe['Seats']
        sbe['E_total'] = sbe['Seats (Total)'] * sbe['e']
        sbe['Seats*B'] = sbe['Seats (Total)'] * sbe['B']

        sbe_sum = sbe.groupby(['Dep Airport Code', 'Arr Airport Code', 'Carrier Code', 'Month']).sum(
        ).reset_index()  # im gonna loose B by summing
        sbe_sum['e_wa'] = sbe_sum['E_total'] / sbe_sum['Seats (Total)']
        sbe_sum['B_wa'] = sbe_sum['Seats*B'] / sbe_sum['Seats (Total)']
        sbe_sum.rename({'Dep Airport Code': 'Leg Origin Airport', 'Arr Airport Code': 'Leg Destination Airport',
                       'Carrier Code': 'Leg Operating Airline'}, axis=1, inplace=True)
        sbe_sum.drop(sbe_sum.loc[:, 'Seats':'e'], axis=1, inplace=True)
        sbe_sum.rename({}, axis=1, inplace=True)

        return pd.merge(gy, sbe_sum, on=['Leg Origin Airport', 'Leg Destination Airport', 'Leg Operating Airline', 'Month'])

    else:
        sbe = to_from_KUL_all.copy()
        sbe['Month'] = sbe.apply(lambda row: Month_csv(row), axis=1)
        sbe['Hours'] = sbe.apply(lambda row: Hours(row), axis=1)
        sbe['Minutes'] = sbe.apply(lambda row: Minutes(row), axis=1)
        sbe['B'] = sbe['Hours'] + sbe['Minutes']/60
        sbe['Specific Aircraft Code'] = sbe['Specific Aircraft Code'].astype(
            str)

        e = pd.read_excel(
            r'C:\Users\amrsa\OneDrive - University of Surrey\PhD\ATM\Frankie\Publication\Code\Data\Assumption.xlsx', sheet_name=5)
        e = e[['Specific Aircraft Code', '# of e-seats']]
        e['Specific Aircraft Code'] = e['Specific Aircraft Code'].astype(str)

        sbe = pd.merge(sbe, e, on=['Specific Aircraft Code'], how='left')
        sbe['e'] = sbe['# of e-seats'] / sbe['Seats']
        sbe['E_total'] = sbe['Seats (Total)'] * sbe['e']
        sbe['Seats*B'] = sbe['Seats (Total)'] * sbe['B']

        sbe_sum = sbe.groupby(['Dep Airport Code', 'Arr Airport Code', 'Carrier Code', 'Month']).sum(
        ).reset_index()  # im gonna loose B by summing
        sbe_sum['e_wa'] = sbe_sum['E_total'] / sbe_sum['Seats (Total)']
        sbe_sum['B_wa'] = sbe_sum['Seats*B'] / sbe_sum['Seats (Total)']
        sbe_sum.rename({'Dep Airport Code': 'Leg Origin Airport', 'Arr Airport Code': 'Leg Destination Airport',
                       'Carrier Code': 'Leg Operating Airline'}, axis=1, inplace=True)
        sbe_sum.drop(sbe_sum.loc[:, 'Seats':'e'], axis=1, inplace=True)
        sbe_sum.rename({}, axis=1, inplace=True)

        return pd.merge(gy, sbe_sum, on=['Leg Origin Airport', 'Leg Destination Airport', 'Leg Operating Airline', 'Month'])

def ancillary(row):
    a = pd.read_excel(r'C:\Users\amrsa\OneDrive - University of Surrey\PhD\ATM\Frankie\Publication\Code\Data\Assumption.xlsx', sheet_name=1)
    a.rename({'Code': 'Leg Operating Airline'}, axis=1, inplace=True)
    a.drop(['Assumption', 'Revenue', 'Airline'], axis=1, inplace=True)
    if row['Leg Operating Airline'] == 'D7':
        return a.loc[a[a['Leg Operating Airline']=='D7'].index.values.astype(int)[0],'ARPP($)']
    elif row['Leg Operating Airline'] == 'TR':
        return a.loc[a[a['Leg Operating Airline']=='TR'].index.values.astype(int)[0],'ARPP($)']
    elif row['Cabin Class'] == 'Discount Coach':
        airline = row['Leg Operating Airline']
        if airline in 'SQ QF TR EK BA TR SV MH OD D7 CA NH JL'.split():
            return a.loc[a[a['Leg Operating Airline']==airline].index.values.astype(int)[0],'ARPP($)']#a[a['Leg Operating Airline'] == airline]['ARPP($)'].to_numpy()#
        else:
            return 0
    else:
        return 0 

# endregion Retrieval
# region Calculations
#####################################Calculations####################################################################

# weighted fare?
# Calculate R_dir
def R_dir(row):
    """
    ss['R_dir'] = ss.apply(lambda row: R_dir(row), axis = 1)
    This is how you use the R_dir() method on the df.

    The apply method is already going through each row. Therefore you 
    create a function that goes throught the row accordingly
    and returns the values needed.
    """
    if row.loc['Stops'] == 0:
        return row.loc['OD Avg. Base Fare(USD)'] * row.loc['Passengers']
    else:
        pass


def feeder_body(row):
    """
    ss['feeder_body'] = ss.apply(lambda row: feeder_body(row), axis = 1)
    This is how you use the feeder_body() method on the df.

    The apply method is already going through each row. Therefore you 
    create a function that goes throught the row accordingly
    and returns the values needed.
    """
    if row['S_feeder'] < 236:
        return 'NB'
    else:
        return 'WB'


def trunk_body(row):
    """
    ss['trunk_body'] = ss.apply(lambda row: trunk_body(row), axis = 1)
    This is how you use the trunk_body() method on the df.

    The apply method is already going through each row. Therefore you 
    create a function that goes throught the row accordingly
    and returns the values needed.
    """
    if row['S_trunk'] < 236:
        return 'NB'
    else:
        return 'WB'


def C_trunk(row, name):

    if row['Stops'] == 1:
        if row['trunk_body'] == 'NB':   # feeder eq
            return 2 * (row['D_trunk'] + 277) * (row['S_trunk'] + 104) * 0.019 / row['S_trunk']
        else:                           # trunk eq
            return 2 * (row['D_trunk'] + 2200) * (row['S_trunk'] + 211) * 0.0115 / row['S_trunk']
    else:
        pass


def C_feeder(row):  # _feeder
    """
    Calculates the C_feeder by using D_feeder and S_feeder of the feeder aircraft
    """
    if row['Stops'] == 1:
        if row['feeder_body'] == 'NB':    # feeder eq
            return 2 * (row['D'] + 2200) * (row['S_feeder'] + 211) * 0.0115 / row['S_feeder']
        else:                       # trunk eq
            return 2 * (row['D'] + 277) * (row['S_feeder'] + 104) * 0.019 / row['S_feeder']
    else:
        pass


def R_con(row):
    if row['Stops'] == 1:
        return row['OD Avg. Base Fare(USD)'] * row['Passengers'] * (row['C_trunk']/(row['C_trunk'] + row['C_feeder']))



def gross_yield_anc(df):
    gy = df.groupby(['Leg Origin Airport', 'Leg Destination Airport',
                     'Leg Operating Airline', 'Cabin Class','Month']).sum().reset_index() # this didn't have cabin class 
    gy = gy[['Leg Origin Airport', 'Leg Destination Airport',
               'Leg Operating Airline','Cabin Class', 'Month', 'Passengers', 'R_dir', 'R_con']] # this didn't have cabin class
    gy['Yield/P'] = (gy['R_dir'] + gy['R_con']) / gy['Passengers']
    gy.drop(['R_dir', 'R_con'], axis=1, inplace=True) #  this had passengers
    return gy


def final_D(df, REB):
    d = df.groupby(['Leg Origin Airport', 'Leg Destination Airport']).mean().reset_index()
    d = d['Leg Origin Airport', 'Leg Destination Airport', 'D_trunk']
    return pd.merge(REB, d, on=['Leg Origin Aiport','Leg Destination Airport'])

def airline_type(row):
    if row.loc['Leg Operating Airline'] == 'TR' or row.loc['Leg Operating Airline'] == 'D7' or row.loc['Leg Operating Airline'] == 'JQ' :
        return 'LHLCC'
    else:
        return 'FSNC'

###############################################################################
###############################################################################
###############################################################################
# endregion Calculations
# region Run

# Importing into a list
with os.scandir('Data_All') as files:  # this gives me pointers
    l_files = []
    od_files = []
    print("Retrieving files...")

    print("Creating 2 lists for ODs and LFs")
    for file in files:  # file is the name of the excel sheet
        if file.name.split('.')[0][-2:] == '-L':
            l_file = file
            l_files.append(l_file)

        else:
            od_file = file
            od_files.append(od_file)

od_files = sorted(od_files, key=lambda x: (x.is_dir(), x.name))
l_files  = sorted(l_files, key=lambda x: (x.is_dir(), x.name))

print('\nThese are the ODs:')
for file in od_files:
    print(file.name)

print('\nThese are the load factors:')
for file in l_files:
    print(file.name)


print(' ')

# Airline Code Dictionary
carrier_list = {
    'SIN-PER': ['SQ', 'QF', 'TR'],
    'SIN-MEL': ['SQ', 'QF', 'TR', 'EK'],
    'SIN-SYD': ['SQ', 'QF', 'TR', 'BA'],
    'SIN-KIX': ['SQ', 'TR'],
    'SIN-JED': ['SV', 'TR'],
    'KUL-PER': ['MH', 'OD', 'D7'],
    'KUL-SYD': ['MH', 'D7'],
    'KUL-PEK': ['D7', 'MH', 'CA'],  # AIRPORT-PAIR
    'KUL-KIX': ['MH', 'D7'],
    'KUL-HND': ['NH', 'D7'],  # AIRPORT-PAIR
    'KUL-NRT': ['D7', 'JL', 'MH', 'NH'],  # AIRPORT-PAIR
    'KUL-JED': ['D7', 'MH'],
}

# Selecting airlines
od_df_list = []
for file in od_files:  # for each idf
    print("The airlines involved in", file.name, "are: ")

    df = pd.DataFrame()
    for carrier in carrier_list[file.name.split('.')[0]]:
        print(carrier)

        od_df = pd.read_csv(file)  # extracting csv data into pd.DataFrame
        od_df = od_df[od_df['Leg Operating Airline'] == carrier]
        df = df.append(od_df, ignore_index=True)  # appending to an empty df
    print('\n')

    od_df_list.append(df)  # appending to an empty list


def calculate(df, l_df, name):
    print("\nOpening", name, "...")
    print("Retrieving number of stops...")
    df['Stops'] = df.apply(lambda row: count_stops(row), axis=1)
    print("Moving df onto df2 and keeping stops 0 & 1")
    df2 = df[(df['Stops'] == 0) | (df['Stops'] == 1)]
    drop_all(df2)
    del df
    df = df2

    print("Calculating R_dir...")
    df['R_dir'] = df.apply(lambda row: R_dir(row), axis=1)

    print("Retrieving Distances (D) for feeder segments...")
    df = D(df, name)

    print("Retrieving distances for trunk segments...")
    df = D_trunk(df, name)

    print("Retrieving feeder seats...")
    df = S_feeder(df, name)

    print("Retrieving trunk seats...")
    df = S_trunk(df, name)

    print("Identifying feeder body type...")
    df['feeder_body'] = df.apply(lambda row: feeder_body(row), axis=1)

    print("Identifying trunk body type...")
    df['trunk_body'] = df.apply(lambda row: trunk_body(row), axis=1)

    print("Calculating C_feeder...")
    df['C_feeder'] = df.apply(lambda row: C_feeder(row), axis=1)

    print("Calculating C_trunk...")
    df['C_trunk'] = df.apply(lambda row: C_trunk(row, name), axis=1)

    print("Calculating R_con...")
    df['R_con'] = df.apply(lambda row: R_con(row), axis=1)

    print("Calculating gross yield and generating new dataframe called gy...")
    gy = gross_yield_anc(df)

    print("Retrieving ancillary revenues...")
    gy = A(gy)

    tot_pass = gy.groupby(['Leg Origin Airport','Leg Destination Airport','Leg Operating Airline','Month']).sum().reset_index()
    tot_pass.drop(['Yield/P', 'ARPP($)'], axis=1, inplace=True)
    tot_pass.rename({'Passengers': 'Total Passengers'}, axis=1, inplace=True)

    # tot_seats = gy.groupby(['Leg Origin Airport','Leg Destination Airport','Leg Operating Airline','Month']).sum().reset_index()
    # tot_seats.drop(['Yield/P', 'ARPP($)'], axis=1, inplace=True)
    # tot_seats.rename({'Passengers': 'Total Passengers'}, axis=1, inplace=True)

    gy = pd.merge(gy, tot_pass, on=['Leg Origin Airport','Leg Destination Airport','Leg Operating Airline','Month'], how='left')

    gy['Weight Factor'] = gy['Passengers'] / gy['Total Passengers']

    gy['Yield/P+A'] = gy['Yield/P'] + gy['ARPP($)']

    gy['W_Yield/P+A'] = gy['Yield/P+A'] * gy['Weight Factor']
    
    gy = gy.groupby(['Leg Origin Airport','Leg Destination Airport','Leg Operating Airline','Month']).sum().reset_index()


    print("Retrieving tax...")
    gy = t(gy)

    print("Calculating net yield...")
    gy['W_Net Yield'] = gy['W_Yield/P+A'] - gy['Tax($)']
    # gy['Net_Yield'] = gy['Yield'] + gy['ARPP($)'] - gy['Tax($)']

    print("Retrieving load facotrs...")
    gy = load_factor(gy, l_df)

    print("Retreiving total seats flown...")
    gy = S_total(gy, name)

    print("Calculating R_total...")
    gy['R_total'] = gy['W_Net Yield']*gy['Load Factor'] * \
        gy['Seats (Total)']  # add undersore to LF

    print("Retrieving SBE")
    gy = SBE(gy, name)
    gy['R_total'] = gy['R_total'].astype('float')

    print("Summing R and E")
    RE = gy.groupby(['Leg Operating Airline', 'Leg Origin Airport',
                    'Leg Destination Airport']).sum().reset_index()

    print("Sum_R/Sum_E")
    RE['RE'] = RE['R_total'] / RE['E_total']

    RE.drop(['B_wa','W_Net Yield'], axis=1, inplace=True)

    print("Retrieving average Block hours from dataframe B...")
    B = gy.groupby(['Leg Operating Airline']).mean().reset_index()

    print("Retrieving distaces for ODs...")
    d = df.groupby(
        ['Leg Origin Airport', 'Leg Destination Airport']).mean().reset_index()
    d = d[['Leg Origin Airport', 'Leg Destination Airport','D_trunk']]

    B = B[['Leg Operating Airline', 'B_wa', 'W_Net Yield']]

    print("Merging B onto to RE...")
    REB = pd.merge(RE, B, on=['Leg Operating Airline'], how='left')
    #

    print("Calculating Yield/Passenger")  # This will be retriving
    #REB['Y/Pax'] = REB['Net_Yield']/REB['Passengers']

    print("Calculating REB...")
    REB['REB'] = REB['RE'] / REB['B_wa']
    REB = pd.merge(REB, d, on=['Leg Origin Airport',
                   'Leg Destination Airport'], how='left')


    print("Done!!!")

    return df, gy, RE, REB


dfs = []
gys = []
REs = []
REBs = []
for idf in range(len(od_files)):
    df, gy, RE, REB = calculate(pd.read_csv(
        od_files[idf]), pd.read_csv(l_files[idf]), od_files[idf].name)
    dfs.append(df)
    gys.append(gy)
    REs.append(RE)
    REBs.append(REB)

results_df = pd.concat(dfs, ignore_index=True)

results_gy = pd.concat(gys, ignore_index=True)

results_RE = pd.concat(REs, ignore_index=True)

results_REB = pd.concat(REBs, ignore_index=True)

print('\nThese are the ODs:')
for file in od_files:
    print(file.name)

print('\nThese are the load factors:')
for file in l_files:
    print(file.name)

toc = time.perf_counter()

print("This took", toc - tic, "seconds")

################################# Pre-Plotting ###############################
#REB airline plot
results_REB.sort_values('D_trunk', inplace=True)

# Yield plot
results_REB['Y/P/B'] = results_REB['W_Net Yield'] / results_REB['B_wa']
results_REB['Airline Type'] = results_REB.apply(lambda row: airline_type(row), axis=1)
results_gy['Airline Type'] = results_gy.apply(lambda row: airline_type(row), axis=1)

#Premium passenger plot
results_df['Airline Type'] = results_df.apply(lambda row: airline_type(row), axis=1)

# Mean REB
results_REB['P.REB'] = results_REB['Passengers'] * results_REB['REB']

# seats / e-seats
results_REB['s/e'] = results_REB['Seats (Total)'] / results_REB['E_total'] * 100

# Connecting revenue
cr = results_df.groupby(['Airline Type','Leg Type','Passengers','R_dir','R_con']).sum()

# Ancillaries 
print('Copying results_df')
anc_df = results_df.copy()
anc_gy = gross_yield_anc(anc_df)
anc_gy['ARPP($) 2'] = anc_gy.apply(lambda row: ancillary(row), axis=1)
print(anc_gy.dtypes)
print('ARPP added')
tot_pass = anc_gy.groupby(['Leg Origin Airport','Leg Destination Airport','Leg Operating Airline','Month']).sum().reset_index()
tot_pass.drop(['Yield/P', 'ARPP($) 2'], axis=1, inplace=True)
tot_pass.rename({'Passengers': 'Total Passengers'}, axis=1, inplace=True)
anc_gy = pd.merge(anc_gy, tot_pass, on=['Leg Origin Airport','Leg Destination Airport','Leg Operating Airline','Month'], how='left')
anc_gy['AR*P'] = anc_gy['ARPP($) 2']*anc_gy['Passengers']
anc_gy['Weight Factor'] = anc_gy['Passengers'] / anc_gy['Total Passengers']
anc_gy['Yield/P+A'] = anc_gy['Yield/P'] + anc_gy['ARPP($) 2']
anc_gy['W_Yield/P+A'] = anc_gy['Yield/P+A'] * anc_gy['Weight Factor']
print(anc_gy.dtypes)
gy = anc_gy.groupby(['Leg Origin Airport','Leg Destination Airport','Leg Operating Airline','Month']).sum().reset_index()
gy['Anc/Pax'] = gy['AR*P'] / gy['Passengers']
gy['Airline Type'] = gy.apply(lambda row: airline_type(row), axis=1)
anc = gy.groupby('Airline Type').sum().reset_index()
anc = anc[['Airline Type', 'AR*P']]
pax = gy.groupby('Airline Type').sum().reset_index()
pax = pax[['Airline Type','Passengers']]
anc = pd.merge(anc, pax, on=['Airline Type'])
anc['Ancillary'] = anc['AR*P'] / anc['Passengers']
b = results_gy.groupby('Airline Type').mean().reset_index()
b = b[['Airline Type', 'B_wa']]
anc = pd.merge(anc,b,on='Airline Type')
anc['A/B'] = anc['Ancillary'] / anc['B_wa']
an = anc

# endregion Run
# %% Plotting

# Averages
avgs = results_REB.groupby(['Leg Origin Airport', 'Leg Destination Airport']).mean().reset_index()
avgs.sort_values('D_trunk', inplace=True)
avgs = list(avgs['REB'])
del avgs[6]
avgs[5]=25.8

# x y values
airline_names = list(results_REB['Leg Operating Airline'])
y = list(results_REB['REB'])
y2 = list(results_REB['W_Net Yield'])

x = np.arange(len(results_REB['Leg Operating Airline']))

# parameters
ylim = 45 # y-axis limit
w = 0.65 # bar width
lw = 0.5 # linewidth
fs = 7 # fonstsize
dss = 40.8 # distances location
cpp = 42 # city-pair location
fscp = 9 # font-size city-pair
l = '#3273a8' # LHLC bar color
f = '#878787' # FSNC bar color
lwavgs = 1


####################################### REB Airline values #######################################
fig, ax = plt.subplots(figsize=(15,5)) # Creates a figure with one axes for plotting
ax2=ax.twinx()

reb = ax.bar(x, y, w, color=[f,l,f,f,f,l,l,f,f,l,f,l,f,l,f,f,f,f,l,l,f,f,l,f,f,f,l,f,f,l,f,f,l,f,l])

ax.set_ylabel('REB - Revenue/ e-seat/ block hour (US$)')
ax.set_xticks(x)
ax.set_xticklabels(airline_names)
ax.set_ylim([0,ylim])
ax.set_xlim([0-w, 34+w]) # 33
ax.bar_label(reb, padding=3, fmt='%.1f')

yieldplot = ax2.plot(x, y2, color='k', label= 'Yield/Passenger')
ax2.set_ylabel('Yield / Passenger (US$)')
ax2.set_ylim([0,1000])

ax.plot([2.5,2.5],[0,ylim], color='k',linewidth=lw)
ax.plot([5.5,5.5],[0,ylim], color='k',linewidth=lw)
ax.plot([8.5,8.5],[0,ylim], color='k',linewidth=lw)
ax.plot([10.5,10.5],[0,ylim], color='k',linewidth=lw)
ax.plot([12.5,12.5],[0,ylim], color='k',linewidth=lw)
ax.plot([18.5,18.5],[0,ylim], color='k',linewidth=lw)
ax.plot([23.5,23.5],[0,ylim], color='k',linewidth=lw)
ax.plot([27.5,27.5],[0,ylim], color='k',linewidth=lw)
ax.plot([29.5,29.5],[0,ylim], color='k',linewidth=lw)
ax.plot([32.5,32.5],[0,ylim], color='k',linewidth=lw)

ax.annotate('SIN-PER',xy=(1,cpp),horizontalalignment='center', weight='bold', fontsize=fscp)
ax.annotate('KUL-PER',xy=(4,cpp),horizontalalignment='center', weight='bold', fontsize=fscp)
ax.annotate('KUL-BJS',xy=(7,cpp),horizontalalignment='center', weight='bold', fontsize=fscp)
ax.annotate('SIN-OSA',xy=(9.5,cpp),horizontalalignment='center', weight='bold', fontsize=fscp)
ax.annotate('KUL-OSA',xy=(11.5,cpp),horizontalalignment='center', weight='bold', fontsize=fscp)
ax.annotate('KUL-TYO',xy=(15.5,cpp),horizontalalignment='center', weight='bold', fontsize=fscp)
ax.annotate('SIN-MEL',xy=(21,cpp),horizontalalignment='center', weight='bold', fontsize=fscp)
ax.annotate('SIN-SYD',xy=(25.5,cpp),horizontalalignment='center', weight='bold', fontsize=fscp)
ax.annotate('KUL-SYD',xy=(28.5,cpp),horizontalalignment='center', weight='bold', fontsize=fscp)
ax.annotate('KUL-JED',xy=(31,cpp),horizontalalignment='center', weight='bold', fontsize=fscp)
ax.annotate('SIN-JED',xy=(33.5,cpp),horizontalalignment='center', weight='bold', fontsize=fscp)

ax.annotate('3963 km',xy=(1,dss),horizontalalignment='center', fontsize=fs, style='italic')
ax.annotate('4194 km',xy=(4,dss),horizontalalignment='center', fontsize=fs, style='italic')
ax.annotate('4446 km',xy=(7,dss),horizontalalignment='center', fontsize=fs, style='italic')
ax.annotate('4957 km',xy=(9.5,dss),horizontalalignment='center', fontsize=fs, style='italic')
ax.annotate('4991 km',xy=(11.5,dss),horizontalalignment='center', fontsize=fs, style='italic')
ax.annotate('5400 km',xy=(15.5,dss),horizontalalignment='center', fontsize=fs, style='italic')
ax.annotate('6080 km',xy=(21,dss),horizontalalignment='center', fontsize=fs, style='italic')
ax.annotate('6340 km',xy=(25.5,dss),horizontalalignment='center', fontsize=fs, style='italic')
ax.annotate('6362 km',xy=(28.5,dss),horizontalalignment='center', fontsize=fs, style='italic')
ax.annotate('7087 km',xy=(31,dss),horizontalalignment='center', fontsize=fs, style='italic')
ax.annotate('7379 km',xy=(33.5,dss),horizontalalignment='center', fontsize=fs, style='italic')

mean = ax.plot([0-w,2.5],[avgs[0],avgs[0]], color='k',linewidth=lwavgs, linestyle='dashed', label = 'REB City-Pair mean')
ax.plot([2.5,5.5],[avgs[1],avgs[1]], color='k',linewidth=lwavgs, linestyle='dashed')
ax.plot([5.5,8.5],[avgs[2],avgs[2]], color='k',linewidth=lwavgs, linestyle='dashed')
ax.plot([8.5,10.5],[avgs[3],avgs[3]], color='k',linewidth=lwavgs, linestyle='dashed')
ax.plot([10.5,12.5],[avgs[4],avgs[4]], color='k',linewidth=lwavgs, linestyle='dashed')
ax.plot([12.5,18.5],[avgs[5],avgs[5]], color='k',linewidth=lwavgs, linestyle='dashed')
ax.plot([18.5,23.5],[avgs[6],avgs[6]], color='k',linewidth=lwavgs, linestyle='dashed')
ax.plot([23.5,27.5],[avgs[7],avgs[7]], color='k',linewidth=lwavgs, linestyle='dashed')
ax.plot([27.5,29.5],[avgs[8],avgs[8]], color='k',linewidth=lwavgs, linestyle='dashed')
ax.plot([29.5,32.5],[avgs[9],avgs[9]], color='k',linewidth=lwavgs, linestyle='dashed')
ax.plot([32.5,34+w],[avgs[10],avgs[10]], color='k',linewidth=lwavgs, linestyle='dashed')

# added these two lines
lns = yieldplot+mean
labs = [l.get_label() for l in lns]
ax.legend(lns, labs, loc='lower center', ncol=2,bbox_to_anchor=(0, -.17, 1., .102))#,mode='expand'

plt.show()
fig.savefig('p_Big_REB.eps', format='eps')
fig.savefig('p_Big_REB.png')

#%%
fig, (axy, axp, axc, axa, axl, axs) = plt.subplots(nrows=1, ncols=6, figsize=(15,5), gridspec_kw={'width_ratios': [1,1,2,1,1,1]})

#parameters
w2 = 0.7 # bar width


####################################### Yield ##################################################
yield_type = results_REB.groupby('Airline Type').mean().reset_index()[['Airline Type','Y/P/B']]

airline_types = list(yield_type['Airline Type'])
y = list(yield_type['Y/P/B'])
x = np.arange(len(yield_type['Airline Type']))

yield_plot = axy.bar(x, y, w2)

axy.set_title('YIELD')
axy.set_ylabel('Yield/ passenger/ block hour (US$)')
axy.set_xticks(x)
axy.set_xticklabels(airline_types)
axy.set_ylim([0,80])
axy.set_xlim([0-w2,1+w2])
axy.bar_label(yield_plot, padding=3, fmt='%.1f')

#Arrow
axy.plot([0,0,1],[55,65,65], color='k')
axy.arrow(1,65,0,-28,width=0.01,head_length=3,head_width=0.2, color='k')
axy.annotate('- 43.9%',xy=(0.5,66),horizontalalignment='center')


####################################### Premium Pass #######################################
axp.set_title('PREMIUM PASS.')
axp.set_ylabel('Premium passengers (%)')
import matplotlib.ticker as mtick
axp.yaxis.set_major_formatter(mtick.PercentFormatter())

premium_pass = results_df.groupby(['Airline Type','Cabin Class']).sum().reset_index()[['Airline Type','Cabin Class','Passengers']]
#calculated by hand
y = [13.9,3.9]
x = [0,1]

premium_plot = axp.bar(x,y,w2)

axp.set_xticks(x)
axp.set_xticklabels(airline_types)
axp.set_ylim([0,30])
axp.set_xlim([0-w2,1+w2])
axp.bar_label(premium_plot, padding=3, fmt='%.1f')

#Arrow
axp.plot([0,0,1],[16,18,18], color='k')
axp.arrow(1,18,0,-12,width=0.01,head_length=0.8,head_width=0.2, color='k')
axp.annotate('- 10%p',xy=(0.5,18.3),horizontalalignment='center')


#######################################  Connecting Revenue #######################################
axc.set_title('CONNECTING REVENUE')
axc.yaxis.set_major_formatter(mtick.PercentFormatter())

cr = results_df.groupby(['Airline Type','Leg Type']).sum().reset_index()[['Airline Type','Leg Type','Passengers','R_dir','R_con']]

F_R_dir = cr.loc[1,'R_dir'] 
F_R_con = cr.loc[0,'R_con']
F_P_dir = cr.loc[1,'Passengers'] 
F_P_con = cr.loc[0,'Passengers']

L_R_dir = cr.loc[3,'R_dir'] 
L_R_con = cr.loc[2,'R_con']
L_P_dir = cr.loc[3,'Passengers'] 
L_P_con = cr.loc[2,'Passengers']

F_P_dir_per = F_P_dir/(F_P_dir+F_P_con) * 100
F_P_con_per = 100 - F_P_dir_per
F_R_dir_per = F_R_dir/(F_R_dir+F_R_con) * 100
F_R_con_per = 100 - F_R_dir_per

L_P_dir_per = L_P_dir/(L_P_dir+L_P_con) * 100
L_P_con_per = 100 - L_P_dir_per
L_R_dir_per = L_R_dir/(L_R_dir+L_R_con) * 100
L_R_con_per = 100 - L_R_dir_per

#calculated by hand
labels = 'FSNC FSNC LHLCC LHLCC'.split()
y_dir = [F_P_dir_per, F_R_dir_per, L_P_dir_per, L_R_dir_per]
y_con = [F_P_con_per, F_R_con_per, L_P_con_per, L_R_con_per]
x = [0,1,2,3]


cr_plot_dir = axc.bar(x, y_dir, w2)
cr_plot_con = axc.bar(x, y_con, w2, bottom=y_dir)

axc.set_xticks(x)
axc.set_xticklabels(labels)
axc.set_ylim([0,100])
axc.set_xlim([0-w2,3+w2])
axc.bar_label(cr_plot_dir, padding=-12, fmt='%.1f')

axc.annotate('Direct Passengers',xy=(0,10),horizontalalignment='center', fontsize=10, rotation=90)
axc.annotate('Direct Revenue',xy=(1,10),horizontalalignment='center', fontsize=10, rotation=90)
axc.annotate('Direct Passengers',xy=(2,10),horizontalalignment='center', fontsize=10, rotation=90)
axc.annotate('Direct Revenue',xy=(3,10),horizontalalignment='center', fontsize=10, rotation=90)

axc.annotate('Connecting Passengers (CP)',xy=(0,51),horizontalalignment='center', fontsize=10, rotation=90)
axc.annotate('Connecting Revenue',xy=(0.9,64),horizontalalignment='center', fontsize=10, rotation=90)
axc.annotate('(CR)',xy=(1.2,75),horizontalalignment='center', fontsize=10, rotation=90)
axc.annotate('CP',xy=(2,97),horizontalalignment='center', fontsize=10)
axc.annotate('CR',xy=(3,97),horizontalalignment='center', fontsize=10)


####################################### Ancillaries #######################################

y = np.array(an['A/B'])
x = [0,1]

an_plot = axa.bar(x,y,w2)
axa.set_title('ANCILLARIES')

axa.set_ylabel('Ancillary rev./ pass./ block hour (US$)')
axa.set_xticks(x)
axa.set_xticklabels(airline_types)
axa.set_ylim([0,11])
axa.set_xlim([0-w2,1+w2])
axa.bar_label(an_plot, padding=3, fmt='%.1f')

#Arrow
axa.plot([0,0,1],[4.5,7,7], color='k')
axa.arrow(1,7,0,-1,width=0.01,head_length=0.5,head_width=0.2, color='k')
axa.annotate('+ 30.6%',xy=(0.5,7.2),horizontalalignment='center')


####################################### Load Factor #######################################
axl.set_title('LOAD FACTORS')
axl.set_ylabel('Load Factor (%)')
import matplotlib.ticker as mtick
axl.yaxis.set_major_formatter(mtick.PercentFormatter())

lf = results_gy.groupby(['Airline Type']).mean().reset_index()[['Airline Type','Load Factor']]
#calculated by hand
y = np.array(lf['Load Factor'])*100
x = [0,1]

lf_plot = axl.bar(x,y,w2)

axl.set_ylabel('Yield/ passenger/ block hour (US$)')
axl.set_xticks(x)
axl.set_xticklabels(airline_types)
axl.set_ylim([0,100])
axl.set_xlim([0-w2,1+w2])
axl.bar_label(lf_plot, padding=3, fmt='%.1f')

#Arrow
axl.plot([0,0,1],[80,95,95], color='k')
axl.arrow(1,95,0,-6,width=0.01,head_length=2,head_width=0.2, color='k')
axl.annotate('+ 13%p',xy=(0.5,96),horizontalalignment='center')


####################################### Seat Density #######################################
axs.set_title('SEAT DENSITY')
axs.set_ylabel('Seats/ e-seat (%)')
axs.yaxis.set_major_formatter(mtick.PercentFormatter())

sd = results_REB.groupby(['Airline Type']).mean().reset_index()[['Airline Type','s/e']]
#calculated by hand
y = np.array(sd['s/e'])
x = [0,1]

sd_plot = axs.bar(x,y,w2)

axs.set_xticks(x)
axs.set_xticklabels(airline_types)
axs.set_ylim([0,100])
axs.set_xlim([0-w2,1+w2])
axs.bar_label(sd_plot, padding=3, fmt='%.1f')

#Arrow
axs.plot([0,0,1],[72,98,98], color='k')
axs.arrow(1,98,0,-4,width=0.01,head_length=2,head_width=0.2, color='k')
axs.annotate('+21.8%p',xy=(0.5,94),horizontalalignment='center')

fig.tight_layout()
plt.show()
fig.savefig('p_The6.png')
fig.savefig('p_The6.eps', format='eps')

#%%
####################################### Mean REB #######################################
fig, ax = plt.subplots(figsize= (3,5))
REB_type = results_REB.groupby('Airline Type').sum().reset_index()[['Airline Type','REB','Passengers','P.REB']]
REB_type['REB_wa'] = REB_type['P.REB']/REB_type['Passengers']

airline_types = list(yield_type['Airline Type'])
y = list(REB_type['REB_wa'])
x = np.arange(len(yield_type['Airline Type']))

REB_plot = ax.bar(x, y, 0.6)

ax.set_title('REB')
ax.set_ylabel('REB - Revenue/ e-seat/ block hour (US$)')
ax.set_xticks(x)
ax.set_xticklabels(airline_types)
ax.set_ylim([0,30])
ax.set_xlim([0-w2,1+w2])
ax.bar_label(REB_plot, padding=3, fmt='%.1f')

#Arrow
ax.plot([0,0,1],[26,27,27], color='k')
ax.arrow(1,27,0,-7,width=0.01,head_length=0.75,head_width=0.05, color='k')
ax.annotate('- 26.6%',xy=(0.5,27.5),horizontalalignment='center')
plt.show()

fig.tight_layout()
fig.savefig('p_REB_Avg.eps', format='eps')
fig.savefig('p_REB_Avg.png')

toc = time.perf_counter()

print("This took", toc - tic, "seconds")

# %%
# Tables 
table_reb = results_REB.copy()
table_reb.drop(columns=['Month','Yield/P','ARPP($)','Total Passengers','Weight Factor','Yield/P+A','W_Yield/P+A','Tax($)','Load Factor','Seats*B','e_wa','P.REB','D_trunk'], inplace=True)
load_factors = results_gy.groupby(['Leg Origin Airport','Leg Destination Airport','Leg Operating Airline']).mean().reset_index()
load_factors = load_factors[['Leg Origin Airport','Leg Destination Airport','Leg Operating Airline','Load Factor']]
table_reb = pd.merge(table_reb, load_factors, on=['Leg Origin Airport','Leg Destination Airport','Leg Operating Airline'], how='left')


table_reb.rename({'Leg Operating Airline': 'Airline','Leg Origin Airport':'Origin Airport','Leg Destination Airport':'Destination Airport','Seats (Total)':'Seats','R_total':'R','E_total':'E','B_wa':'B','W_Net Yield':'Net Yield'}, axis=1, inplace=True) #'Total Passengers':'Passengers',
    
table_reb = table_reb[['Origin Airport', 'Destination Airport', 'Airline', 'Passengers', 'Net Yield', 'R', 'E', 'Load Factor', 'RE', 'B', 'REB', 'Y/P/B']]
# table_reb = table_reb.round(1)



# table_reb = table_reb.reindex(columns=[])

table_reb.to_excel("REB.xlsx")
#%%
results_gy.to_excel("RawData.xlsx")
