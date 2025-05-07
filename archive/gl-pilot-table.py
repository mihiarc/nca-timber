#!/usr/bin/env python
# coding: utf-8

# In[67]:


import pandas as pd
import openpyxl

# read in spatial crosswalk table
priceRegions = pd.read_csv('../data/priceRegions.csv')
# convert columns to character
priceRegions['fips'] = priceRegions['fips'].astype(str).str.zfill(5)
priceRegions['unitcd'] = priceRegions['unitcd'].fillna(0).astype(int)
priceRegions['unitcd'] = priceRegions['unitcd'].astype(str).str.zfill(2)
priceRegions['statecd'] = priceRegions['statecd'].astype(str).str.zfill(2)
priceRegions['priceRegion'] = priceRegions['priceRegion'].astype(str).str.zfill(2)

# drop fips from priceRegions by keeping only unique values of statecd and priceRegion and unitcd
priceRegions = priceRegions.drop(columns=['fips']).drop_duplicates()

# read in northern price data from excel file
pricesNorth = pd.read_excel('../data/Timber Prices/TMN/TMN_Price_Series_June2023.xlsx')


# drop all rows where Region has exactly 2 characters
# these are state mean prices
pricesNorth = pricesNorth[pricesNorth['Region'].str.len() != 2]

# filter for Market = 'Stumpage'
pricesNorth = pricesNorth[pricesNorth['Market'] == 'Stumpage']

# convert 'Period End Date' to datetime
pricesNorth['Period End Date'] = pd.to_datetime(pricesNorth['Period End Date'],
                                                errors='coerce')

# create a year variable from column "Period End Date"
pricesNorth['year'] = pricesNorth['Period End Date'].dt.year

# split the Region column into two columns on '-'
pricesNorth[['state_abbr', 'priceRegion']] = pricesNorth['Region'].str.split('-', n=1, expand=True)
pricesNorth['priceRegion'] = pricesNorth['priceRegion'].str.zfill(2)

# add a column for the state fips code
# first, create a dictionary of state abbreviations and fips codes for MN, WI, MI
state_fips = {'MN': '27', 'WI': '55', 'MI': '26'}
pricesNorth['statecd'] = pricesNorth['state_abbr'].map(state_fips)

# select only the columns we need
# year, priceRegion, Species, Product, $ Per Unit, Units
pricesNorth = pricesNorth[['year', 'statecd', 'priceRegion', 'Species',
                            'Product', '$ Per Unit', 'Units']]

# drop if $ Per Unit is NaN or year is NaN
pricesNorth = pricesNorth.dropna(subset=['$ Per Unit', 'year'])

# if the Units column is 'Cords', convert $ Per Unit to $ per cord
# if the Units column is 'MBF', convert $ Per Unit to $ per MBF
# conversion factors are 1 cord = 128 cubic feet and 1 MBF = 1000 board feet
# 12 board feet = 1 cubic foot
pricesNorth['$ Per Unit'] = pricesNorth['$ Per Unit'].astype(float)
pricesNorth['cuftPrice'] = pricesNorth['$ Per Unit']
pricesNorth.loc[pricesNorth['Units'] == 'cord', 'cuftPrice'] = pricesNorth['$ Per Unit'] / 128
pricesNorth.loc[pricesNorth['Units'] == 'mbf', 'cuftPrice'] = pricesNorth['$ Per Unit'] / 12

# drop the $ Per Unit and Units columns
pricesNorth = pricesNorth.drop(columns=['$ Per Unit', 'Units'])

# rename variables
pricesNorth.rename(columns={'Species': 'priceSpecies'}, inplace=True)

# reduce pricesNorth to the mean price by priceRegion, priceSpecies, Product
pricesNorth = pricesNorth.groupby(
    ['statecd', 'priceRegion','priceSpecies', 'Product']
    )['cuftPrice'].mean().reset_index()

# pivot the table so that each row is a unique year, 
# priceRegion, priceSpecies
# and the columns are the products
pricesNorth = pricesNorth.pivot(
    index=['statecd', 'priceRegion', 'priceSpecies'],
    columns='Product',
    values='cuftPrice').reset_index()

# some prices are not reported for all products
# fill missing values with 0
pricesNorth = pricesNorth.fillna(0)

