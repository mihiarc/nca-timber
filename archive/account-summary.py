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

# ## Timber Regions

# In[4]:


# draw a map of the counties with reported stumpage prices
# use cartopy to draw the map

import geopandas as gpd
import matplotlib.pyplot as plt

# define the states included in the pilots as pilotStates; use state_abbr
pilotStates = ['MI', 'MN', 'WI', 'TX', 'LA', 'MS',
                'AL', 'FL', 'GA', 'SC', 'NC', 'VA', 'TN', 'AR']


# Load the shapefiles locally
# statesPath = '/Users/mihiarc/Work/spatial-boundaries/tl_2023_us_state/tl_2023_us_state.shp'
# states = gpd.read_file(statesPath)

# filter the states and counties to only include the pilot states
# states = states[states['STUSPS'].isin(pilotStates)]

# # Change the CRS to Albers Equal Area
# albers_crs = 'EPSG:5070'
# states = states.to_crs(albers_crs)

# # Plot the filtered states
# fig, ax = plt.subplots(figsize=(15, 10))
# states.plot(ax=ax, edgecolor='black', facecolor='none')

# # Set plot title
# plt.title('Pilot States for Timber Asset Account')

# # Show the plot
# plt.show()


# ## Timber Species
# 
# | FIA Code | Timber Species | Family | Market |
# |:---:|:-----|--------|:----------------------|
# | 012 | Balsim Fir | Pine | Great Lakes |
# | 068 | eastern redcedar | Cypress | Great Lakes, South |
# | 071 | tamarack | Pine | Great Lakes |
# | 091 | Norway spruce | Pine | Great Lakes |
# | 094 | white spruce | Pine | Great Lakes |
# | 095 | black spruce | Pine | Great Lakes |
# | 105 | jack pine | Pine |Great Lakes |
# | 110 | shortleaf pine | Pine | South |
# | 111 | slash pine | Pine | South |
# | 121 | longleaf pine | Pine | South |
# | 125 | red pine | Pine | Great Lakes |
# | 126 | pitch pine | Pine | Great Lakes |
# | 129 | eastern white pine | Pine | Great Lakes, South |
# | 130 | Scotch (Scots) pine | Pine | Great Lakes |
# | 131 | loblolly pine | Pine | South |
# | 132 | Virginia pine | Pine | South |
# | 221 | baldcypress | Cypress | South |
# | 313 | boxelder | Maple | Great Lakes |
# | 314 | black maple | Maple | Great Lakes, South |
# | 316 | red maple | Maple | Great Lakes                                       
# | 318 | sugar maple | Maple | Great Lakes, South |
# | 371 | yellow birch | Birch | Great Lakes |
# | 375 | paper birch | Birch | Great Lakes |
# | 409 | mockernut hickory | Walnut | South |
# | 402 | bitternut hickory | Walnut | Great Lakes, South |
# | 403 | pignut hickory | Walnut | South |
# | 404 | pecan | Walnut | South |
# | 405 | shelbark hickory | Walnut | South |
# | 407 | shagbark hickory | Walnut | South |
# | 462 | hackberry | Elm | Great Lakes |
# | 531 | American beech | Beech | Great Lakes |
# | 541 | white ash | Olive | Great Lakes, South |
# | 543 | black ash | Olive | Great Lakes |
# | 544 | green ash | Olive | Great Lakes, South |
# | 546 | blue ash | Olive | Great lakes, South |
# | 601 | butternut | Walnut | South |
# | 602 | black walnut | Walnut | Great Lakes, South |
# | 611 | sweetgum | Witch-hazel | South |
# | 621 | yellow-poplar | Magnolia | South |
# | 651 | cucubertree | Magnolia | South |
# | 652 | southern magnolia | Magnolia | South |
# | 653 | sweetbay | Magnolia | South |
# | 742 | eastern cottonwood | Willow | Great Lakes |
# | 743 | bigtooth aspen | Willow | Great Lakes |
# | 746 | quaking aspen | Willow | Great lakes |
# | 762 | black cherry | Rose | Great Lakes, South |
# | 802 | white oak | Beech | Great Lakes, South |
# | 804 | swamp white oak | Beech | Great Lakes, South |
# | 809 | northern pin oak | Beech | Great Lakes |
# | 812 | southern red oak | Beech | South |
# | 822 | overcup oak | Beech | South |
# | 823 | bur oak | Beech | Great Lakes, South |
# | 826 | chinkapin oak | Beech | Great Lakes |
# | 830 | pin oak | Beech | South |
# | 832 | chestnut oak | Beech | South |
# | 833 | northern red oak | Beech | Great Lakes |
# | 837 | black oak | Beech | Great Lakes, South |
# | 951 | American basswood | Linden | Great Lakes |
# | 972 | American elm | Elm | Great Lakes |
# | 977 | rock elm | Elm | Great Lakes |
# 

