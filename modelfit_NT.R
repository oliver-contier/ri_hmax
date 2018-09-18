# This script is meant to run the model fitting procedure on our computing cluster.
# The model setup is identical to the ones found in brms_analysis.ipynb, which
# loads the saved .rds files to visualize and analyze the reslts.


print('load brms')
library(brms)

print('loading data')
# Load data
load("./prepped_data.RData", ex <- new.env())
df <- ex$df_total

# print data to stdout
head(df)
str(df)

print('fitting nullmodel1')
answer_nullmodel <- brm(Answer ~ ec_b2 + ec_b3 + task + task_order + (ec_b2 + ec_b3 + task + task_order|sub) + (1|item_id),
                        data=df,
                        family=bernoulli,
                        file="answer_nullmodel",
                        sample_prior=TRUE, save_all_pars=TRUE,
                        chains=2, cores=2)

print('fitting nullmodel2')
answer_nullmodel2 <- brm(Answer ~ ec_b2 + ec_b3 + task + ec_b2:task + ec_b3:task + task_order + (1|ec_b2 + ec_b3 + task + ec_b2:task + ec_b3:task + task_order) + (1|item_id),
                        data=df,
                        family=bernoulli,
                        file="answer_nullmodel2",
                        sample_prior=TRUE, save_all_pars=TRUE,
                        chains=2, cores=2)

print('fitting nullmodel3')
answer_nullmodel3 <- brm(Answer ~ ec_b2 + ec_b3 + task_order + ec_b2:task_order + ec_b3:task_order + task + (1|ec_b2 + ec_b3 + task_order + ec_b2:task_order + ec_b3:task_order + task) + (1|item_id),
                        data=df,
                        family=bernoulli,
                        file="answer_nullmodel3",
                        sample_prior=TRUE, save_all_pars=TRUE,
                        chains=2, cores=2)

print('fitting nullmodel4')
answer_nullmodel4 <- brm(Answer ~ ec_b2 + ec_b3 + task + task_order + task:task_order + (ec_b2 + ec_b3 + task + task_order + task:task_order|sub) + (1|item_id),
                        data=df,
                        family=bernoulli,
                        file="answer_nullmodel4",
                        sample_prior=TRUE, save_all_pars=TRUE,
                        chains=2, cores=2,
                        inits=0)

print('fitting nullmodel5')
answer_nullmodel5 <- brm(Answer ~ ec_b2 + ec_b3 + task + task_order + task:task_order + ec_b2:task + ec_b3:task + ec_b2:task:task_order + ec_b3:task:task_order + (ec_b2 + ec_b3 + task + task_order + task:task_order + ec_b2:task + ec_b3:task + ec_b2:task:task_order + ec_b3:task:task_order|sub) + (1|item_id),
                        data=df,
                        family=bernoulli,
                        file="answer_nullmodel5",
                        sample_prior=TRUE, save_all_pars=TRUE,
                        chains=2, cores=2,
                        inits=0)

print('comparing null models with LOO')
loo_nullmodcomp_nills <- loo(answer_nullmodel, answer_nullmodel2, answer_nullmodel3, answer_nullmodel4, answer_nullmodel5)
print(loo_nullmodcomp_nulls)

# print('fitting newNT model')
# # newfound typicality
# answer_newNT <- brm(Answer ~ newNT_cent*Block*task + (newNT_cent*Block*task|sub) + (1|item_id),
#                     data=df,
#                     #priors=set_prior("normal(0,100)", class="b")
#                     family=bernoulli,
#                     file="answer_newNT",
#                     save_all_pars=TRUE,
#                     chains=2, cores=2)
#
# print('fitting conNT model')
# # conserved typicality
# answer_conNT <- brm(Answer ~ conNT_cent*Block*task + (conNT_cent*Block*task|sub) + (1|item_id),
#                     data=df,
#                     family=bernoulli,
#                     #priors=set_prior("normal(0,100)", class="b")
#                     file="answer_conNT",
#                     save_all_pars=TRUE,
#                     chains=2, cores=2)
#
# print('fitting bothNT model')
# # newfound and conserved typicality
# answer_bothNT <- brm(Answer ~ newNT_cent*conNT_cent*Block*task + (newNT_cent*conNT_cent*Block*task|sub) + (1|item_id),
#                     data=df,
#                     family=bernoulli,
#                     #priors=set_prior("normal(0,100)", class="b")
#                     file="answer_bothNT",
#                     save_all_pars=TRUE,
#                     chains=2, cores=2)

print('DONE')
