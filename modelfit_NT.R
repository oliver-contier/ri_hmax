# This script is meant to run the model fitting procedure with BRMS on our computing cluster.
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


# Null models

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

print('fitting nullmodel6')
answer_nullmodel6 <- brm(Answer ~ ec_b2 + ec_b3 + task + task_order + task:task_order + (ec_b2 + ec_b3 + task + task_order|sub) + (1|item_id),
                        data=df,
                        family=bernoulli,
                        file="answer_nullmodel6",
                        sample_prior=TRUE, save_all_pars=TRUE,
                        chains=2, cores=2,
                        inits=0)

print('fitting nullmodel7')
answer_nullmodel7 <- brm(Answer ~ ec_b2 + ec_b3 + task + task_order + task:task_order + ec_b2:task + ec_b3:task + ec_b2:task:task_order + ec_b3:task:task_order + (ec_b2 + ec_b3 + task + task_order|sub) + (1|item_id),
                        data=df,
                        family=bernoulli,
                        file="answer_nullmodel7",
                        sample_prior=TRUE, save_all_pars=TRUE,
                        chains=2, cores=2,
                        inits=0)


# Neural Typicality models

print('fitting bothNT model')
answer_bothNT <- brm(Answer ~ ec_b2 + ec_b3 + task + task_order + conNT + newNT + conNT:newNT + conNT:ec_b2 + conNT:ec_b3 + newNT:ec_b2 + newNT:ec_b3 + conNT:task + newNT:task + task:ec_b2 + task:ec_b3 + (ec_b2 + ec_b3 + task + task_order + conNT + newNT|sub) + (1|item_id),
                        data=df,
                        family=bernoulli,
                        file="answer_bothNT",
                        sample_prior=TRUE, save_all_pars=TRUE,
                        chains=2, cores=2)

print('fitting newNT model')
answer_newNT <- brm(Answer ~ ec_b2 + ec_b3 + task + task_order + newNT + newNT:ec_b2 + newNT:ec_b3 + newNT:task + task:ec_b2 + task:ec_b3 + (ec_b2 + ec_b3 + task + task_order + newNT|sub) + (1|item_id),
                    data=df,
                    family=bernoulli,
                    file="answer_newNT",
                    sample_prior=TRUE, save_all_pars=TRUE,
                    chains=2, cores=2)

print('fitting conNT model')
answer_conNT <- brm(Answer ~ ec_b2 + ec_b3 + task + task_order + conNT + conNT:ec_b2 + conNT:ec_b3 + conNT:task + task:ec_b2 + task:ec_b3 + (ec_b2 + ec_b3 + task + task_order + conNT|sub) + (1|item_id),
                    data=df,
                    family=bernoulli,
                    file="answer_conNT",
                    sample_prior=TRUE, save_all_pars=TRUE,
                    chains=2, cores=2)

print('comparing models with LOO')
loo_modcomp <- loo(answer_nullmodel, answer_nullmodel2, answer_nullmodel3,
  answer_nullmodel4, answer_nullmodel5, answer_nullmodel6, answer_nullmodel7,
  answer_bothNT, answer_newNT, answer_conNT)
print(loo_modcomp)

# Save LOO results to rds file
print('saving LOO results')
saveRDS(loo_modcomp, file = "loo_modcomp.rds")

print('DONE')
