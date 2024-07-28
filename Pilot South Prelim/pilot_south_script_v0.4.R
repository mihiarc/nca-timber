# create pilot tables for southern pine

library(tidyverse)
library(pivottabler)

# load data----

setwd("C:/Users/cmihiar/OneDrive - USDA/(DUKE) Natural Capital/NCA Timber Account")
# setwd("E:/OneDrive - USDA/NCA Timber Account/Pilot South")

# prices are in per ton units
prices <- read.csv('Pilot South/Georgia stumpage prices.csv')
quantity <- read.csv('Pilot South/Georgia FIA example.csv')

merch <- read.csv('FIA Data/Merch bio.csv')
premerch <- read.csv('FIA Data/Premerch bio.csv')

# clean and merge data----

p <- prices %>%
  mutate(pm1p = plpp / 1.05^8,
         pm2p = plpp / 1.05^6,
         pm3p = plpp / 1.05^4,
         pm4p = plpp / 1.05^2,
         pm1h = plph / 1.05^8,
         pm2h = plph / 1.05^6,
         pm3h = plph / 1.05^4,
         pm4h = plph / 1.05^2) %>%
  pivot_longer(cols = c(5:18), values_to = "price") %>%
  mutate(product = substr(name, 1, 3),
         type = substr(name, 4, 4)) %>%
  select(-name) %>%
  group_by(year, product, state, type) %>%
  summarize(price = mean(price, na.rm = T), .groups = "drop") %>%
  mutate(type = recode(type, 'p' = 'Softwood',
                       'h' = 'Hardwood',
                       'm' = 'Mixed'),
         PRODUCT = product,
         SPCLASS = type,
         PRICE = price) %>%
  filter(product != "cns", type != "Mixed", year == 2021) %>%
  select(PRODUCT, SPCLASS, PRICE)

pm <- premerch
names(pm) <- c("STATENM", "STATECD", "COUNTYNM", "COUNTYCD", "SPGRPCD",
               "SPGRPNM", "SPCLASS", "UNITCD", "RESERVCD", "EVALID",
               "PM1", "PM2", "PM3", "PM4")
mc <- merch
names(mc) <- c("STATENM", "STATECD", "COUNTYNM", "COUNTYCD", "SPGRPCD",
               "SPGRPNM", "SPCLASS", "UNITCD", "RESERVCD", "EVALID",
               "PW1","PW2","PW3",
               "ST01","ST02","ST03","ST04","ST05","ST06", "ST07","ST08",
               "ST09","ST10","ST11","ST12","ST13","ST14","ST15","ST16")

szcd <- data.frame(SZCLASS = c("PM1","PM2","PM3","PM4",
                               "PW1","PW2","PW3",
                               "ST01","ST02","ST03","ST04","ST05",
                               "ST06", "ST07","ST08",
                               "ST09","ST10","ST11","ST12","ST13",
                               "ST14","ST15","ST16"),
                   PRODUCT = c("pm1","pm2","pm3","pm4",
                               "plp","plp","plp",
                               "saw","saw","saw","saw","saw","saw",
                               "saw","saw","saw","saw","saw","saw",
                               "saw","saw","saw","saw"))

pm <- pm %>%
  filter(RESERVCD == 1) %>%
  pivot_longer(cols = 11:14, names_to = 'SZCLASS') %>%
  group_by(SPCLASS, SZCLASS) %>%
  summarize(biomass = sum(value, na.rm = T), .groups = 'drop') %>%
  left_join(szcd, by = 'SZCLASS') %>%
  left_join(p, by = c("PRODUCT", "SPCLASS")) %>%
  mutate(value = (biomass * PRICE))

mc <- mc %>%
  filter(RESERVCD == 1) %>%
  pivot_longer(cols = 11:29, names_to = 'SZCLASS') %>%
  group_by(SPCLASS, SZCLASS) %>%
  summarize(biomass = sum(value, na.rm = T), .groups = 'drop') %>%
  left_join(szcd, by = 'SZCLASS') %>%
  left_join(p, by = c("PRODUCT", "SPCLASS")) %>%
  mutate(value = (biomass * PRICE))

