#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd

# # Methods
# 
# ## Defining U.S. Production Boundaries
# 
# We define the production boundary for the timber asset account along two dimensions: tree species and spatial extent. The spatial extent is inferred from regions where timber markets are currently active. These regions indicate that buyers (forestry and logging operations) and sellers (timber owners) value the trees as assests when making management decisions. There are four primary U.S. timber markets; the south (11 states), northeast (mostly Maine), the lake states (Michigan, Minnesota, and Wisconsin), and the pacific northwest (Washington, Oregon, and Northern California). Each of these regions has specialized their timber markets to utilize their distinct tree species distribution, topology, and climatic conditions.
# 
# ### The Southern U.S. Timber Market
#     
# The Southern U.S. market is dominated by yellow pine species (list them) including loblolly pine that makes up X% of total harvest. Because of the heavy concentration of yellow pine, standing timber prices are reported broadly with species distinctions falling into only two categories; pine and hardwood. Pine timber is utilized for building materials needing large sawlog size timber, and pulpwood for paper products relying on smaller trees harvested during thinning operations and residue from processing larger timber. Given these market characteristics, we stratify the standing timber biomass according to diameter size class estimated from the U.S. Forest Service's National Forest Inventory.
# 
# Timber Price data for the southern U.S. is curated by TimberMart South, a private firm providing price and market analysis across 11 states. Each state has two regions that generally divide the landscape between the coastal plain and the piedmont region. (what makes these regions different?). Similarly, the NFI estimates forest extent and condition across survey units designed to capture the climatic and topological differences betweent the coastal plain, piedmont, and Appalachian mountain range.
# 
# ### The Great Lakes U.S. Timber Market
# 
# The Great Lakes region is comprised of the northern portions of Michigan, Minnesota, and Wisconsin. This region's timber market has formed around large, slow growing hardwood tree species.
# 
# ### Stumpage vs Delivered Price
# 
# We use stumpage price because our objective is to value the timber asset prior to harvesting. Once timber is harvested the asset moves out of the timber account into the national account for forestry and logging where value is added through additional human and capital inputs. The delivered price is paid to loggers at the mill and differs from stumpage based on the cost of harvesting the trees and transporting them to the mill.

# ### Spatial Extent
# 
# We link price data to biomass volume using the county fips identifier. Each county belongs to a distinct survey unit and price region. 

# In[3]:


# create a dictionary with fia code, species name, species family, and market region
# use the fia code as the key
# use the species name, species family, and market region as the values
# market region is either 'Great Lakes' or 'South'
timberSpecies = {'012': ['balsam fir', 'Pine', 'Great Lakes'],
                 '086': ['eastern redcedar', 'Cypress', 'Great Lakes, South'],
                 '071': ['tamarack', 'Pine', 'Great Lakes'],
                    '091': ['Norway spruce', 'Pine', 'Great Lakes'],
                    '094': ['white spruce', 'Pine', 'Great Lakes'],
                    '095': ['black spruce', 'Pine', 'Great Lakes'],
                    '105': ['jack pine', 'Pine', 'Great Lakes'],
                    '110': ['shortleaf pine', 'Pine', 'South'],
                     '111': ['slash pine', 'Pine', 'South'],
                     '121': ['longleaf pine', 'Pine', 'South'],
                     '125': ['red pine', 'Pine', 'Great Lakes'],
                     '126': ['pitch pine', 'Pine', 'Great Lakes'],
                     '129': ['eastern white pine', 'Pine', 'Great Lakes, South'],
                     '130': ['Scotch (Scots) pine', 'Pine', 'Great Lakes'],
                     '131': ['loblolly pine', 'Pine', 'South'],
                     '132': ['Virginia pine', 'Pine', 'South'],
                     '221': ['baldcypress', 'Cypress', 'South'],
                     '313': ['boxelder', 'Maple', 'Great Lakes'],
                     '314': ['black maple', 'Maple', 'Great Lakes, South'],
                     '316': ['red maple', 'Maple', 'Great Lakes'],
                     '318': ['sugar maple', 'Maple', 'Great Lakes, South'],
                     '371': ['yellow birch', 'Birch', 'Great Lakes'],
                     '375': ['paper birch', 'Birch', 'Great Lakes'],
                     '409': ['mockernut hickory', 'Walnut', 'South'],
                     '402': ['bitternut hickory', 'Walnut', 'Great Lakes, South'],
                     '403': ['pignut hickory', 'Walnut', 'South'],
                     '404': ['pecan', 'Walnut', 'South'],
                     '405': ['shelbark hickory', 'Walnut', 'South'],
                     '407': ['shagbark hickory', 'Walnut', 'South'],
                     '462': ['hackberry', 'Elm', 'Great Lakes'],
                     '531': ['American beech', 'Beech', 'Great Lakes'],
                     '541': ['white ash', 'Olive', 'Great Lakes, South'],
                     '543': ['black ash', 'Olive', 'Great Lakes'],
                     '544': ['green ash', 'Olive', 'Great Lakes, South'],
                     '546': ['blue ash', 'Olive', 'Great Lakes, South'],
                     '601': ['butternut', 'Walnut', 'South'],
                     '602': ['black walnut', 'Walnut', 'Great Lakes, South'],
                     '611': ['sweetgum', 'Witch-hazel', 'South'],
                     '621': ['yellow-poplar', 'Magnolia', 'South'],
                     '651': ['cucubertree', 'Magnolia', 'South'],
                     '652': ['southern magnolia', 'Magnolia', 'South'],
                     '653': ['sweetbay', 'Magnolia', 'South'],
                     '742': ['eastern cottonwood', 'Willow', 'Great Lakes'],
                     '743': ['bigtooth aspen', 'Willow', 'Great Lakes'],
                     '746': ['quaking aspen', 'Willow', 'Great Lakes'],
                     '762': ['black cherry', 'Rose', 'Great Lakes, South'],
                     '802': ['white oak', 'Beech', 'Great Lakes, South'],
                     '804': ['swamp white oak', 'Beech', 'Great Lakes, South'],
                     '809': ['northern pin oak', 'Beech', 'Great Lakes'],
                     '812': ['southern red oak', 'Beech', 'South'],
                     '822': ['overcup oak', 'Beech', 'South'],
                     '823': ['bur oak', 'Beech', 'Great Lakes, South'],
                     '826': ['chinkapin oak', 'Beech', 'Great Lakes'],
                     '830': ['pin oak', 'Beech', 'South'],
                     '832': ['chestnut oak', 'Beech', 'South'],
                     '833': ['northern red oak', 'Beech', 'Great Lakes'],
                     '837': ['black oak', 'Beech', 'Great Lakes, South'],
                     '951': ['American basswood', 'Linden', 'Great Lakes'],
                     '972': ['American elm', 'Elm', 'Great Lakes'],
                     '977': ['rock elm', 'Elm', 'Great Lakes']
                     }

# ### Southern Stumpage Prices

# In[4]:


# process southern stumpage prices
pricesSouth = pd.read_csv('../data/Timber Prices/prices_south.csv')

# columns 4 through 69 are stumpage prices grouped by product type,
# state abbreviation and state region. for example, sawfl1 is sawtimber prices for
# state of Florida and Florida region 1. we can use the pandas melt function to
# convert these columns into rows

pricesSouth = pricesSouth.melt(
    id_vars=pricesSouth.columns[0:3],
    value_vars=pricesSouth.columns[3:69],
    var_name='product',
    value_name='price'
    )

# split the product column into three columns: product, stateAbbr, priceRegion
pricesSouth['stateAbbr'] = pricesSouth['product'].str[3:5].str.upper()
pricesSouth['priceRegion'] = pricesSouth['product'].str[5:].str.zfill(2)
pricesSouth['product'] = pricesSouth['product'].str[:3]

# drop product if equal to 'pre'
pricesSouth = pricesSouth[pricesSouth['product'] != 'pre']

# change 'saw' to 'Sawtimber' and 'pul' to 'Pulpwood'
pricesSouth['product'] = pricesSouth['product'].replace({'saw': 'Sawtimber',
                                                         'plp': 'Pulpwood'})

