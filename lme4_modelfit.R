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

answer_null <- glmer(Answer ~ Block + task + task_order +
                      (Block + task + task_order|sub) + (1|item_id),
                      data = df, family = binomial,
                      control=glmerControl(optimizer ="Nelder_Mead"))

end_time <- Sys.time()
print('accuracies took:')
print(end_time - start_time)


# Reaction times (linear model)
print('fitting RT')
start_time <- Sys.time()

rt_bothNT <- lmer(RT ~ conNT_z + newNT_z + Block + task + task_order +
                  (conNT_z + newNT_z + Block + task + task_order|sub) + (1|item_id),
                  data = df, control = lmerControl(optimizer ="Nelder_Mead"))

rt_conNT <- lmer(RT ~ conNT_z + Block + task + task_order +
                  (conNT_z + Block + task + task_order|sub) + (1|item_id),
                  data = df, control = lmerControl(optimizer ="Nelder_Mead"))

rt_newNT <- lmer(RT ~ newNT_z + Block + task + task_order +
                  (newNT_z + Block + task + task_order|sub) + (1|item_id),
                  data = df, control = lmerControl(optimizer ="Nelder_Mead"))

rt_null <- lmer(RT ~ conNT_z + Block + task + task_order +
                (conNT_z + Block + task + task_order|sub) + (1|item_id),
                data = df, control = lmerControl(optimizer ="Nelder_Mead"))

end_time <- Sys.time()
print('answer_bothNT took:')
print(end_time - start_time)


print('model comparison')
anova_answer <- anova(answer_bothNT, answer_conNT, answer_newNT, answer_null)
anova_rt <- anova(rt_bothNT, rt_conNT, rt_newNT, rt_null)

# save data
save.image(file = "lme4_modelfit.RData", version = NULL, safe = TRUE)
#saveRDS(..., file = "./lme4_results/....rds")

print('DONE')