total.value.ga <- rbind(pm,mc)
sum(total.value.ga$value)/1000000000 #total value in billions
#total value of hardwood stock
sum(total.value.ga$value[total.value.ga$SPCLASS=="Hardwood"])/1000000000
#total value of hardwood stock in sawtimber classses
sum(total.value.ga$value[total.value.ga$SPCLASS=="Hardwood" & 
                           total.value.ga$SZCLASS %in% c("ST01","ST02","ST03","ST04","ST05",
                                                         "ST06", "ST07","ST08",
                                                         "ST09","ST10","ST11","ST12","ST13",
                                                         "ST14","ST15","ST16")])/1000000000
#total value of hardwood stock in pulpwood classes
sum(total.value.ga$value[total.value.ga$SPCLASS=="Hardwood" & 
                           total.value.ga$SZCLASS %in% c("PW1","PW2","PW3")])/1000000000
#total value of hardwood stock in premerch classes
sum(total.value.ga$value[total.value.ga$SPCLASS=="Hardwood" & 
                           total.value.ga$SZCLASS %in% c("PM1","PM2","PM3","PM4")])/1000000000

#total value of softwood stock
sum(total.value.ga$value[total.value.ga$SPCLASS=="Softwood"])/1000000000
#total value of softwood stock in sawtimber classses
sum(total.value.ga$value[total.value.ga$SPCLASS=="Softwood" & 
                           total.value.ga$SZCLASS %in% c("ST01","ST02","ST03","ST04","ST05",
                                                         "ST06", "ST07","ST08",
                                                         "ST09","ST10","ST11","ST12","ST13",
                                                         "ST14","ST15","ST16")])/1000000000
#total value of softwood stock in pulpwood classes
sum(total.value.ga$value[total.value.ga$SPCLASS=="Softwood" & 
                           total.value.ga$SZCLASS %in% c("PW1","PW2","PW3")])/1000000000
#total value of softwood stock in premerch classes
sum(total.value.ga$value[total.value.ga$SPCLASS=="Softwood" & 
                           total.value.ga$SZCLASS %in% c("PM1","PM2","PM3","PM4")])/1000000000


# p <- prices %>%
#   pivot_longer(cols = c(4:69), values_to = "price_raw") %>%
#   mutate(product = substr(name, 1, 3),
#          state = substr(name, 4, 5),
#          region = as.integer(substr(name, 6, 6))) %>%
#   select(-name) %>%
#   filter(state == 'ga') %>%
#   group_by(year, product, state, type) %>%
#   summarize(price_scrib = mean(price_raw, na.rm = T), .groups = "drop") %>%
#   mutate(price_tons = case_when(product == 'saw' ~ price_scrib / 7,
#                                 product == 'plp' ~ price_scrib / 8,
#                                 product == 'pre' ~ price_scrib / 8))

# p <- prices %>%
#   mutate(prep = 0, preh = 0) %>%
#   pivot_longer(cols = c(5:12), values_to = "price") %>%
#   mutate(product = substr(name, 1, 3),
#          type = substr(name, 4, 4)) %>%
#   select(-name) %>%
#   group_by(year, product, state, type) %>%
#   summarize(price = mean(price, na.rm = T), .groups = "drop") %>%
#   mutate(type = recode(type, 'p' = 'Pines',
#                        'h' = 'Oaks',
#                        'm' = 'Other hardwoods')) %>%
#   filter(product != "cns")

q <- quantity %>%
  rename(pre = GAGB_le_6,
         plp = GAGB_6_12,
         saw = GAGB_12,
         type = spgrp2) %>%
  pivot_longer(cols = c(3:6), names_to = 'product', values_to = 'tons') %>%
  filter(type %in% c("Oaks", "Pines", "Other hardwoods"),
         !product == "GAGB_total") %>%
  mutate(state = "ga")

df <- full_join(p, q, by = c("year", "state", "type", "product")) %>%
  mutate(product_name = recode(product,
                          'pre' = 'Pre-Merchantable (<6"DBH)',
                          'plp' = 'Pulpwood (6\" - 11.9")',
                          'saw' = 'Sawtimber (12\" and up)'),
         state = recode(state,
                        'ga' = 'Georgia'),
         value = price * tons) %>%
  filter(year >= 2014,
         type != "Other hardwoods")

# trend figures----

ggplot(filter(df, product == "plp")) +
  geom_line(aes(x=year, y=tons, color = type))

# custom override functions----