# add a new variable called "mergedSpecies" to priceNorth. 
# using a specific dictionary, map the priceSpecies to the mergedSpecies
speciesCrosswalk = {'Maple Unspecified': 'Maple',
                    'Mixed Hdwd': 'Hardwood',
                    'Mixed Sftwd': 'Pine',
                    'Other Hdwd': 'Hardwood',
                    'Other Sfwd': 'Pine',
                    'Oak Unspecified': 'Oak',
                    'Other Hardwood': 'Hardwood',
                    'Other Softwood': 'Softwood',
                    'Pine Unspecified': 'Pine',
                    'Spruce Unspecified': 'Spruce',
                    'Spruce/Fir': 'Spruce',
                    'White Birch': 'Paper Birch',
                    'Scrub Oak': 'Oak'}

pricesNorth['mergedSpecies'] = pricesNorth['priceSpecies'].map(speciesCrosswalk)

# if the mergedSpecies is null, set it to the priceSpecies
pricesNorth['mergedSpecies'] = pricesNorth['mergedSpecies'].fillna(pricesNorth['priceSpecies'])

# drop the priceSpecies column
pricesNorth = pricesNorth.drop(columns='priceSpecies')

# use agg() to reduce pricesNorth to the mean price by priceRegion, mergedSpecies
pricesNorth = pricesNorth.groupby(['statecd', 'priceRegion', 'mergedSpecies']).agg({
    'Pulpwood': 'mean',
    'Sawtimber': 'mean'
}).reset_index()

# convert mergedSpecies to lowercase
pricesNorth['mergedSpecies'] = pricesNorth['mergedSpecies'].str.lower()

# melt prices North to long format
pricesNorth = pricesNorth.melt(
    id_vars=['statecd', 'priceRegion', 'mergedSpecies'],
    var_name='product',
    value_name='cuftPrice'
)

# load biomassNorth data from the FS FIA's National Forest Inventory
# data is in excel format on the first sheet
biomassNorth = pd.read_excel('../data/Merch Bio GLakes by spp 08-28-2024.xlsx', sheet_name=0)

# replace NaN with 0 in the biomassNorth data
biomassNorth.fillna(0, inplace=True)

# columns 13-32 are the total volume of timber in cubic feet for each size class
# for example, column 11 is '`0003 5.0-6.9'; which is size class code 0003 and size class 5.0-6.9 inches
# we can use the pandas melt function to convert these columns into rows
biomassNorth = biomassNorth.melt(
    id_vars=biomassNorth.columns[0:13],
    value_vars=biomassNorth.columns[13:29],
    var_name='size_class',
    value_name='volume'
    )


# split the size class code and size class range into two columns
biomassNorth[['size_class_code', 'size_class_range']] = \
    biomassNorth['size_class'].str.split(' ', n=1, expand=True)
# drop the first two characters of the size class code
biomassNorth['size_class_code'] = biomassNorth['size_class_code'].str[2:]
# drop the last character in the size class range
biomassNorth['size_class_range'] = biomassNorth['size_class_range'].str[:-1]


# recode evalid to add year
# convert to string of length 6 with leading zeros
biomassNorth['EVALID'] = biomassNorth['EVALID'].astype(str).str.zfill(6)

# middle two characters are the two digit year; extract and convert to 4 digit integer
biomassNorth['year'] = biomassNorth['EVALID'].str[2:4].astype(int) + 2000

# # format fips codes
# # STATECD should be two characters
# # COUNTYCD should be three characters
biomassNorth['STATECD'] = biomassNorth['STATECD'].astype(str).str.zfill(2)
biomassNorth['COUNTYCD'] = biomassNorth['COUNTYCD'].astype(str).str.zfill(3)
biomassNorth['fips'] = biomassNorth['STATECD'] + biomassNorth['COUNTYCD']

# # format survey unit codes; should be two characters
biomassNorth['UNITCD'] = biomassNorth['UNITCD'].astype(str).str.zfill(2)

# make all variables lowercase
biomassNorth.columns = biomassNorth.columns.str.lower()

# # keep only the columns we need
# # year, fips, unitcd, spclass, spcd, spgrpcd, size_class_code, size_class_range, volume
biomassNorth = biomassNorth[['statenm', 'statecd', 'fips', 'unitcd', 'spcd', 'scientific_name',
                                 'spgrpcd', 'spclass', 'size_class_code',
                                 'size_class_range', 'volume']]

# load harvest species list
harvestSpeciesGL = pd.read_excel('../data/GLakes harvested tree species V2.xlsx', sheet_name='GL harvested spp')

# drop if ESTIMATE is 0
harvestSpeciesGL = harvestSpeciesGL[harvestSpeciesGL['Harvest removals, in trees, at least 5in, forestland'] != 0]

# drop if Estimate is NaN
harvestSpeciesGL = harvestSpeciesGL.dropna(subset=['Harvest removals, in trees, at least 5in, forestland'])

