print('load brms')
library(brms)

print('loading data')
# Load data
load("./prepped_data.RData", ex <- new.env())
df <- ex$df_total

# print data to stdout
head(df)
str(df)

print('fitting nullmodel')
# Null model
answer_nullmodel <- brm(Answer ~ Block + (Block|sub) + (1|item_id) + (1|task),
                        data = df,
                        family = bernoulli,
                        file = "answer_nullmodel",
                        chains = 2, cores = 2)

print('fitting newNT model')
# newfound typicality
answer_newNT <- brm(Answer ~ newNT_cent*Block + (newNT_cent*Block|sub) + (1|item_id) + (1|task), data = df, family = bernoulli, file = "answer_newNT, chains = 2, cores = 2)

print('fitting conNT model')
# conserved typicality
answer_conNT <- brm(Answer ~ conNT_cent*Block + (conNT_cent*Block|sub) + (1|item_id) + (1|task),
                    data = df,
                    family = bernoulli,
                    file = "answer_conNT",
                    chains = 2, cores = 2)

print('fitting bothNT model')
# newfound and conserved typicality
answer_bothNT <- brm(Answer ~ conNT_cent*newNT_cent*Block + (conNT_cent*newNT_cent*Block|sub) + (1|item_id) + (1|task),
                    data = df,
                    family = bernoulli,
                    file = "answer_bothNT",
                    chains = 2, cores = 2)
