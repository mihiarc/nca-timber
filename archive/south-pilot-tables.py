import pandas as pd
"""
This script processes timber price and biomass data for the southern United States.
It performs the following steps:
1. Reads and processes spatial crosswalk table (`priceRegions`).
2. Reads and processes southern stumpage prices (`pricesSouth`).
3. Calculates pre-merchantable timber prices (`pricesSouthPremerch`).
4. Reads and processes pre-merchantable biomass data (`biomassSouthPremerch`).
5. Merges price and biomass data to create a table of pre-merchantable timber values (`tablePremerch`).
6. Reads and processes harvested species data (`harvestSpecies`).
7. Reads and processes merchantable biomass data (`biomassSouth`).
8. Merges price and biomass data to create a table of merchantable timber values (`tableSouth`).
9. Concatenates pre-merchantable and merchantable tables.
10. Aggregates data to create tables by product type (`pwTable`, `stTable`).
11. Saves the final tables to CSV files.
Files used:
- `../data/priceRegions.csv`
- `../data/Timber Prices/prices_south.csv`
- `../data/Premerch Bio South by spp 08-28-2024.xlsx`
- `../data/Southern harvested tree species.csv`
- `../data/Merch Bio South by spp 08-28-2024.xlsx`
Output files:
- `../data/tableSouthPremerch.csv`
- `../data/tableSouthMerch.csv`
- `../data/tableSouthByProduct.csv`
"""

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

# change 'saw' to 'Sawtimber' and 'pul' to 'Pulpwood' and 'pre' to 'Pre-merchantable'
pricesSouth['product'] = pricesSouth['product'].replace({'saw': 'Sawtimber',
                                                         'plp': 'Pulpwood',
                                                         'pre': 'Pre-merchantable',})

# change 'pine' and 'oak' to 'Pine' and 'Oak'
pricesSouth['type'] = pricesSouth['type'].replace({'pine': 'Pine',
                                                    'oak': 'Oak'})

# change column 'type' to 'spclass'
pricesSouth.rename(columns={'type': 'spclass'}, inplace=True)


# add state fips code
state_fips = {'AL': '01', 'AR': '05', 'FL': '12', 'GA': '13',
              'LA': '22', 'MS': '28', 'NC': '37', 'SC': '45',
              'TN': '47', 'TX': '48', 'VA': '51'}
pricesSouth['statecd'] = pricesSouth['stateAbbr'].map(state_fips)



# aggregate prices by year, state, priceRegion, product, spclass
pricesSouth = pricesSouth.groupby(['statecd', 'stateAbbr', 'priceRegion',
                                  'spclass', 'product'])['price'].mean().reset_index()


# convert price to dollars per cubic foot from dollars per ton
# 1 ton = 40 cubic feet
pricesSouth['price'] = pricesSouth['price'] / 40
pricesSouth.rename(columns={'price': 'cuftPrice',
                            'product': 'Product'}, inplace=True)

# assign a price to pre-merchantable timber that scales the pulpwood price
# using the following formula: pre-merchantable price = pulpwood price / (1 + r)^(Am-age)
# where r = 0.05 and Am-age is the difference between the merchantable age and the age of the stand
# assume a mertchantable age of 15 years for pine. for oak, we assume pre-merch price remains zero
# because oak is not typically managed for pre-merchantable timber
# assume a growth rate of 8.88 cubic feet per year, which is the average growth rate for pine in the south

# calculate pre-merchantable price for pine at size classes 1-1.9", 2-2.9", 3-3.9", 4-4.9".
# assume merchantable age is 15 years

pricesSouthPremerch = pricesSouth.copy()
# drop oak
pricesSouthPremerch = pricesSouthPremerch[pricesSouthPremerch['spclass'] == 'Pine']
# drop sawtimber
pricesSouthPremerch = pricesSouthPremerch[pricesSouthPremerch['Product'] == 'Pulpwood']
# reshape the data
pricesSouthPremerch = pricesSouthPremerch.pivot_table(index=['statecd', 'stateAbbr', 'priceRegion'],
                                                      columns='spclass', values='cuftPrice').reset_index()


