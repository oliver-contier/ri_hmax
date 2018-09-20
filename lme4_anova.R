# Load the fitted models and do pairwise model comparison with the
# likelihood ratio test from Rs ANOVA command.
# result is a workspace image with the same name as the loaded one

# Note that comparing the accuracy models with ANOVA would be quite fast
# but included in this script in the interest of clarity.

library('lme4')

# Load data
print('loading data')
load("./lme4_modelfit.RData", ex <- new.env())
# data frame
df <- ex$df
# model results
answer_bothNT <- ex$answer_bothNT
answer_conNT <- ex$answer_conNT
answer_newNT <- ex$answer_newNT
answer_null <- ex$answer_null
rt_bothNT <- ex$rt_bothNT
rt_conNT <- ex$rt_conNT
rt_newNT <- ex$rt_newNT
rt_null <- ex$rt_null


# fit ANOVAS

# accuracies
print('comparing accuracies')
answer_nullboth <- anova(answer_null, answer_bothNT)
answer_nullnew <- anova(answer_null, answer_newNT)
answer_nullcon <- anova(answer_null, answer_conNT)
answer_bothcon <- anova(answer_bothNT, answer_conNT)
answer_bothnew <- anova(answer_bothNT, answer_conNT)
answer_connew <- anova(answer_conNT, answer_newNT)

# rt
print('comparing RT')
rt_nullboth <- anova(rt_null, rt_bothNT)
rt_nullnew <- anova(rt_null, rt_newNT)
rt_nullcon <- anova(rt_null, rt_conNT)
rt_bothcon <- anova(rt_bothNT, rt_conNT)
rt_bothnew <- anova(rt_bothNT, rt_newNT)
rt_connew <- anova(rt_conNT, rt_newNT)


# save data under same name
print('saving data')
save.image(file = "lme4_modelfit.RData", version = NULL, safe = TRUE)

print('DONE!')
