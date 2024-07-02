# NCA Timber Account
# query fia data for forest stock

library(tidyverse)
library(rFIA)
library(parallel)

ga <- getFIA(states = 'GA', dir = 'E:/')

db <- readFIA('E:/FIADB', states = c('GA'))

# how much biomass (ie. stock)?----

timber.stock <- biomass(db,
                        landType = 'timber',
                        treeType = 'gs')

# how much volume (ie. stock)?----

timber.volume <- volume(db,
                        landType = 'timber',
                        areaDomain = FORTYPCD %in% C(160:168),
                        treeType = 'gs',
                        totals = T,
                        nCores = 6)



d <- growMort(db, grpBy = 'UNITCD',
              bySizeClass = T,
              stateVar = 'BIO',
              totals = T,
              nCores = 6)



grm.bio.state <- growMort(db,
                          stateVar = 'BIO_AG',
                          areaDomain = FORTYPCD %in% C(160:168),
                          totals = T,
                          nCores = 6)

grm <- grm.bio.state %>%
  select(1, ends_with('TOTAL')) %>%
  mutate(recruitment = RECR_TOTAL / 2000 / 1000000,
         mortality = MORT_TOTAL / 2000 / 1000000,
         removals = REMV_TOTAL / 2000 / 1000000,
         net_change = (RECR_TOTAL - MORT_TOTAL - REMV_TOTAL) / 2000 / 1000000,
         current_total = CURR_TOTAL / 2000 / 1000000)

grow.bio.state <- vitalRates(db, grpBy = c(FORTYPCD, STATECD),
                             treeDomain = DIA >= 12,
                             totals = T,
                             nCores = 6)