# ## Size Class
# 
# * In the southern U.S. diameter class include non-merchantable (pine only) (1"-4.9"), pulpwood (5"-11.9"), and sawtimber (12"+).
# * The great lakes diameter classes differ only across large trees, either standard sawtimber size (20 - 30") or veneer size (30"+).

# # Southern Timber Asset Accounts

# In[5]:


# summarize southern premerch data
tableSouth = pd.read_csv('../data/tableSouthMerch.csv')

# add species names and species group names
species = pd.read_csv('../data/speciesDict.csv')
speciesGroup = pd.read_csv('../data/speciesGroupDict.csv')

tableSouth = pd.merge(tableSouth, species, on='spcd')
tableSouth = pd.merge(tableSouth, speciesGroup, on='spgrpcd')
tableSouth = tableSouth.replace({'spclass': {'Softwood': 'Coniferous',
                                              'Hardwood': 'Non-coniferous'}})

# scale to billions of dollars
tableSouth['value'] = tableSouth['value'] / 1e9
# convert to cubic feet to megatonnes
tableSouth['volume'] = tableSouth['volume'] * 0.025713 / 1e6


# # South Table 1
# 
# ### Physical Table: Opening Stock 2021

# In[9]:


# reduce value and volume across space
southTable1 = tableSouth[tableSouth['product'] != 'Pre-merchantable']
southTable1 = southTable1.groupby(['spclass', 'product']).agg(
                    {'volume': 'sum'}).reset_index()

southTable1 = southTable1.pivot(index='spclass',
                                columns='product',
                                values='volume').reset_index()
southTable1 = southTable1.sort_values('spclass', ascending=True)

# Set the index to the Species column for easier display
southTable1.set_index('spclass', inplace=True)
southTable1 = southTable1.style.set_caption("Biomass Volume by Timber Species Class") \
                    .format("{:,.0f} Mt", na_rep='-')
html = southTable1.to_html()
from IPython.display import HTML
HTML(html)

# In[10]:


# reduce value and volume across space
southTable2 = tableSouth[tableSouth['product'] != 'Pre-merchantable']
southTable2 = southTable2.groupby(['spclass', 'product']).agg(
                    {'value': 'sum'}).reset_index()

southTable2 = southTable2.pivot(index='spclass',
                                columns='product',
                                values='value').reset_index()
southTable2 = southTable2.sort_values('spclass', ascending=True)

# Set the index to the Species column for easier display
southTable2.set_index('spclass', inplace=True)
southTable2 = southTable2.style.set_caption("Value ($) by Timber Species Class\n(in billions)") \
                    .format("${:,.0f}", na_rep='-')
html = southTable2.to_html()
from IPython.display import HTML
HTML(html)

# In[11]:


# reduce value and volume across space
southTable3 = tableSouth[tableSouth['product'] != 'Pre-merchantable']
southTable3 = southTable3.groupby(['speciesGroup', 'product']).agg(
                    {'volume': 'sum'}).reset_index()

southTable3 = southTable3.pivot(index='speciesGroup',
                                columns='product',
                                values='volume').reset_index()
southTable3 = southTable3.sort_values('Sawtimber', ascending=False)
# Set the index to the Species column for easier display
southTable3.set_index('speciesGroup', inplace=True)
southTable3 = southTable3.style.set_caption("Biomass Volume by Timber Species Class") \
                    .format("{:,.0f} Mt", na_rep='-')