# change 'pine' and 'oak' to 'Pine' and 'Oak'
pricesSouth['type'] = pricesSouth['type'].replace({'pine': 'Pine',
                                                    'oak': 'Oak'})

# change column 'type' to 'priceSpecies'
pricesSouth.rename(columns={'type': 'priceSpecies'}, inplace=True)

# add state fips code
state_fips = {'AL': '01', 'AR': '05', 'FL': '12', 'GA': '13', 'KY': '21',
              'LA': '22', 'MS': '28', 'NC': '37', 'OK': '40', 'SC': '45',
              'TN': '47', 'TX': '48', 'VA': '51'}
pricesSouth['statecd'] = pricesSouth['stateAbbr'].map(state_fips)

# aggregate prices by year, state, priceRegion, product, priceSpecies
pricesSouth = pricesSouth.groupby(['statecd', 'stateAbbr', 'priceRegion',
                                  'priceSpecies', 'product'])['price'].mean().reset_index()

# convert price to dollars per cubic foot from dollars per ton
# 1 ton = 40 cubic feet
pricesSouth['price'] = pricesSouth['price'] / 40
pricesSouth.rename(columns={'price': 'cuftPrice',
                            'product': 'Product'}, inplace=True)

# group by priceSpecies and product to return the mean over all years
pricesSouth = pricesSouth.groupby(['statecd', 'stateAbbr', 'priceRegion',
                                  'priceSpecies', 'Product'])['cuftPrice'].mean().reset_index()

# print the first 5 rows of the pricesSouth dataframe
# print(pricesSouth.head())

# ## Southern Cut List

# In[5]:


# load harvest species list
harvestSpecies = pd.read_csv('../data/Southern harvested tree species.csv')

# drop if ESTIMATE is 0
harvestSpecies = harvestSpecies[harvestSpecies['ESTIMATE'] != 0]

# drop if Estimate is NaN
harvestSpecies = harvestSpecies.dropna(subset=['ESTIMATE'])

# characters 7 and 8 are of GRP2 is state fip code. extract and name columm statecd
harvestSpecies['statecd'] = harvestSpecies['GRP2'].str[6:8]

# 12-14 of GRP1 is the species code. extract and name column spcd
harvestSpecies['spcd'] = harvestSpecies['GRP1'].str[11:14]

# convert spcd to int64
harvestSpecies['spcd'] = harvestSpecies['spcd'].astype('int64')

# rename ESTIMATE to volume
harvestSpecies.rename(columns={'ESTIMATE': 'volume'}, inplace=True)

# keep only the columns we need
harvestSpecies = harvestSpecies[['statecd', 'spcd']]

# sort and print the unique species
species = harvestSpecies.drop_duplicates()
species = species.sort_values('spcd')
#print(species['spcd'].unique())

# make a list of marketable species
marketSpecies = [68, 110, 111, 121, 129, 131, 132, 221, 314, 318,
                 409, 402, 403, 404, 407, 541, 544, 546, 601, 602,
                 611, 621, 651, 652, 653, 762, 802, 804, 812, 822,
                 823, 830, 832, 837, 405]

# filter the harvestSpecies to only include marketable species
harvestSpecies = harvestSpecies[harvestSpecies['spcd'].isin(marketSpecies)]
                                
# print the unique species
species = harvestSpecies.drop_duplicates()
species = species.sort_values('spcd')
#print(species['spcd'].unique())        

# how many unique species are in each state?
#print(harvestSpecies.groupby('statecd')['spcd'].nunique())

# ## Southern Timber Stock

# In[ ]:


# load biomassSouth data from the FS FIA's National Forest Inventory
# data is in excel format on the first sheet
biomassSouth = pd.read_excel('../data/Merch Bio South by spp 08-28-2024.xlsx', sheet_name=0)

# replace NaN with 0 in the biomassSouth data
biomassSouth.fillna(0, inplace=True)

# columns 13-32 are the total volume of timber in cubic feet for each size class
# for example, column 11 is '`0003 5.0-6.9'; which is size class code 0003 and size class 5.0-6.9 inches
# we can use the pandas melt function to convert these columns into rows
biomassSouth = biomassSouth.melt(
    id_vars=biomassSouth.columns[0:13],
    value_vars=biomassSouth.columns[13:29],
    var_name='size_class',
    value_name='volume'
    )