getLastYearFilter <- function(pt, filters, cell) {
  # get the date filter
  filter <- filters$getFilter("year")
  if(is.null(filter)||(filter$type=="ALL")||(length(filter$values)>1)) {
    # there is no filter on year in this cell
    # i.e. we are in one of the total cells that covers all dates,
    # so the concept of last year has no meaning, so block all dates
    newFilter <- PivotFilter$new(pt, variableName="year", type="NONE")
    filters$setFilter(newFilter, action="replace")
  }
  else {
    # get the date value and subtract one year
    date <- filter$values
    date <- date - 1
    filter$values <- date
  }
}

# create tables----

# tables nov28----

st <- 'Georgia'
tp <- c(2018,2019)
ft <- 'Pines'
sc <- 'saw'

df.table <- filter(df,
                   year %in% tp,
                   state == st,
                   product == sc,
                   type == ft)

pt <- PivotTable$new()
pt$addData(df.table)
# pt$addColumnDataGroups("state",
#                         addTotal = F)
pt$addRowDataGroups("year", addTotal = F)
filterOverrides <- PivotFilterOverrides$new(pt,
                                            overrideFunction = 
                                              getLastYearFilter)
pt$defineCalculation(calculationName="OpeningStock", filters=filterOverrides, 
                      summariseExpression="sum(tons, na.rm=T) / 1000000",
                      caption="Opening Stock",
                      format="%.1f")
pt$defineCalculation(calculationName="NetChangeStock", type="calculation", 
                      basedOn=c("ClosingStock", "OpeningStock"),
                      calculationExpression="values$ClosingStock-values$OpeningStock", 
                      caption="Net Change in Stock",
                      format="%.1f")
pt$defineCalculation(calculationName = "ClosingStock",
                      caption = "Closing Stock",
                      summariseExpression = "sum(tons, na.rm=T) / 1000000",
                      format="%.1f")
pt$addRowCalculationGroups()
pt$theme <- "largeplain"
pt$renderPivot(styleNamePrefix="t2")
pt$renderPivot()

# table pilot v.02----

pt <- PivotTable$new()
pt$addData(df)
#add columns
pt$addColumnDataGroups("state", addTotal = F)
pt$addColumnDataGroups("type", addTotal = F)
#add rows
pt$addRowDataGroups("year", addTotal = F)
#growing stock
pt$defineCalculation(calculationName = "GrowingStock",
                     caption = "Growing Stock",
                     summariseExpression = "sum(tons, na.rm=T) / 1000000",
                     format="%.1f")
#price
pt$defineCalculation(calculationName="Price",
                     caption = "Price per ton",
                     summariseExpression = "mean(price, na.rm=T)",
                     format=list(digits = 2, big.mark = ','))
#value
pt$defineCalculation(calculationName="Value",
                     caption = "Value",
                     summariseExpression = "sum(value, na.rm=T) / 1000000",
                     format=list(digits = 2, big.mark = ','))


pt$addRowCalculationGroups()
pt$theme <- "largeplain"
pt$renderPivot(styleNamePrefix="t2")

# pt$evaluatePivot()
# pt$removeRows(rowNumbers=c(4))

pt$renderPivot()

# pt$renderPivot(includeHeaderValues=TRUE, includeRCFilters=TRUE)

# table pilot v.01----


pt <- PivotTable$new()
pt$addData(df)
#add columns
pt$addColumnDataGroups("state", addTotal = F)
pt$addColumnDataGroups("type", addTotal = F)

#add rows

pt$addColumnDataGroups("product", dataSortOrder = "custom",
                       customSortOrder = c('Pre-Merchantable (<6"DBH)',
                                           'Pulpwood (6\" - 11.9")',
                                           'Sawtimber (12\" and up)'),
                       addTotal = F)
#define stock metrics
filterOverrides <- PivotFilterOverrides$new(pt,
                                            overrideFunction =
                                              getLastYearFilter)
pt$defineCalculation(calculationName="OpeningStock", filters=filterOverrides,
                      summariseExpression="sum(tons, na.rm=T) / 1000000",
                      caption="Opening Growing Stock",
                      format="%.1f")
pt$defineCalculation(calculationName="NetChangeStock", type="calculation",
                      basedOn=c("ClosingStock", "OpeningStock"),
                      calculationExpression="values$ClosingStock-values$OpeningStock",
                      caption="Net Change in Stock",
                      format="%.1f")