# add columns to calculate pre-merchantable price
r = 0.05
Am = 15
pricesSouthPremerch['0004'] = pricesSouthPremerch['Pine'] / (1 + r)**(Am - 12.264)
pricesSouthPremerch['0003'] = pricesSouthPremerch['Pine'] / (1 + r)**(Am - 7.5)
pricesSouthPremerch['0002'] = pricesSouthPremerch['Pine'] / (1 + r)**(Am - 2.736)
pricesSouthPremerch['0001'] = pricesSouthPremerch['Pine'] / (1 + r)**(Am - 0.722)
# melt pricesSouthPremerch
pricesSouthPremerch = pricesSouthPremerch.melt(
    id_vars=['statecd', 'stateAbbr', 'priceRegion'],
    value_vars=['0004', '0003', '0002', '0001'],
    var_name='sizeclass',
    value_name='cuftPrice'
    )

# merge priceregions with pricesSouthPremerch
pricesSouthPremerch = pd.merge(pricesSouthPremerch, priceRegions, on=['statecd', 'priceRegion'])
biomassSouthPremerch = pd.read_excel('../data/Premerch Bio South by spp 08-28-2024.xlsx', sheet_name=0)
# replace NaN with 0 in the biomassSouthPremerch data
biomassSouthPremerch.fillna(0, inplace=True)

# melt the biomassSouthPremerch data; id variables are [0:13]
biomassSouthPremerch = biomassSouthPremerch.melt(
    id_vars=biomassSouthPremerch.columns[0:13],
    var_name='sizeClass',
    value_name='volume'
)

# drop spclass == hardwood
biomassSouthPremerch = biomassSouthPremerch[biomassSouthPremerch['SPCLASS'] != 'Hardwood']

# define marketable pine species
marketSpeciesPremerch = [110, 111, 121, 131]

# filter the biomassSouthPremerch to only include marketable species
biomassSouthPremerch = biomassSouthPremerch[biomassSouthPremerch['SPCD'].isin(marketSpeciesPremerch)]


# split the size class code and size class range into two columns
biomassSouthPremerch[['sizeClass', 'sizeRange']] = \
    biomassSouthPremerch['sizeClass'].str.split(' ', n=1, expand=True)
# drop the first two characters of the size class code
biomassSouthPremerch['sizeClass'] = biomassSouthPremerch['sizeClass'].str[2:]
# drop the last character in the size class range
biomassSouthPremerch['sizeRange'] = biomassSouthPremerch['sizeRange'].str[:-1]


# recode evalid to add year
# convert to string of length 6 with leading zeros
biomassSouthPremerch['EVALID'] = biomassSouthPremerch['EVALID'].astype(str).str.zfill(6)

# middle two characters are the two digit year; extract and convert to 4 digit integer
biomassSouthPremerch['year'] = biomassSouthPremerch['EVALID'].str[2:4].astype(int) + 2000


# # format fips codes
# # STATECD should be two characters
# # COUNTYCD should be three characters
biomassSouthPremerch['STATECD'] = biomassSouthPremerch['STATECD'].astype(str).str.zfill(2)
biomassSouthPremerch['COUNTYCD'] = biomassSouthPremerch['COUNTYCD'].astype(str).str.zfill(3)
biomassSouthPremerch['fips'] = biomassSouthPremerch['STATECD'] + biomassSouthPremerch['COUNTYCD']

# # format survey unit codes; should be two characters
biomassSouthPremerch['UNITCD'] = biomassSouthPremerch['UNITCD'].astype(str).str.zfill(2)

# make all variables lowercase
biomassSouthPremerch.columns = biomassSouthPremerch.columns.str.lower()

# # # keep only the columns we need
# # # year, fips, unitcd, spclass, spcd, spgrpcd, size_class_code, size_class_range, volume
biomassSouthPremerch = biomassSouthPremerch[['year', 'statecd', 'fips', 'unitcd', 'spcd',
                                 'spgrpcd', 'spclass', 'sizeclass',
                                 'sizerange', 'volume']]

# add priceRegion by merging with priceRegions
biomassSouthPremerch = pd.merge(biomassSouthPremerch, priceRegions, on=['statecd', 'unitcd'])
# merge pricesSouthPremerch with biomassSouthPremerch
tablePremerch = biomassSouthPremerch.merge(pricesSouthPremerch,
                                                  how='left',
                                                  on=['statecd', 'unitcd', 'priceRegion', 'sizeclass'])