# split the size class code and size class range into two columns
biomassSouth[['size_class_code', 'size_class_range']] = \
    biomassSouth['size_class'].str.split(' ', n=1, expand=True)
# drop the first two characters of the size class code
biomassSouth['size_class_code'] = biomassSouth['size_class_code'].str[2:]
# drop the last character in the size class range
biomassSouth['size_class_range'] = biomassSouth['size_class_range'].str[:-1]

# recode evalid to add year
# convert to string of length 6 with leading zeros
biomassSouth['EVALID'] = biomassSouth['EVALID'].astype(str).str.zfill(6)

# middle two characters are the two digit year; extract and convert to 4 digit integer
biomassSouth['year'] = biomassSouth['EVALID'].str[2:4].astype(int) + 2000

# # format fips codes
# # STATECD should be two characters
# # COUNTYCD should be three characters
biomassSouth['STATECD'] = biomassSouth['STATECD'].astype(str).str.zfill(2)
biomassSouth['COUNTYCD'] = biomassSouth['COUNTYCD'].astype(str).str.zfill(3)
biomassSouth['fips'] = biomassSouth['STATECD'] + biomassSouth['COUNTYCD']

# # format survey unit codes; should be two characters
biomassSouth['UNITCD'] = biomassSouth['UNITCD'].astype(str).str.zfill(2)

# make all variables lowercase
biomassSouth.columns = biomassSouth.columns.str.lower()

# # keep only the columns we need
# # year, fips, unitcd, spclass, spcd, spgrpcd, size_class_code, size_class_range, volume
biomassSouth = biomassSouth[['year', 'statecd', 'fips', 'unitcd', 'spcd',
                                 'spgrpcd', 'spclass', 'size_class_code',
                                 'size_class_range', 'volume']]

# print number of unique species in each state
# print(biomassSouth.groupby('statecd')['spcd'].nunique())

# filter biomassSouth using harvestSpecies
biomassSouth = biomassSouth[biomassSouth['spcd'].isin(marketSpecies)]

# print number of unique species in each state
# sort and print the unique species
species = biomassSouth.groupby('statecd')['spcd'].nunique()
# print(species)


# ## Price Regions

# In[7]:


# create a crosswalk to merge the biomassSouth data with the pricesSouth data
crosswalkSpecies = {'Softwood': 'Pine',
                    'Hardwood': 'Oak'}

# map priceSpecies to spclass
biomassSouth['priceSpecies'] = biomassSouth['spclass'].map(crosswalkSpecies)
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

# map spclass to product
biomassSouth['Product'] = biomassSouth['size_class_code'].map(crosswalkProduct)
# priceRegions
# print column names
# print(pricesSouth.columns)

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
# print(priceRegions.head())

# ## Southern Table

# In[8]:


# drop states in biomassSouth that are not in pricesSouth
biomassSouth = biomassSouth[biomassSouth['statecd'].isin(pricesSouth['statecd'].unique())]

# print column names
# print(biomassSouth.columns)


# reduce biomassSouth on fips, unitcd, priceRegion,
#  Product, priceSpecies, size_class_range
biomassSouth = biomassSouth.groupby(['statecd', 'fips', 'unitcd', 'spclass',
                                    'spcd', 'spgrpcd', 'Product', 'priceSpecies',
                                    'size_class_range', 'size_class_code'])['volume'].mean().reset_index()

biomassSouth = biomassSouth.groupby(['statecd', 'unitcd', 'Product', 'priceSpecies',
                                     'spcd', 'spgrpcd', 'size_class_range',
                                    'size_class_code'])['volume'].sum().reset_index()



# merge pricesSouth with priceRegions
tableSouth = pd.merge(pricesSouth, priceRegions,
                        how='left', on=['statecd', 'priceRegion'])
# merge biomassSouth with tableSouth
tableSouth = pd.merge(biomassSouth, tableSouth,
                        how='left', on=['statecd', 'unitcd', 'Product', 'priceSpecies'])

