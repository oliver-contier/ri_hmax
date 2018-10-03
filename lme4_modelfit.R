print('load packages')
#library(lme4)
library(lmerTest)

print('loading data')
# Load data
load("./prepped_data.RData", ex <- new.env())
df <- ex$df_total

# print data to stdout
head(df)
str(df)

# #TODO: Create function and loop
# # specify ffx and rfx as vectors
# ffx <- paste("ED", "Block", "", sep="+")
# rfx_sub <- paste("ED", "Block", sep="+")
# # build a formula out of these vectors
# # and plug formla into glmer
# form <- paste("Answer~", ffx, "(", rfx, "|sub) + (1|item_id)", sep="")
# test <- glmer(form, data = df, family = binomial)

# Accuracies (logistic models)
print('fitting accuracies')

  ## ED and CD models
rdspath <- "./lme4_data/answer_bothD.rds"
paste("fitting", rdspath, sep=" ")
if (!file.exists(rdspath)){
  answer_bothD <- glmer(Answer ~ ED + CD + Block + task + task_order +
                          (ED + CD + Block + task + task_order|sub) + (1|item_id),
                          data = df, family = binomial)
  saveRDS(answer_bothD, rdspath)
}

rdspath <- "./lme4_data/answer_ED.rds"
paste("fitting", rdspath, sep=" ")
if (!file.exists(rdspath)){
  answer_ED <- glmer(Answer ~ ED + Block + task + task_order +
                  (ED + Block + task + task_order|sub) + (1|item_id),
                  data = df, family = binomial)
  saveRDS(answer_ED, rdspath)
}

rdspath <- "./lme4_data/answer_CD.rds"
paste("fitting", rdspath, sep=" ")
if (!file.exists(rdspath)){
  answer_CD <- glmer(Answer ~ CD + Block + task + task_order +
                        (CD + Block + task + task_order|sub) + (1|item_id),
                        data = df, family = binomial)
  saveRDS(answer_CD, rdspath)
}

  ## conNT and newNT models
rdspath <- "./lme4_data/answer_bothNT.rds"
paste("fitting", rdspath, sep=" ")
if (!file.exists(rdspath)){
  answer_bothNT <- glmer(Answer ~ conNT_z + newNT_z + Block + task + task_order +
                        (conNT_z + newNT_z + Block + task + task_order|sub) + (1|item_id),
                        data = df, family = binomial)
  saveRDS(answer_bothNT, rdspath)
}

rdspath <- "./lme4_data/answer_bothNT2.rds"
paste("fitting", rdspath, sep=" ")
if (!file.exists(rdspath)){
  # simpler version of bothNT model (no RFX for NT measures)
  answer_bothNT2 <- glmer(Answer ~ conNT_z + newNT_z + Block + task + task_order +
                        (Block + task + task_order|sub) + (1|item_id),
                        data = df, family = binomial)
  saveRDS(answer_bothNT2, rdspath)
}

rdspath <- "./lme4_data/answer_conNT.rds"
paste("fitting", rdspath, sep=" ")
if (!file.exists(rdspath)){
  answer_conNT <- glmer(Answer ~ conNT_z + Block + task + task_order +
                        (conNT_z + Block + task + task_order|sub) + (1|item_id),
                        data = df, family = binomial)
  saveRDS(answer_conNT, rdspath)
}

rdspath <- "./lme4_data/answer_newNT.rds"
paste("fitting", rdspath, sep=" ")
if (!file.exists(rdspath)){
  answer_newNT <- glmer(Answer ~ newNT_z + Block + task + task_order +
                        (newNT_z + Block + task + task_order|sub) + (1|item_id),
                        data = df, family = binomial)
  saveRDS(answer_newNT, rdspath)
}

  ## null model
rdspath <- "./lme4_data/answer_null.rds"
paste("fitting", rdspath, sep=" ")
if (!file.exists(rdspath)){
  answer_null <- glmer(Answer ~ Block + task + task_order +
                        (Block + task + task_order|sub) + (1|item_id),
                        data = df, family = binomial)
  saveRDS(answer_null, rdspath)
}


# Reaction time models

## ED and CD models
rdspath <- "./lme4_data/rt_bothD.rds"
paste("fitting", rdspath, sep=" ")
if (!file.exists(rdspath)){
  rt_bothD <- lmer(RT ~ ED + CD + Block + task + task_order +
                    (ED + CD + Block + task + task_order|sub) + (1|item_id),
                    data = df, REML=F)
  saveRDS(rt_bothD, rdspath)
}

rdspath <- "./lme4_data/rt_ED.rds"
paste("fitting", rdspath, sep=" ")
if (!file.exists(rdspath)){
  rt_ED <- lmer(RT ~ ED + Block + task + task_order +
                    (ED + Block + task + task_order|sub) + (1|item_id),
                    data = df, REML=F)
  saveRDS(rt_ED, rdspath)
}

rdspath <- "./lme4_data/rt_CD.rds"
paste("fitting", rdspath, sep=" ")
if (!file.exists(rdspath)){
  rt_CD <- lmer(RT ~ CD + Block + task + task_order +
                (CD + Block + task + task_order|sub) + (1|item_id),
                data = df, REML=F)
  saveRDS(rt_CD, rdspath)
}