# drop missing
tablePremerch = tablePremerch.dropna()

# calculate value
tablePremerch['value'] = tablePremerch['volume'] * tablePremerch['cuftPrice']
tablePremerch.columns

# 'stateAbbr', 'statecd', 'unitcd', 'priceRegion', 'spcd', 'spname',
#        'spgrpcd', 'spclass', 'Product', 'size_class_code', 'size_class_range',
#        'cuftPrice', 'volume', 'value'],
# calculate the mean over time
tablePremerch = tablePremerch.groupby(['stateAbbr', 'statecd', 'unitcd',
                                        'priceRegion', 'spcd', 'spgrpcd', 'spclass',
                                          'sizeclass', 'sizerange']).agg(
    volume=('volume', 'mean'),
    value=('value', 'mean')
).reset_index()


# use agg() to sum volume and value by statecd, spcd, spgrpcd, sizeclass, sizerange
tablePremerch = tablePremerch.groupby(['stateAbbr', 'statecd', 'unitcd',
                                        'priceRegion', 'spcd', 'spgrpcd', 'spclass',
                                          'sizeclass', 'sizerange']).agg(
    volume=('volume', 'sum'),
    value=('value', 'sum')
).reset_index()

# drop column sizeclass
tablePremerch.drop(columns='sizeclass', inplace=True)

# add column product and set to 'Pre-merchantable'
tablePremerch['product'] = 'Pre-merchantable'

# save tablePremerch
tablePremerch.to_csv('../data/tableSouthPremerch.csv', index=False)
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