pt$defineCalculation(calculationName = "ClosingStock",
                      caption = "Closing Stock",
                      summariseExpression = "sum(tons, na.rm=T) / 1000000",
                      format="%.1f")
#define value metrics
# pt$defineCalculation(calculationName="OpeningValue", filters=filterOverrides, 
#                       summariseExpression="sum(value, na.rm=T) / 1000000",
#                       caption="Opening Value (millions)",
#                       format=list(digits = 2, big.mark = ','))
# pt$defineCalculation(calculationName="NetChangeValue", type="calculation", 
#                      caption = "Net Change in Value",
#                      basedOn=c("ClosingValue", "OpeningValue"),
#                      calculationExpression="values$ClosingValue-values$OpeningValue", 
#                      format=list(digits = 2, big.mark = ','))
# pt$defineCalculation(calculationName = "ClosingValue",
#                       caption = "Closing Value",
#                       summariseExpression = "sum(value, na.rm=T) / 1000000",
#                       format=list(digits = 2, big.mark = ','))
# 
# 

#render table
pt$addRowDataGroups("year", addTotal = F)
pt$addRowCalculationGroups()
pt$evaluatePivot()
pt$removeRows(rowNumbers=c(1,2,3))
pt$theme <- "largeplain"
pt$renderPivot(styleNamePrefix="t2")

# pilot table v.03----
pt <- PivotTable$new()
pt$addData(df)
#add columns
pt$addColumnDataGroups("state", addTotal = F)
pt$addColumnDataGroups("type", addTotal = T)

#add rows

pt$addColumnDataGroups("product", dataSortOrder = "custom",
                       customSortOrder = c('Pre-Merchantable (<6"DBH)',
                                           'Pulpwood (6\" - 11.9")',
                                           'Sawtimber (12\" and up)'),
                       addTotal = F)

#define value metrics
pt$defineCalculation(calculationName="OpeningValue", filters=filterOverrides,
                      summariseExpression="sum(value, na.rm=T) / 1000000",
                      caption="Opening Value (millions)",
                      format=list(digits = 2, big.mark = ','))
pt$defineCalculation(calculationName="NetChangeValue", type="calculation",
                     caption = "Net Change in Value",
                     basedOn=c("ClosingValue", "OpeningValue"),
                     calculationExpression="values$ClosingValue-values$OpeningValue",
                     format=list(digits = 2, big.mark = ','))
pt$defineCalculation(calculationName = "ClosingValue",
                      caption = "Closing Value",
                      summariseExpression = "sum(value, na.rm=T) / 1000000",
                      format=list(digits = 2, big.mark = ','))



#render table
pt$addRowDataGroups("year", addTotal = F)
pt$addRowCalculationGroups()
pt$evaluatePivot()
pt$removeRows(rowNumbers=c(1,2,3))
pt$removeColumns(columnNumbers = c(1,4))
pt$theme <- "largeplain"
pt$renderPivot(styleNamePrefix="t2")

# table 1: GA Pine, all years----
pt1 <- PivotTable$new()
pt1$addData(df)
pt1$addColumnDataGroups("state", addTotal = F)
pt1$addColumnDataGroups("product", dataSortOrder = "custom",
                       customSortOrder = c('Pre-Merchantable (<6"DBH)',
                                           'Pulpwood (6\" - 11.9")',
                                           'Sawtimber (12\" and up)'),
                       addTotal = T)
pt1$addRowDataGroups("type",
                        addTotal = F)
pt1$addRowDataGroups("year",
                    addTotal = F)
pt1$defineCalculation(calculationName = "tons",
                     caption = "Green Tons (millions)",
                     summariseExpression = "sum(tons, na.rm=T) / 1000000",
                     format="%.0f")
pt1$defineCalculation(calculationName = "price",
                     caption = "Price Per Ton",
                     summariseExpression = "mean(price, na.rm=T)",
                     format="$%.2f")
pt1$defineCalculation(calculationName = "value",
                     caption = "Value (millions)",
                     type = "calculation",
                     basedOn = c("price", "tons"),
                     format=list(digits = 2, big.mark = ','),
                     calculationExpression = "(values$price * values$tons)")
pt$theme <- "largeplain"
pt$renderPivot(styleNamePrefix="t2")
pt1$renderPivot()

# table 2: GA Pine Biomass (Green Tons), NCA format----