# calculate total value as volume * price
tableSouth['value'] = tableSouth['volume'] * tableSouth['cuftPrice']

columnOrder = ['stateAbbr', 'statecd', 'unitcd', 'priceRegion', 'spcd', 'spgrpcd',
                'priceSpecies', 'Product', 'size_class_code', 'size_class_range',
                'cuftPrice', 'volume', 'value']

tableSouth = tableSouth[columnOrder]

# sort the table by statecd, unitcd, priceRegion, spcd, spgrpcd, priceSpecies, Product, then size_class_code
tableSouth = tableSouth.sort_values(['statecd', 'unitcd', 'priceRegion',
                                    'spcd', 'spgrpcd', 'priceSpecies', 'Product', 'size_class_code'])
# if size_class_code is in ['0003', '0004', '0005', '0006'], save to pwTable
pwTable = tableSouth[tableSouth['size_class_code'].isin(['0003', '0004', '0005', '0006'])]

# slice pwTable for Product = 'Pulpwood'
pwTable = pwTable[pwTable['Product'] == 'Pulpwood']

# drop columns from pwTable
pwTable = pwTable[['statecd', 'spcd', 'priceSpecies', 'volume', 'value']]

# rename columns
pwTable.rename(columns={'spcd': 'species',
                        'priceSpecies': 'spclass',
                        'volume': 'pwVolume',
                        'value': 'pwValue'}, inplace=True)

# reduce pwTable to the sum of pwVolume and pwValue by statecd, spclass, species
pwTable = pwTable.groupby(['statecd', 'spclass', 'species']).agg({
    'pwVolume': 'sum',
    'pwValue': 'sum'
}).reset_index()


# if size_class_code is in ['0007',...], save to stTable
stTable = tableSouth[tableSouth['size_class_code'].isin(['0007', '0008', '0009',
                                                         '0010', '0011', '0012',
                                                         '0013', '0014', '0015',
                                                         '0016', '0017', '0018'])]

# drop columns from stTable
stTable = stTable[['statecd', 'spcd', 'priceSpecies', 'volume', 'value']]

# rename columns
stTable.rename(columns={'spcd': 'species',
                        'priceSpecies': 'spclass',
                        'volume': 'stVolume',
                        'value': 'stValue'}, inplace=True)


# reduce stTable to the sum of stVolume and stValue by statecd, spclass, species
stTable = stTable.groupby(['statecd', 'spclass', 'species']).agg({
    'stVolume': 'sum',
    'stValue': 'sum'
}).reset_index()

tableSouth = pd.merge(pwTable, stTable, on=['statecd', 'spclass', 'species'])



# ## Southern Species Dictionary

# In[12]:


# Create a crosswalk dataframe
crosswalk = pd.DataFrame({'species': [318, 402, 403, 404, 405, 407, 409,
                                   541, 544, 546, 601, 602, 611, 621, 651,
                                   652, 653, 762, 802, 804, 812, 822, 823,
                                   830, 832, 837, 68, 110, 111, 121, 129, 131,
                                   132, 221],
                        'spname': ['sugar maple', 'bitternut hickory',
                                   'pignut hickory', 'pecan', 'shelbark hickory',
                                   'shagbark hickory', 'mockernut hickory',
                                   'white ash', 'green ash', 'blue ash',
                                   'butternut', 'black walnut', 'sweetgum',
                                   'yellow-poplar', 'cucumbertree', 'southern magnolia',
                                   'sweetbay', 'black cherry', 'white oak',
                                   'swamp white oak', 'southern red oak', 'overcup oak',
                                   'bur oak', 'pin oak', 'chestnut oak', 'black oak',
                                   'eastern redcedar', 'shortleaf pine', 'slash pine',
                                   'longleaf pine', 'eastern white pine', 'loblolly pine',
                                   'Virginia pine', 'baldcypress']
                          })

# in tableSouth, replace spcd with spname
tableSouth = pd.merge(tableSouth, crosswalk, on='species')


# drop spcd
tableSouth = tableSouth.drop(columns='species')

# rename spname to species
tableSouth.rename(columns={'spname': 'species'}, inplace=True)

