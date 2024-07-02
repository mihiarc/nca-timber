# timber asset value
# process FIA query of 
# volume_timber -- volume of current stock by species, age, and size
volume_timber <- readRDS("C:/Users/cmihiar/OneDrive - USDA/(NCA) Natural Capital/NCA Timber Account/FIA Data/timber_stock_volume.rds")

d <- volume_timber %>%
  filter(!is.na(volcfnet),
         volcfnet > 0)

dtrt <- filter(d, TRTCD1 != 0)
dplnt <- filter(d, STDORGCD == 1)

sum(dplnt$volcfnet)/sum(d$volcfnet)

dspcd <- distinct(d, SPCD)
dspgrpcd <- distinct(d, SPGRPCD)
dfortypcd <- distinct(d, FORTYPCD)

saveRDS(list(species = dspcd,
             species_group = dspgrpcd,
             forest_type = dfortypcd), "C:/Users/cmihiar/OneDrive - USDA/(NCA) Natural Capital/NCA Timber Account/FIA Data/timber_species_list.rds")

dspcdplnt <- distinct(dplnt, SPCD)
dspgrpcdplnt <- distinct(dplnt, SPGRPCD)
dfortypcdplnt <- distinct(dplnt, FORTYPCD)

# harvest removal----
# load packages
library(RSQLite)
library(tidyverse)

# connect to FIA database----

fiadb <- dbConnect(SQLite(), 'D:/FIADB SQLite/SQLite_FIADB_ENTIRE.db')


hvol <- dbGetQuery(fiadb, "select ps.expns * sum(
  grm.subp_tparemv_unadj_gs_timber * (case when coalesce(grm.subptyp_midpt, 0) = 0 then 0
                            when grm.subptyp_midpt = 1 then ps.adj_factor_subp
                            when grm.subptyp_midpt = 2 then ps.adj_factor_micr
                            when grm.subptyp_midpt = 3 then ps.adj_factor_macr
                            else 0 end) *
  tgrmmid.volcfnet) as harvest_volume


FROM pop_stratum ps,
pop_plot_stratum_assgn ppsa,
plot plot,
plot pplot,
plotgeom plotg,
cond cond,
cond pcond,
tree tree,
tree ptree,
tree_grm_begin tgrmbegin,
tree_grm_midpt tgrmmid,
tree_grm_component grm

where ps.cn = ppsa.stratum_cn
and ppsa.plt_cn = plot.cn
and plot.cn = plotg.cn
and plot.cn = cond.plt_cn
and plot.cn = tree.plt_cn
and tree.condid = cond.condid
and tree.plt_cn = cond.plt_cn
and plot.prev_plt_cn = pplot.cn
and tree.prevcond = pcond.condid
and tree.prev_tre_cn = ptree.cn
and tree.cn = tgrmbegin.tre_cn
and tree.cn = tgrmmid.tre_cn
and tree.cn = grm.tre_cn
and plotg.statecd = 13")