html = southTable3.to_html()
from IPython.display import HTML
HTML(html)


# In[12]:


# reduce value and volume across space
southTable4 = tableSouth[tableSouth['product'] != 'Pre-merchantable']
southTable4 = southTable4.groupby(['spclass', 'speciesGroup', 'product']).agg(
                    {'value': 'sum'}).reset_index()
southTable4 = southTable4.sort_values(by='value', ascending=False)
southTable4


southTable4 = southTable4.pivot(index=['spclass', 'speciesGroup'],
                                columns='product',
                                values='value').reset_index()

southTable4 = southTable4.sort_values(by=['spclass', 'speciesGroup'],
                                       ascending=False)
# Set the index to the Species column for easier display
southTable4.set_index(['spclass', 'speciesGroup'], inplace=True)
southTable4 = southTable4.style.set_caption("Value ($) by Timber Species Group\n(in billions)") \
                    .format("$  {:,.0f}", na_rep='-')
html = southTable4.to_html()
from IPython.display import HTML
HTML(html)

# In[39]:


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

figureSouth1 = tableSouth[tableSouth['product'] != 'Pre-merchantable']
figureSouth1 = figureSouth1[figureSouth1['spclass'] == 'Coniferous']
figureSouth1 = figureSouth1.groupby(['spclass', 'sizerange', 'product']).agg(
                    {'volume': 'sum'}).reset_index()

figureSouth2 = tableSouth[tableSouth['product'] != 'Pre-merchantable']
figureSouth2 = figureSouth2[figureSouth2['spclass'] == 'Coniferous']
figureSouth2 = figureSouth2.groupby(['spclass', 'sizerange', 'product']).agg(
                    {'value': 'sum'}).reset_index()

color_mapping = {
    'Coniferous Pulpwood': 'limegreen',
    'Non-coniferous Pulpwood': 'lightcoral',
    'Coniferous Sawtimber': 'forestgreen',
    'Non-coniferous Sawtimber': 'purple'
}

# Create a figure and axis
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 8))

# Iterate over species and product to plot the histogram
for species in figureSouth1['spclass'].unique():
    for product in figureSouth1['product'].unique():
        # Filter the data based on species and product
        data = figureSouth1.loc[(figureSouth1['spclass'] == species) &
                                (figureSouth1['product'] == product)]
        color = color_mapping.get(f'{species} {product}', 'gray')
        # Plot the bar for each species and product combination
        ax1.bar(data['sizerange'],
               data['volume'],
               label=f'{species} {product}',
               color=color)

# Specify the x labels
xlabs = ['5.0-6.9', '7.0-8.9', '9.0-10.9', '11.0-12.9',
         '13.0-14.9', '15.0-16.9', '17.0-18.9', '19.0-20.9',
         '21.0-22.9', '23.0-24.9', '25.0-26.9', '27.0-29.9']

# Set x-ticks and labels
ax1.set_xticks(range(len(xlabs)))
ax1.set_xticklabels(xlabs, rotation=75)

# Set title and labels
ax1.set_title('Biomass Volume of Timber by Product and Size Class')
ax1.set_xlabel('Size Class Range (inches)')
ax1.set_ylabel('Gigatonnes')
ax1.legend(title='Species and Product')

for species in figureSouth2['spclass'].unique():
    for product in figureSouth2['product'].unique():
        # Filter the data based on species and product
        data = figureSouth2.loc[(figureSouth2['spclass'] == species) &
                                (figureSouth2['product'] == product)]
        color = color_mapping.get(f'{species} {product}', 'gray')
        # Plot the bar for each species and product combination
        ax2.bar(data['sizerange'], data['value'],
                label=f'{species} {product}', color=color)

# Set x-ticks and labels
ax2.set_xticks(range(len(xlabs)))
ax2.set_xticklabels(xlabs, rotation=75)

# Set title and labels
ax2.set_title('Value of Timber by Product and Size Class')
ax2.set_xlabel('Size Class Range (inches)')
ax2.set_ylabel('Billions of Dollars')
ax2.legend(title='Species and Product')