pt2 <- PivotTable$new()
pt2$addData(df)
pt2$addColumnDataGroups("state",
                       addTotal = F)
pt2$addColumnDataGroups("product", dataSortOrder = "custom",
                       customSortOrder = c('Pre-Merchantable (<6"DBH)',
                                           'Pulpwood (6\" - 11.9")',
                                           'Sawtimber (12\" and up)'),
                       addTotal = T)
pt2$addRowDataGroups("type",
                     addTotal = F)
pt2$addRowDataGroups("year",
                    addTotal = F)
filterOverrides <- PivotFilterOverrides$new(pt2,
                                            overrideFunction = 
                                              getLastYearFilter)
pt2$defineCalculation(calculationName="OpeningStock", filters=filterOverrides, 
                     summariseExpression="sum(tons, na.rm=T) / 1000000",
                     caption="Opening Stock",
                     format="%.1f")
pt2$defineCalculation(calculationName="NetChangeStock", type="calculation", 
                     basedOn=c("ClosingStock", "OpeningStock"),
                     calculationExpression="values$ClosingStock-values$OpeningStock", 
                     caption="Net Change in Stock",
                     format="%.1f")
pt2$defineCalculation(calculationName = "ClosingStock",
                     caption = "Closing Stock",
                     summariseExpression = "sum(tons, na.rm=T) / 1000000",
                     format="%.1f")
pt2$theme <- "largeplain"
pt2$renderPivot(styleNamePrefix="t2")
pt2$renderPivot()

# table 3: GA Pine Value, NCA format----

pt3 <- PivotTable$new()
pt3$addData(filter(df, !product == "Pre-Merchantable (<6\"DBH)"))
pt3$addColumnDataGroups("state",
                       addTotal = F)
pt3$addColumnDataGroups("product", dataSortOrder = "custom",
                       customSortOrder = c('Pre-Merchantable (<6"DBH)',
                                           'Pulpwood (6\" - 11.9")',
                                           'Sawtimber (12\" and up)'),
                       addTotal = T)
pt3$addRowDataGroups("type",
                     addTotal = F)
pt3$addRowDataGroups("year",
                    addTotal = F,
                    header = 'Year')
filterOverrides <- PivotFilterOverrides$new(pt3,
                                            overrideFunction = 
                                              getLastYearFilter)
pt3$defineCalculation(calculationName = "price",
                     caption = "Price Per Ton",
                     summariseExpression = "mean(price, na.rm=T)",
                     format="$%.2f")
pt3$defineCalculation(calculationName="OpeningValue", filters=filterOverrides, 
                     summariseExpression="sum(value, na.rm=T) / 1000000",
                     caption="Opening Value (millions)",
                     format=list(digits = 2, big.mark = ','))
pt3$defineCalculation(calculationName = "ClosingValue",
                     caption = "Closing Value (millions)",
                     summariseExpression = "sum(value, na.rm=T) / 1000000",
                     format=list(digits = 2, big.mark = ','))
pt3$defineCalculation(calculationName="NetChangeValue", type="calculation", 
                     caption = "Net Change in Value (millions)",
                     basedOn=c("ClosingValue", "OpeningValue"),
                     calculationExpression="values$ClosingValue-values$OpeningValue", 
                     format=list(digits = 2, big.mark = ','))
pt3$theme <- "largeplain"
pt3$renderPivot(styleNamePrefix="t2")
pt3$renderPivot()







# table 4: GA Oak, all years----
pt4 <- PivotTable$new()
pt4$addData(filter(df, type == 'oak'))
pt4$addColumnDataGroups("state",
                        addTotal = F)
pt4$addColumnDataGroups("product", dataSortOrder = "custom",
                        customSortOrder = c('Pre-Merchantable (<6"DBH)',
                                            'Pulpwood (6\" - 11.9")',
                                            'Sawtimber (12\" and up)'),
                        addTotal = T)
pt4$addRowDataGroups("year",
                     addTotal = F)
pt4$defineCalculation(calculationName = "tons",
                      caption = "Green Tons (millions)",
                      summariseExpression = "sum(tons, na.rm=T) / 1000000",
                      format="%.0f")
pt4$defineCalculation(calculationName = "price_tons",
                      caption = "Price Per Ton",
                      summariseExpression = "mean(price_tons, na.rm=T)",
                      format="$%.2f")