# Create a crosswalk dataframe
crosswalk = pd.DataFrame({'spcd': [318, 402, 403, 404, 405, 407, 409,
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

# drop states in biomassSouth that are not in pricesSouth
biomassSouth = biomassSouth[biomassSouth['statecd'].isin(pricesSouth['statecd'].unique())]


# reduce biomassSouth on fips, unitcd, priceRegion,
#  Product, priceSpecies, size_class_range
biomassSouth = biomassSouth.groupby(['statecd', 'fips', 'unitcd', 'spclass',
                                    'spcd', 'spgrpcd', 'Product', 'priceSpecies',
                                    'size_class_range', 'size_class_code'])['volume'].mean().reset_index()

biomassSouth = biomassSouth.groupby(['statecd', 'unitcd', 'Product', 'priceSpecies',
                                     'spcd', 'spgrpcd', 'size_class_range',
                                    'size_class_code'])['volume'].sum().reset_index()

# rename priceSpecies to spclass
biomassSouth.rename(columns={'priceSpecies': 'spclass'}, inplace=True)


# drop premerch from pricesSouth
pricesSouth = pricesSouth[pricesSouth['Product'] != 'Pre-merchantable']

# merge pricesSouth with priceRegions
tableSouth = pd.merge(pricesSouth, priceRegions,
                        how='left', on=['statecd', 'priceRegion'])

# merge biomassSouth with tableSouth
tableSouth = pd.merge(biomassSouth, tableSouth,
                        how='left', on=['statecd', 'unitcd', 'Product', 'spclass'])


# calculate total value as volume * price
tableSouth['value'] = tableSouth['volume'] * tableSouth['cuftPrice']

# in tableSouth, replace spcd with spname
tableSouth = pd.merge(tableSouth, crosswalk, on='spcd', how='left')

# rename spname to species
tableSouth.rename(columns={'priceSpecies': 'spclass'}, inplace=True)

# in the column, spclass, replace 'Pine' with 'Coniferous' and 'Oak' with 'Non-coniferous'
tableSouth['spclass'] = tableSouth['spclass'].replace({'Pine': 'Coniferous',
                                                        'Oak': 'Non-coniferous'})

columnOrder = ['stateAbbr', 'statecd', 'unitcd', 'priceRegion', 'spcd', 'spname', 'spgrpcd',
                'spclass', 'Product', 'size_class_code', 'size_class_range',
                'cuftPrice', 'volume', 'value']

tableSouth = tableSouth[columnOrder]

# sort the table by statecd, unitcd, priceRegion, spcd, spgrpcd, priceSpecies, Product, then size_class_code
tableSouth = tableSouth.sort_values(['statecd', 'unitcd', 'priceRegion',
                                    'spcd', 'spgrpcd', 'spclass', 'Product', 'size_class_code'])

# drop size codes 15, 16, 17, 18
tableSouth = tableSouth[tableSouth['size_class_code'] != '0015']
tableSouth = tableSouth[tableSouth['size_class_code'] != '0016']
tableSouth = tableSouth[tableSouth['size_class_code'] != '0017']
tableSouth = tableSouth[tableSouth['size_class_code'] != '0018']

# drop spname
tableSouth.drop(columns='spname', inplace=True)
# drop cuftPrice
tableSouth.drop(columns='cuftPrice', inplace=True)
# drop size_class_code
tableSouth.drop(columns='size_class_code', inplace=True)
# rename size_class_range to sizerange
tableSouth.rename(columns={'size_class_range': 'sizerange'}, inplace=True)
# rename Product to product
tableSouth.rename(columns={'Product': 'product'}, inplace=True)

columnOrder = ['stateAbbr', 'statecd', 'unitcd', 'priceRegion', 'spcd', 'spgrpcd',
                'spclass', 'product', 'sizerange',
                'volume', 'value']

tableSouth = tableSouth[columnOrder]


# reorder columns in tablePremerch
tablePremerch = tablePremerch[columnOrder]

# concatenate tableSouth and tablePremerch
tableSouth = pd.concat([tableSouth, tablePremerch])

# recode the sizerange column
tableSouth['sizerange'] = tableSouth['sizerange'].replace({'1.0-1.9': '01.0-01.9',
                                                            '2.0-2.9': '02.0-02.9',
                                                            '3.0-3.9': '03.0-03.9',
                                                            '4.0-4.9': '04.0-04.9',
                                                            '5.0-6.9': '05.0-06.9',
                                                            '7.0-8.9': '07.0-08.9',
                                                            '9.0-10.9': '09.0-10.9'})

# sort the table
tableSouth = tableSouth.sort_values(['statecd', 'unitcd', 'priceRegion',
                                    'spcd', 'spgrpcd', 'spclass', 'product', 'sizerange'])

# add spname to tableSouth
tableSouth = pd.merge(tableSouth, crosswalk, on='spcd', how='left')

columnOrder = ['stateAbbr', 'statecd', 'unitcd', 'priceRegion', 'spcd', 'spname',
               'spgrpcd', 'spclass', 'product', 'sizerange',
                'volume', 'value']

tableSouth = tableSouth[columnOrder]
                                                           
# save tableSouth
tableSouth.to_csv('../data/tableSouthMerch.csv', index=False)
# Aggregate to Premerch/Pulpwood/Sawtimber

# slice pwTable for Product = 'Pulpwood'
pwTable = tableSouth[(tableSouth['product'] == 'Pulpwood') |
                      (tableSouth['product'] == 'Pre-merchantable')]

# drop columns from pwTable
pwTable = pwTable[['stateAbbr', 'spname', 'spclass', 'volume', 'value']]

# rename columns
pwTable.rename(columns={'spname': 'species',
                        'volume': 'pwVolume',
                        'value': 'pwValue'}, inplace=True)

# reduce pwTable to the sum of pwVolume and pwValue by statecd, spclass, species
pwTable = pwTable.groupby(['stateAbbr', 'spclass', 'species']).agg({
    'pwVolume': 'sum',
    'pwValue': 'sum'
}).reset_index()

# if product is sawtimber, save to stTable
stTable = tableSouth[tableSouth['product'] == 'Sawtimber']

# drop columns from stTable
stTable = stTable[['stateAbbr', 'spname', 'spclass', 'sizerange', 'volume', 'value']]

# rename columns
stTable.rename(columns={'spname': 'species',
                        'volume': 'stVolume',
                        'value': 'stValue'}, inplace=True)

# reduce stTable to the sum of stVolume and stValue by statecd, spclass, species
stTable = stTable.groupby(['stateAbbr', 'spclass', 'species']).agg({
    'stVolume': 'sum',
    'stValue': 'sum'
}).reset_index()

# merge tables pwTable and stTable
table = pd.merge(pwTable, stTable, on=['stateAbbr', 'spclass', 'species'], how='outer')

# save as tableByProduct
table.to_csv('../data/tableSouthByProduct.csv', index=False)