# spatial id in "EVALUATION" looks like "`0055 552101 Wisconsin 2021"
# where "552101" is statecd + two digit year + evalid
# extract the state code from the spatial id
harvestSpeciesGL['statecd'] = harvestSpeciesGL['EVALUATION'].str[6:8]

# species information in "SPECIES" looks like "`0012 SPCD 0012 - balsam fir (Abies balsamea)"
# where "SPCD 0012" is the species code
# extract the second part of species code from the species information
harvestSpeciesGL['spcd'] = harvestSpeciesGL['SPECIES'].str.split(' ').str[2]

# convert spcd to int64
harvestSpeciesGL['spcd'] = harvestSpeciesGL['spcd'].astype('int64')

# rename 4th column to volume
harvestSpeciesGL.rename(columns={'Harvest removals, in trees, at least 5in, forestland': 'volume'}, inplace=True)

# keep only the columns we need
harvestSpeciesGL = harvestSpeciesGL[['statecd', 'spcd']]
# sort and print the unique speciesGL
# speciesGL = harvestSpeciesGL.drop_duplicates()
# speciesGL = speciesGL.sort_values('spcd')
# print(speciesGL['spcd'].unique())

# use timberSpecies dictionary to filter BiomassNorth to only include marketable species
marketSpeciesGL = [
    12, 86, 71, 91, 94, 95, 105, 110,
    111, 121, 125, 126, 129, 130, 131,
    132, 221, 313, 314, 316, 318, 371,
    375, 409, 402, 403, 404, 405, 407,
    462, 531, 541, 543, 544, 546, 601,
    602, 611, 621, 651, 652, 653, 742,
    743, 746, 762, 802, 804, 809, 812,
    822, 823, 826, 830, 832, 833, 837,
    951, 972, 977
    ]

# filter harvestSpeciesGL to only include marketable species
harvestSpeciesGL = harvestSpeciesGL[harvestSpeciesGL['spcd'].isin(marketSpeciesGL)]

# sort and print the unique speciesGL
speciesGL = harvestSpeciesGL.drop_duplicates()  
speciesGL = harvestSpeciesGL['spcd'].unique()
# speciesGL = speciesGL.sort_values('spcd')
# print(speciesGL['spcd'].unique())


biomassNorth = biomassNorth[biomassNorth['spcd'].isin(speciesGL)]
# Create a crosswalk dataframe
crosswalk = pd.DataFrame({'mergedSpecies': ['white pine', 'hard maple',
                                            'hard maple', 'hickory', 'hickory',
                                            'white ash', 'ash', 'hickory',
                                            'black walnut', 'hardwood', 'black cherry',
                                            'white oak', 'oak',
                                            'oak', 'spruce', 'pine', 'spruce',
                                            'white spruce', 'spruce', 'jack pine',
                                            'red pine', 'pine', 'soft maple',
                                            'soft maple', 'yellow birch', 'white birch',
                                            'elm', 'beech', 'black ash', 'hardwood',
                                            'aspen', 'aspen', 'oak',
                                            'red oak', 'basswood', 'elm'],
                          'spcd': [129, 314, 318, 402,
                                   407, 541, 544,
                                   601, 602, 621, 762, 802,
                                   823, 837, 12, 71, 91,
                                   94, 95, 105, 125, 130, 313,
                                   316, 371, 375, 462, 531, 543,
                                   742, 743, 746, 809, 833,
                                   951, 972]})

# Merge the crosswalk dataframe with the biomassNorth dataframe
biomassNorth = biomassNorth.merge(crosswalk, on='spcd', how='left')

# product crosswalk
crosswalkProduct = {'0003': 'Pulpwood',
                    '0004': 'Pulpwood',
                    '0005': 'Pulpwood',
                    '0006': 'Pulpwood',
                    '0007': 'Sawtimber',
                    '0008': 'Sawtimber',
                    '0009': 'Sawtimber',
                    '0010': 'Sawtimber',
                    '0011': 'Sawtimber',
                    '0012': 'Sawtimber',
                    '0013': 'Sawtimber',
                    '0014': 'Sawtimber',
                    '0015': 'Sawtimber',
                    '0016': 'Sawtimber',
                    '0017': 'Sawtimber',
                    '0018': 'Sawtimber'}

# add a new column to biomassNorth called "Product"
# using the crosswalk dictionary, map the size_class_code to the Product
biomassNorth['product'] = biomassNorth['size_class_code'].map(crosswalkProduct)

# add priceRegion to biomassNorth
biomassNorth = biomassNorth.merge(priceRegions, on=['statecd', 'unitcd'])

# rename size_class_range to sizerange
biomassNorth.rename(columns={'size_class_range': 'sizerange'}, inplace=True)