# Display the plot
plt.tight_layout()
plt.show()

# In[41]:


# plot a histogram
import matplotlib.pyplot as plt

figureSouth3 = tableSouth[tableSouth['product'] != 'Pre-merchantable']
figureSouth3 = figureSouth3[figureSouth3['spclass'] == 'Non-coniferous']
figureSouth3 = figureSouth3.groupby(['spclass', 'sizerange', 'product']).agg(
                    {'volume': 'sum'}).reset_index()

figureSouth4 = tableSouth[tableSouth['product'] != 'Pre-merchantable']
figureSouth4 = figureSouth4[figureSouth4['spclass'] == 'Non-coniferous']
figureSouth4 = figureSouth4.groupby(['spclass', 'sizerange', 'product']).agg(
                    {'value': 'sum'}).reset_index()

# create a figure and axis
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 8))

# Iterate over species and product to plot the histogram
for species in figureSouth3['spclass'].unique():
    for product in figureSouth3['product'].unique():
        # Filter the data based on species and product
        data = figureSouth3.loc[(figureSouth3['spclass'] == species) &
                                (figureSouth3['product'] == product)]
        color = color_mapping.get(f'{species} {product}', 'gray')
        # Plot the bar for each species and product combination
        ax1.bar(data['sizerange'],
               data['volume'],
               label=f'{species} {product}',
               color=color)

# set title and labels
ax1.set_title('Volume of Pre-Mertchantable Timber by Species and Size Class')
ax1.set_xlabel('Size Class Range (inches)')
ax1.set_ylabel('Volume (billions of cubic feet)')
ax1.legend()

for species in figureSouth4['spclass'].unique():
    for product in figureSouth4['product'].unique():
        # Filter the data based on species and product
        data = figureSouth4.loc[(figureSouth4['spclass'] == species) &
                                (figureSouth4['product'] == product)]
        color = color_mapping.get(f'{species} {product}', 'gray')
        # Plot the bar for each species and product combination
        ax2.bar(data['sizerange'], data['value'],
                label=f'{species} {product}', color=color)

# set title and labels
ax2.set_title('Value of Pre-Mertchantable Timber by Species and Size Class')
ax2.set_xlabel('Size Class Range (inches)')
ax2.set_ylabel('Value (billions of dollars)')
ax2.legend()

# specify the x labels
xlabs = ['1.0-1.9', '2.0-2.9', '3.0-3.9', '4.0-4.9',
         '5.0-6.9', '7.0-8.9', '9.0-10.9', '11.0-12.9',
          '13.0-14.9', '15.0-16.9', '17.0-18.9', '19.0-20.9',
            '21.0-22.9', '23.0-24.9', '25.0-26.9', '27.0-29.9',
            '30.0-32.9', '33.0-34.9', '35-36.9']

# display the plot
plt.setp(ax1.xaxis.get_majorticklabels(), rotation=75)
plt.setp(ax2.xaxis.get_majorticklabels(), rotation=75)
plt.tight_layout()
plt.show()

# In[13]:


# Summarize Great Lakes data
tableGL = pd.read_csv('../data/tableGL.csv')

# Add species names and species group names
species = pd.read_csv('../data/speciesDict.csv')
speciesGroup = pd.read_csv('../data/speciesGroupDict.csv')

tableGL = pd.merge(tableGL, species, on='spcd')
tableGL = pd.merge(tableGL, speciesGroup, on='spgrpcd')
tableGL = tableGL.replace({'spclass': {'Softwood': 'Coniferous', 'Hardwood': 'Non-coniferous'}})

# Scale to billions of dollars
tableGL['value'] = tableGL['value'] / 1e9
# Convert to cubic feet to megatonnes
tableGL['volume'] = tableGL['volume'] * 0.025713 / 1e6


# In[15]:



