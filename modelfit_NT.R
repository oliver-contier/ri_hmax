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
# Null model
answer_nullmodel <- brm(Answer ~ Block + (Block|sub) + (1|item_id) + (1|task),
                        data = df,
                        family = bernoulli,
                        file = "answer_nullmodel",
                        chains = 2, cores = 2)

print('fitting nullmodel2')
# Null model with varying slope for Block over tasks and over subjects
answer_nullmodel2 <- brm(Answer ~ Block + (Block|sub) + (Block|task) + (1|item_id),
                        data = df,
                        family = bernoulli,
                        file = "answer_nullmodel2",
                        chains = 2, cores = 2)

print('fitting nullmodel3')
# Null model with random slope for block and task as well as their interaction across subjects
answer_nullmodel3 <- brm(Answer ~ Block*task + (Block*task|sub) + (1|item_id),
                        data = df,
                        family = bernoulli,
                        file = "answer_nullmodel3",
                        chains = 2, cores = 2)

print('fitting nullmodel4')
# Null model equivalent to nullmodel3, but with random item slope over tasks.
answer_nullmodel4 <- brm(Answer ~ Block*task + (Block*task|sub) + (item_id|task),
                        data = df,
                        family = bernoulli,
                        file = "answer_nullmodel4",
                        chains = 2, cores = 2)


print('fitting newNT model')
# newfound typicality
answer_newNT <- brm(Answer ~ newNT_cent*Block*task + (newNT_cent*Block*task|sub) + (1|item_id),
                    data = df,
                    family = bernoulli,
                    file = "answer_newNT",
                    chains = 2, cores = 2)

print('fitting conNT model')
# conserved typicality
answer_conNT <- brm(Answer ~ conNT_cent*Block*task + (conNT_cent*Block*task|sub) + (1|item_id),
                    data = df,
                    family = bernoulli,
                    file = "answer_conNT",
                    chains = 2, cores = 2)

print('fitting bothNT model')
# newfound and conserved typicality
answer_bothNT <- brm(Answer ~ newNT_cent*conNT_cent*Block*task + (newNT_cent*conNT_cent*Block*task|sub) + (1|item_id),
                    data = df,
                    family = bernoulli,
                    file = "answer_bothNT",
                    chains = 2, cores = 2)