# keep only the columns we need
biomassNorth = biomassNorth[['statecd', 'unitcd', 'priceRegion',
                             'spcd', 'spgrpcd', 'spclass', 'product', 'sizerange',
                             'mergedSpecies', 'volume']]


# merge pricesNorth with biomassNorth
tableNorth = pd.merge(biomassNorth, pricesNorth,
                        how='left', on=['statecd', 'priceRegion', 'product', 'mergedSpecies'])

# calculate the value of the timber
tableNorth['value'] = tableNorth['cuftPrice'] * tableNorth['volume']

# replace missing values with 0
tableNorth = tableNorth.fillna(0)



# In[80]:


# if product is pulpwood, save to pwTable
pwTable = tableNorth[tableNorth['product'] == 'Pulpwood']

# reduce
pwTable = pwTable.groupby(['statecd', 'unitcd', 'priceRegion', 'spcd',
                           'spgrpcd', 'spclass', 'sizerange']).agg({
    'volume': 'sum',
    'value': 'sum'
}).reset_index()

# add a new column to pwTable called "product", set to "Pulpwood"
pwTable['product'] = 'Pulpwood'

# recode the sizerange column
pwTable['sizerange'] = pwTable['sizerange'].replace({'5.0-6.9': '05.0-06.9',
                                                     '7.0-8.9': '07.0-08.9',
                                                    '9.0-10.9': '09.0-10.9',
                                                    '11.0-12.9': '11.0-12.9'})


# In[81]:



# if product is sawtimber, save to stTable
stTable = tableNorth[tableNorth['product'] == 'Sawtimber']

# reduce
stTable = stTable.groupby(['statecd', 'unitcd', 'priceRegion', 'spcd',
                           'spgrpcd', 'spclass', 'sizerange']).agg({
    'volume': 'sum',
    'value': 'sum'
}).reset_index()

# add a new column to stTable called "product", set to "Sawtimber"
stTable['product'] = 'Sawtimber'

# drop sizerange from stTable for sizes greater than or equal to 29"
stTable = stTable[stTable['sizerange'] != '29.0-30.9']
stTable = stTable[stTable['sizerange'] != '31.0-32.9']
stTable = stTable[stTable['sizerange'] != '33.0-34.9']
stTable = stTable[stTable['sizerange'] != '35.0-36.9']

# In[90]:


tableGL = pd.concat([pwTable, stTable])

# add stateAbbr to tableGL
stateAbbr = {'27': 'MN', '55': 'WI', '26': 'MI'}

tableGL['stateAbbr'] = tableGL['statecd'].map(stateAbbr)

# recode spcd to common name, call it species
speciesCrosswalk = {129: 'eastern white pine', 314: 'black maple', 318: 'sugar maple',
                    402: 'bitternut hickory', 407: 'shagbark hickory', 541: 'white ash',
                    544: 'green ash', 601: 'butternut', 602: 'black walnut',
                    621: 'yellow-poplar', 762: 'black cherry', 802: 'white oak',
                    823: 'bur oak', 837: 'black oak', 12: 'balsim fir', 71: 'tamarack',
                    91: 'Norway spruce', 94: 'white spruce', 95: 'black spruce',
                    105: 'jack pine', 125: 'red pine', 130: 'Scotch pine',
                    313: 'boxelder', 316: 'red maple', 371: 'yellow birch',
                    375: 'paper birch', 462: 'hackberry', 531: 'American beech',
                    543: 'black ash', 742: 'eastern cottonwood', 743: 'bigtooth aspen',
                    746: 'quaking aspen', 809: 'northern pin oak', 833: 'northern red oak',
                    951: 'American basswood', 972: 'American elm'}

tableGL['species'] = tableGL['spcd'].map(speciesCrosswalk)

# columns to reorder
columnOrder = ['stateAbbr', 'statecd', 'unitcd', 'priceRegion', 'spcd',
               'spgrpcd', 'species', 'spclass', 'sizerange', 'product', 'volume', 'value']

# reorder columns
tableGL = tableGL[columnOrder]

# replace spclass: Softwood to Coniferous and Hardwood to Non-coniferous
tableGL['spclass'] = tableGL['spclass'].replace({'Softwood': 'Coniferous',
                                                 'Hardwood': 'Non-coniferous'})

# sort tableGL by statecd, priceRegion, spcd, spgrpcd, spclass, sizerange
tableGL = tableGL.sort_values(by=['statecd', 'unitcd', 'priceRegion', 'spcd',
                                 'spgrpcd', 'spclass', 'product', 'sizerange'])

# write tableGL to csv
tableGL.to_csv('../data/tableGL.csv', index=False)

