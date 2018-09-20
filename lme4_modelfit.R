# execute GLM analyses with lme4 on our cluster

print('load packages')
library(lme4)

print('loading data')
# Load data
load("./prepped_data.RData", ex <- new.env())
df <- ex$df_total

# print data to stdout
head(df)
str(df)


# Accuracies (logistic models)
print('fitting accuracies')
start_time <- Sys.time()

## ED and CD models
answer_bothD <- glmer(Answer ~ ED + CD + Block + task + task_order +
                      (ED + CD + Block + task + task_order|sub) + (1|item_id),
                      data = df, family = binomial,
                      control=glmerControl(optimizer ="Nelder_Mead"))

answer_ED <- glmer(Answer ~ ED + Block + task + task_order +
                      (ED + Block + task + task_order|sub) + (1|item_id),
                      data = df, family = binomial,
                      control=glmerControl(optimizer ="Nelder_Mead"))

answer_CD <- glmer(Answer ~ CD + Block + task + task_order +
                      (CD + Block + task + task_order|sub) + (1|item_id),
                      data = df, family = binomial,
                      control=glmerControl(optimizer ="Nelder_Mead"))

## conNT and newNT models
answer_bothNT <- glmer(Answer ~ conNT_z + newNT_z + Block + task + task_order +
                      (conNT_z + newNT_z + Block + task + task_order|sub) + (1|item_id),
                      data = df, family = binomial,
                      control=glmerControl(optimizer ="Nelder_Mead"))

answer_conNT <- glmer(Answer ~ conNT_z + Block + task + task_order +
                      (conNT_z + Block + task + task_order|sub) + (1|item_id),
                      data = df, family = binomial,
                      control=glmerControl(optimizer ="Nelder_Mead"))

answer_newNT <- glmer(Answer ~ newNT_z + Block + task + task_order +
                      (newNT_z + Block + task + task_order|sub) + (1|item_id),
                      data = df, family = binomial,
                      control=glmerControl(optimizer ="Nelder_Mead"))

## null model
answer_null <- glmer(Answer ~ Block + task + task_order +
                      (Block + task + task_order|sub) + (1|item_id),
                      data = df, family = binomial,
                      control=glmerControl(optimizer ="Nelder_Mead"))

end_time <- Sys.time()
print('accuraciy models took:')
print(end_time - start_time)


# Reaction times (linear model)
# Note that ML instead of REML must be used to allow comparison of models
# with different fixed effects
print('fitting RT')
start_time <- Sys.time()

## ED and CD models
rt_bothD <- lmer(RT ~ ED + CD + Block + task + task_order +
                  (ED + CD + Block + task + task_order|sub) + (1|item_id),
                  data = df, control = lmerControl(optimizer ="Nelder_Mead"), REML=F)

rt_ED <- lmer(RT ~ ED + Block + task + task_order +
                  (ED + Block + task + task_order|sub) + (1|item_id),
                  data = df, control = lmerControl(optimizer ="Nelder_Mead"), REML=F)

rt_CD <- lmer(RT ~ CD + Block + task + task_order +
                  (CD + Block + task + task_order|sub) + (1|item_id),
                  data = df, control = lmerControl(optimizer ="Nelder_Mead"), REML=F)

## conNT and newNT models
rt_bothNT <- lmer(RT ~ conNT_z + newNT_z + Block + task + task_order +
                  (conNT_z + newNT_z + Block + task + task_order|sub) + (1|item_id),
                  data = df, control = lmerControl(optimizer ="Nelder_Mead"), REML=F)

rt_conNT <- lmer(RT ~ conNT_z + Block + task + task_order +
                  (conNT_z + Block + task + task_order|sub) + (1|item_id),
                  data = df, control = lmerControl(optimizer ="Nelder_Mead"), REML=F)

rt_newNT <- lmer(RT ~ newNT_z + Block + task + task_order +
                  (newNT_z + Block + task + task_order|sub) + (1|item_id),
                  data = df, control = lmerControl(optimizer ="Nelder_Mead"), REML=F)

## null model
rt_null <- lmer(RT ~ conNT_z + Block + task + task_order +
                (conNT_z + Block + task + task_order|sub) + (1|item_id),
                data = df, control = lmerControl(optimizer ="Nelder_Mead"), REML=F)

end_time <- Sys.time()
print('RT models took:')
print(end_time - start_time)


# Model comparison (likelihood ratio test with Rs ANOVA command)

# accuracies
print('comparing accuracies')
## NT
answer_nullboth <- anova(answer_null, answer_bothNT)
answer_nullnew <- anova(answer_null, answer_newNT)
answer_nullcon <- anova(answer_null, answer_conNT)
answer_bothcon <- anova(answer_bothNT, answer_conNT)
answer_bothnew <- anova(answer_bothNT, answer_newNT)
## CD/ED
answer_nullbothD <- anova(answer_null, answer_bothD)
answer_nullCD <- anova(answer_null, answer_CD)
answer_nullED <- anova(answer_null, answer_ED)
answer_bothCD <- anova(answer_bothD, answer_CD)
answer_bothED <- anova(answer_bothD, answer_ED)

# rt
print('comparing RT')
## NT
rt_nullboth <- anova(rt_null, rt_bothNT)
rt_nullnew <- anova(rt_null, rt_newNT)
rt_nullcon <- anova(rt_null, rt_conNT)
rt_bothcon <- anova(rt_bothNT, rt_conNT)
rt_bothnew <- anova(rt_bothNT, rt_newNT)
## CD/ED
rt_nullbothD <- anova(rt_null, rt_bothD)
rt_nullCD <- anova(rt_null, rt_CD)
rt_nullED <- anova(rt_null, rt_ED)
rt_bothCD <- anova(rt_bothD, rt_CD)
rt_bothED <- anova(rt_bothD, rt_ED)

# save data
save.image(file = "lme4_modelfit.RData", version = NULL, safe = TRUE)

print('DONE')