pt4$defineCalculation(calculationName = "value",
                      caption = "Value (millions)",
                      type = "calculation",
                      basedOn = c("price_tons", "tons"),
                      format=list(digits = 2, big.mark = ','),
                      calculationExpression = "(values$price_tons * values$tons)")
pt4$renderPivot()

# table 5: GA Oak Biomass (Green Tons), NCA format----

pt5 <- PivotTable$new()
pt5$addData(filter(df, type == 'oak'))
pt5$addColumnDataGroups("state",
                        addTotal = F)
pt5$addColumnDataGroups("product", dataSortOrder = "custom",
                        customSortOrder = c('Pre-Merchantable (<6"DBH)',
                                            'Pulpwood (6\" - 11.9")',
                                            'Sawtimber (12\" and up)'),
                        addTotal = T)
pt5$addRowDataGroups("year",
                     addTotal = F)
filterOverrides <- PivotFilterOverrides$new(pt5,
                                            overrideFunction = 
                                              getLastYearFilter)
pt5$defineCalculation(calculationName="OpeningStock", filters=filterOverrides, 
                      summariseExpression="sum(tons, na.rm=T) / 1000000",
                      caption="Opening Stock",
                      format="%.1f")
pt5$defineCalculation(calculationName="NetChangeStock", type="calculation", 
                      basedOn=c("ClosingStock", "OpeningStock"),
                      calculationExpression="values$ClosingStock-values$OpeningStock", 
                      caption="Net Change in Stock",
                      format="%.1f")
pt5$defineCalculation(calculationName = "ClosingStock",
                      caption = "Closing Stock",
                      summariseExpression = "sum(tons, na.rm=T) / 1000000",
                      format="%.1f")
pt5$renderPivot()

# table 6: GA Oak Value, NCA format----

pt6 <- PivotTable$new()
pt6$addData(filter(df, type == "oak", product != "Pre-Merchantable (<6\"DBH)"))
pt6$addColumnDataGroups("state",
                        addTotal = F)
pt6$addColumnDataGroups("product", dataSortOrder = "custom",
                        customSortOrder = c('Pre-Merchantable (<6"DBH)',
                                            'Pulpwood (6\" - 11.9")',
                                            'Sawtimber (12\" and up)'),
                        addTotal = T)
pt6$addRowDataGroups("year",
                     addTotal = F,
                     header = 'Year')
filterOverrides <- PivotFilterOverrides$new(pt6,
                                            overrideFunction = 
                                              getLastYearFilter)
pt6$defineCalculation(calculationName = "price_tons",
                      caption = "Price Per Ton",
                      summariseExpression = "mean(price_tons, na.rm=T)",
                      format="$%.2f")
pt6$defineCalculation(calculationName="OpeningValue", filters=filterOverrides, 
                      summariseExpression="sum(value, na.rm=T) / 1000000",
                      caption="Opening Value (millions)",
                      format=list(digits = 2, big.mark = ','))
pt6$defineCalculation(calculationName = "ClosingValue",
                      caption = "Closing Value (millions)",
                      summariseExpression = "sum(value, na.rm=T) / 1000000",
                      format=list(digits = 2, big.mark = ','))
pt6$defineCalculation(calculationName="NetChangeValue", type="calculation", 
                      caption = "Net Change in Value (millions)",
                      basedOn=c("ClosingValue", "OpeningValue"),
                      calculationExpression="values$ClosingValue-values$OpeningValue", 
                      format=list(digits = 2, big.mark = ','))
pt6$renderPivot()


# output tables----

library(basictabler)
library(officer)
library(flextable)

# convert to a basictabler table
tbl1 <- pt1$asBasicTable()
tbl2 <- pt2$asBasicTable()
tbl3 <- pt3$asBasicTable()

# convert to flextable
ft1 <- tbl1$asFlexTable()
ft2 <- tbl2$asFlexTable()
ft3 <- tbl3$asFlexTable()

# save word document

docx <- read_docx()
docx <- body_add_par(docx, "Example Table 1")
docx <- body_add_flextable(docx, value = ft1)
docx <- body_add_par(docx, "Example Table 2")
docx <- body_add_flextable(docx, value = ft2)
docx <- body_add_par(docx, "Example Table 3")
docx <- body_add_flextable(docx, value = ft3)

print(docx, target = "example_tables_word.docx")