## conNT and newNT models
rdspath <- "./lme4_data/rt_bothNT.rds"
paste("fitting", rdspath, sep=" ")
if (!file.exists(rdspath)){
  rt_bothNT <- lmer(RT ~ conNT_z + newNT_z + Block + task + task_order +
                  (conNT_z + newNT_z + Block + task + task_order|sub) + (1|item_id),
                  data = df, REML=F)
  saveRDS(rt_bothNT, rdspath)
}

# run lme4's RANOVA on our maximal bothNT model
# for indication which RFX can be dropped
rdspath <- "./lme4_data/rt_bothNT_ranova.rds"
if (!file.exists(rdspath)){
  rt_bothNT <- readRDS("./lme4_data/rt_bothNT.rds")
  rt_bothNT_ranova <- ranova(rt_bothNT)
  saveRDS(rt_bothNT_ranova, rdspath)
}

# reduce RFX of bothNT model
rdspath <- "./lme4_data/rt_bothNT2.rds"
paste("fitting", rdspath, sep=" ")
if (!file.exists(rdspath)){
  rt_bothNT2 <- lmer(RT ~ conNT_z + newNT_z + Block + task + task_order +
                    (Block + task + task_order|sub) + (1|item_id),
                    data = df, REML=F)
  saveRDS(rt_bothNT2, rdspath)
}

rdspath <- "./lme4_data/rt_bothNT3.rds"
paste("fitting", rdspath, sep=" ")
if (!file.exists(rdspath)){
  rt_bothNT3 <- lmer(RT ~ conNT_z + newNT_z + Block + task + task_order +
                    (task + task_order|sub) + (1|item_id),
                    data = df, REML=F)
  saveRDS(rt_bothNT3, rdspath)
}

rdspath <- "./lme4_data/rt_bothNT4.rds"
paste("fitting", rdspath, sep=" ")
if (!file.exists(rdspath)){
  rt_bothNT4 <- lmer(RT ~ conNT_z + newNT_z + Block + task + task_order +
                    (Block + task|sub) + (1|item_id),
                    data = df, REML=F)
  saveRDS(rt_bothNT4, rdspath)
}

rdspath <- "./lme4_data/rt_bothNT5.rds"
paste("fitting", rdspath, sep=" ")
if (!file.exists(rdspath)){
  rt_bothNT5 <- lmer(RT ~ conNT_z + newNT_z + Block + task + task_order +
                    (Block + task_order|sub) + (1|item_id),
                    data = df, REML=F)
  saveRDS(rt_bothNT5, rdspath)
}

rdspath <- "./lme4_data/rt_bothNT6.rds"
paste("fitting", rdspath, sep=" ")
if (!file.exists(rdspath)){
  rt_bothNT6 <- lmer(RT ~ conNT_z + newNT_z + Block + task + task_order +
                    (task|sub) + (1|item_id),
                    data = df, REML=F)
  saveRDS(rt_bothNT6, rdspath)
}

rdspath <- "./lme4_data/rt_bothNT7.rds"
paste("fitting", rdspath, sep=" ")
if (!file.exists(rdspath)){
  rt_bothNT7 <- lmer(RT ~ conNT_z + newNT_z + Block + task + task_order +
                    (Block|sub) + (1|item_id),
                    data = df, REML=F)
  saveRDS(rt_bothNT7, rdspath)
}

# same as rt_bothNT4, but removed task_order as fixed-effect.
rdspath <- "./lme4_data/rt_bothNT8.rds"
paste("fitting", rdspath, sep=" ")
if (!file.exists(rdspath)){
  rt_bothNT8 <- lmer(RT ~ conNT_z + newNT_z + Block + task +
                    (Block + task|sub) + (1|item_id),
                    data = df, REML=F)
  saveRDS(rt_bothNT8, rdspath)
}

# ranova for bothNT model 8
rdspath <- "./lme4_data/rt_bothNT8_ranova.rds"
if (!file.exists(rdspath)){
  rt_bothNT8 <- readRDS("./lme4_data/rt_bothNT8.rds")
  rt_bothNT8_ranova <- ranova(rt_bothNT8)
  saveRDS(rt_bothNT8_ranova, rdspath)
}

rdspath <- "./lme4_data/rt_conNT.rds"
paste("fitting", rdspath, sep=" ")
if (!file.exists(rdspath)){
  rt_conNT <- lmer(RT ~ conNT_z + Block + task + task_order +
                  (conNT_z + Block + task + task_order|sub) + (1|item_id),
                  data = df, REML=F)
  saveRDS(rt_conNT, rdspath)
}

rdspath <- "./lme4_data/rt_newNT.rds"
paste("fitting", rdspath, sep=" ")
if (!file.exists(rdspath)){
  rt_newNT <- lmer(RT ~ newNT_z + Block + task + task_order +
                  (newNT_z + Block + task + task_order|sub) + (1|item_id),
                  data = df, REML=F)
  saveRDS(rt_newNT, rdspath)
}

rdspath <- "./lme4_data/rt_null.rds"
paste("fitting", rdspath, sep=" ")
if (!file.exists(rdspath)){
  rt_null <- lmer(RT ~ Block + task + task_order +
                  (Block + task + task_order|sub) + (1|item_id),
                  data = df, REML=F)
  saveRDS(rt_null, rdspath)
}


print('DONE')

# read rds
#mod2 <- readRDS("mymodel.rds")