# Reduce value and volume across space
glTable1 = tableGL[tableGL['product'] != 'Pre-merchantable']
glTable1 = glTable1.groupby(['spclass', 'product']).agg({'volume': 'sum'}).reset_index()
glTable1 = glTable1.pivot(index='spclass', columns='product', values='volume').reset_index()
glTable1 = glTable1.sort_values('spclass', ascending=True)
glTable1.set_index('spclass', inplace=True)
glTable1 = glTable1.style.set_caption("Biomass Volume by Timber Species Class") \
                    .format("{:,.0f} Mt", na_rep='-')

html = glTable1.to_html()
from IPython.display import HTML
HTML(html)


# In[14]:



# Reduce value and volume across space
glTable2 = tableGL[tableGL['product'] != 'Pre-merchantable']
glTable2 = glTable2.groupby(['spclass', 'product']).agg({'value': 'sum'}).reset_index()
glTable2 = glTable2.pivot(index='spclass', columns='product', values='value').reset_index()
glTable2 = glTable2.sort_values('spclass', ascending=True)
glTable2.set_index('spclass', inplace=True)
glTable2 = glTable2.style.set_caption("Value ($) by Timber Species Class\n(in billions)") \
                    .format("{:,.0f} Bil($)", na_rep='-')
html = glTable2.to_html()
from IPython.display import HTML
HTML(html)


# In[16]:


# Reduce value and volume across space
glTable3 = tableGL[tableGL['product'] != 'Pre-merchantable']
glTable3 = glTable3.groupby(['speciesGroup', 'product']).agg({'volume': 'sum'}).reset_index()
glTable3 = glTable3.pivot(index='speciesGroup', columns='product', values='volume').reset_index()
glTable3 = glTable3.sort_values('Sawtimber', ascending=False)
glTable3.set_index('speciesGroup', inplace=True)
glTable3 = glTable3.style.set_caption("Biomass Volume by Timber Species Class") \
                    .format("{:,.0f} Mt", na_rep='-')
html = glTable3.to_html()
from IPython.display import HTML
HTML(html)


# In[17]:


import numpy as np
# Reduce value and volume across space
glTable4 = tableGL[tableGL['product'] != 'Pre-merchantable']
glTable4 = glTable4.groupby(['spclass', 'speciesGroup', 'product']).agg({'value': 'sum'}).reset_index()
glTable4 = glTable4.sort_values(by='value', ascending=False)
glTable4 = glTable4.pivot(index=['spclass', 'speciesGroup'], columns='product', values='value').reset_index()
glTable4 = glTable4.sort_values(by=['spclass', 'speciesGroup'], ascending=False)
glTable4 = glTable4.replace(0, np.nan)
glTable4.set_index(['spclass', 'speciesGroup'], inplace=True)
glTable4 = glTable4.style.set_caption("Value ($) by Timber Species Group\n(in billions)") \
                    .format("{:,.0f} Bil($)", na_rep='-')
html = glTable4.to_html()
from IPython.display import HTML
HTML(html)


# In[49]:


# Plot figures
figureGL1 = tableGL[tableGL['product'] != 'Pre-merchantable']
figureGL1 = figureGL1[figureGL1['spclass'] == 'Coniferous']
figureGL1 = figureGL1.groupby(['spclass', 'sizerange', 'product']).agg({'volume': 'sum'}).reset_index()

figureGL2 = tableGL[tableGL['product'] != 'Pre-merchantable']
figureGL2 = figureGL2[figureGL2['spclass'] == 'Coniferous']
figureGL2 = figureGL2.groupby(['spclass', 'sizerange', 'product']).agg({'value': 'sum'}).reset_index()

# Create a figure and axis
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 8))

# Iterate over species and product to plot the histogram
for species in figureGL1['spclass'].unique():
    for product in figureGL1['product'].unique():
        data = figureGL1.loc[(figureGL1['spclass'] == species) & (figureGL1['product'] == product)]
        color = color_mapping.get(f'{species} {product}', 'gray')
        ax1.bar(data['sizerange'], data['volume'], label=f'{species} {product}', color=color)

# specify the x labels
xlabs = ['1.0-1.9', '2.0-2.9', '3.0-3.9', '4.0-4.9',
         '5.0-6.9', '7.0-8.9', '9.0-10.9', '11.0-12.9',
          '13.0-14.9', '15.0-16.9', '17.0-18.9', '19.0-20.9']