# in the column, spclass, replace 'Pine' with 'Softwood' and 'Oak' with 'Hardwood'
tableSouth['spclass'] = tableSouth['spclass'].replace({'Pine': 'Softwood',
                                                        'Oak': 'Hardwood'})


# ## Great Lakes Market
# 
# ### Biomass

# In[19]:


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

# print number of unique species in each state
print(f"Unique species by state ",biomassNorth.groupby('statecd')['spcd'].nunique())


# ### Great Lakes Cut Species

# In[20]:


# import openpyxl

# # load harvest species list
# harvestSpeciesGL = pd.read_excel('../data/GLakes harvested tree species V2.xlsx', sheet_name='GL harvested spp')

# # drop if ESTIMATE is 0
# harvestSpeciesGL = harvestSpeciesGL[harvestSpeciesGL['Harvest removals, in trees, at least 5in, forestland'] != 0]

# # drop if Estimate is NaN
# harvestSpeciesGL = harvestSpeciesGL.dropna(subset=['Harvest removals, in trees, at least 5in, forestland'])


# # spatial id in "EVALUATION" looks like "`0055 552101 Wisconsin 2021"
# # where "552101" is statecd + two digit year + evalid
# # extract the state code from the spatial id
# harvestSpeciesGL['statecd'] = harvestSpeciesGL['EVALUATION'].str[6:8]

# # species information in "SPECIES" looks like "`0012 SPCD 0012 - balsam fir (Abies balsamea)"
# # where "SPCD 0012" is the species code
# # extract the second part of species code from the species information
# harvestSpeciesGL['spcd'] = harvestSpeciesGL['SPECIES'].str.split(' ').str[2]

# # convert spcd to int64
# harvestSpeciesGL['spcd'] = harvestSpeciesGL['spcd'].astype('int64')

# # rename 4th column to volume
# harvestSpeciesGL.rename(columns={'Harvest removals, in trees, at least 5in, forestland': 'volume'}, inplace=True)


# # keep only the columns we need
# harvestSpeciesGL = harvestSpeciesGL[['statecd', 'spcd']]


# # sort and print the unique speciesGL
# speciesGL = harvestSpeciesGL.drop_duplicates()
# speciesGL = speciesGL.sort_values('spcd')
# print(speciesGL['spcd'].unique())


# In[21]:


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
biomassNorth = biomassNorth[biomassNorth['spcd'].isin(marketSpeciesGL)]
print(biomassNorth.groupby('statecd')['spcd'].nunique())

# ### Great Lakes Stumpage Prices

# In[22]:


# read in northern price data from excel file
import openpyxl

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


# In[23]:


# Create a crosswalk dataframe
crosswalk = pd.DataFrame({'mergedSpecies': ['white pine', 'pine', 'hard maple',
                                            'hard maple', 'hickory', 'hickory',
                                            'hickory', 'hickory', 'hickory',
                                            'white ash', 'ash', 'hickory',
                                            'black walnut', 'hardwood', 'black cherry',
                                            'white oak', 'oak', 'oak', 'oak',
                                            'oak', 'spruce', 'pine', 'spruce',
                                            'white spruce', 'spruce', 'jack pine',
                                            'red pine', 'pine', 'soft maple',
                                            'soft maple', 'yellow birch', 'white birch',
                                            'elm', 'beech', 'black ash', 'hardwood',
                                            'aspen', 'aspen', 'oak', 'oak',
                                            'red oak', 'basswood', 'elm', 'elm'],
                          'spcd': [129, 131, 314, 318, 402,
                                   403, 405, 407, 409, 541, 544,
                                   601, 602, 621, 762, 802, 804,
                                   823, 830, 837, 12, 71, 91,
                                   94, 95, 105, 125, 130, 313,
                                   316, 371, 375, 462, 531, 543,
                                   742, 743, 746, 809, 826, 833,
                                   951, 972, 977]})

# Merge the crosswalk dataframe with the biomassNorth dataframe
biomassNorth = biomassNorth.merge(crosswalk, on='spcd', how='left')


# In[24]:


# merge pricesNorth with biomassNorth
tableNorth = pd.merge(biomassNorth, pricesNorth,
                        how='left', on=['statecd', 'mergedSpecies'])