# Set x-ticks and labels
ax1.set_xticks(range(len(xlabs)))
ax1.set_xticklabels(xlabs, rotation=75)
ax1.set_title('Biomass Volume of Timber by Product and Size Class')
ax1.set_xlabel('Size Class Range (inches)')
ax1.set_ylabel('Gigatonnes')
ax1.legend(title='Species and Product')

for species in figureGL2['spclass'].unique():
    for product in figureGL2['product'].unique():
        data = figureGL2.loc[(figureGL2['spclass'] == species) & (figureGL2['product'] == product)]
        color = color_mapping.get(f'{species} {product}', 'gray')
        ax2.bar(data['sizerange'], data['value'], label=f'{species} {product}', color=color)

ax2.set_xticks(range(len(xlabs)))
ax2.set_xticklabels(xlabs, rotation=75)
ax2.set_title('Value of Timber by Product and Size Class')
ax2.set_xlabel('Size Class Range (inches)')
ax2.set_ylabel('Billions of Dollars')
ax2.legend(title='Species and Product')

plt.tight_layout()
plt.show()

# In[18]:


# appendix
# full table that includes physical and monetary for all products by species
table = pd.concat([tableGL, tableSouth])


# In[ ]:


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

# In[6]:



# group by priceSpecies and product and use agg() to get summary statistics
# round to two decimal places
# sort by size_class_range
summarySouth = dfSouth.groupby(
    ['spclass', 'Product', 'size_class_code', 'size_class_range']
    ).agg({
    'volume': 'sum',
    'value': 'sum'
})

# Convert volume and value to billions
summarySouth['volume'] = summarySouth['volume'] / 1000000000
summarySouth['value'] = summarySouth['value'] / 1000000000

# Round to two decimal places
summarySouth = summarySouth.round(2)

# Sort by priceSpecies, Product, and size_class_code
summarySouth = summarySouth.sort_values(by=['spclass', 'Product', 'size_class_code'])

# Display the summary statistics
summarySouth

# In[ ]:


# maps

# import geopandas as gpd
# import matplotlib.pyplot as plt
# import pandas as pd

# # Define pilot states
# pilotStates = ['AL', 'AR', 'FL', 'GA', 'LA',
#                'MS', 'NC', 'OK', 'SC', 'TN',
#                'TX', 'VA']

# # Load the shapefile locally
# shapefile_path = '/Users/mihiarc/Work/spatial-boundaries/tl_2023_us_state/tl_2023_us_state.shp'
# states = gpd.read_file(shapefile_path)

# # Filter the states shapefile to only include the pilot states
# states = states[states['STUSPS'].isin(pilotStates)]


# # Change the CRS to Albers Equal Area
# albers_crs = 'EPSG:5070'
# states = states.to_crs(albers_crs)


# # prepare the pine data for mapping
# # group by stateAbbr and sum the value
# timberValue = tableSouth.groupby('stateAbbr')['value'].sum().reset_index()

# # divide the value by 1 billion
# timberValue['value'] = timberValue['value'] / 1000000000

# # sort by value
# timberValue = timberValue.sort_values('value', ascending=False)

# # print the timberValue table; round to 2 decimal places
# print(f"Total Southern Timber Value by State (in billions):\n{timberValue.round(2)}")


# In[ ]:


# # Merge the GeoDataFrame with the pine timber volume DataFrame
# # rename stateAbbr to STUSPS to match the states GeoDataFrame
# timberValue.rename(columns={'stateAbbr': 'STUSPS'}, inplace=True)
# states = states.merge(timberValue, on='STUSPS')


# # Plot the choropleth map
# fig, ax = plt.subplots(figsize=(15, 10))
# states.plot(column='value', ax=ax, legend=True,
#             legend_kwds={'label': "Southern Timber Value ($)",
#                          'orientation': "horizontal"},
#             cmap='GnBu', edgecolor='black')

# # # Set plot title
# plt.title('Timber Value Across Southern Pilot States')

# # # Show the plot
# plt.show()