# calculate total value as volume * price
tableNorth['pwValue'] = tableNorth['volume'] * tableNorth['Pulpwood']
tableNorth['stValue'] = tableNorth['volume'] * tableNorth['Sawtimber']

# if size_class_code is in ['0003', '0004', '0005', '0006'], save to pwTable
pwTable = tableNorth[tableNorth['size_class_code'].isin(['0003', '0004', '0005', '0006'])]

# drop columns from pwTable
pwTable = pwTable[['statecd', 'spclass', 'mergedSpecies', 'volume', 'pwValue']]

# rename columns
pwTable.rename(columns={'mergedSpecies': 'species',
                        'volume': 'pwVolume'}, inplace=True)

# reduce pwTable to the sum of pwVolume and pwValue by statecd, spclass, species
pwTable = pwTable.groupby(['statecd', 'spclass', 'species']).agg({
    'pwVolume': 'sum',
    'pwValue': 'sum'
}).reset_index()

# if size_class_code is in ['0007',...], save to stTable
stTable = tableNorth[tableNorth['size_class_code'].isin(['0007', '0008', '0009',
                                                         '0010', '0011', '0012',
                                                         '0013', '0014', '0015',
                                                         '0016', '0017', '0018'])]

# drop columns from stTable
stTable = stTable[['statecd', 'spclass', 'mergedSpecies', 'volume', 'stValue']]

# rename columns
stTable.rename(columns={'mergedSpecies': 'species',
                        'volume': 'stVolume'}, inplace=True)

# reduce stTable to the sum of stVolume and stValue by statecd, spclass, species
stTable = stTable.groupby(['statecd', 'spclass', 'species']).agg({
    'stVolume': 'sum',
    'stValue': 'sum'
}).reset_index()

tableGL = pd.merge(pwTable, stTable, on=['statecd', 'spclass', 'species'])



# In[25]:


# concatinate tableGL and TableSouth
table = pd.concat([tableSouth, tableGL])

# In[26]:


# group by priceSpecies and product and use agg() to get summary statistics
# round to two decimal places
# sort by size_class_range
summary = table.groupby(['spclass', 'species']).agg({
    'pwVolume': 'sum',
    'pwValue': 'sum',
    'stVolume': 'sum',
    'stValue': 'sum'
}).reset_index()


# Convert volume and value to billions
summary['pwVolume'] = summary['pwVolume'] / 1000000000
summary['pwValue'] = summary['pwValue'] / 1000000000
summary['stVolume'] = summary['stVolume'] / 1000000000
summary['stValue'] = summary['stValue'] / 1000000000

# Round to two decimal places
summary = summary.round(2)

# Sort by priceSpecies, Product, and size_class_code
summary = summary.sort_values(by=['spclass', 'species'])

# add a column for total volume and total value
summary['totalVolume'] = summary['pwVolume'] + summary['stVolume']
summary['totalValue'] = summary['pwValue'] + summary['stValue']

# Sort by total value
summary = summary.sort_values('totalValue', ascending=False)

# save to csv
summary.to_csv('../data/final-table-v01.csv', index=False)
tableGL.to_csv('../data/tableGL.csv', index=False)
tableSouth.to_csv('../data/tableSouth.csv', index=False)
table.to_csv('../data/table.csv', index=False)

# Display the summary statistics
summary

# In[196]:


# what is the total volume of the timber stock in the southern region?
print(f"The total volume of the timber stock in the southern region is {summarySouth['volume'].sum():,.2f} billion cubic feet")

# what is the total value of the timber stock in the southern region?
print(f"The total value of the timber stock in the southern region is ${summarySouth['value'].sum():,.2f} (in billions)")

# what is the total volume of the timber stock in the northern region?
print(f"The total volume of the timber stock in the great lakes region is {summaryGL['pwVolume'].sum() + summaryGL['stVolume'].sum():,.2f} billion cubic feet")

# what is the total value of the timber stock in the northern region?
print(f"The total value of the timber stock in the great lakes region is ${summaryGL['pwValue'].sum() + summaryGL['stValue'].sum():,.2f} (in billions)")
