library(brms)
theme_set(theme_default())

# load RData into environment called ex
# ex contains data frames: disc_df_r, disc_df_brms, test_df
load("~/Desktop/hmax/python/compare_images/prepped_data.RData", ex <- new.env())

# Load test data from environment
disc_df_brms <- ex$disc_df_brms
str(disc_df_brms)

# try this
disc_df_brms$Block <- factor(disc_df_brms$Block, ordered = FALSE)

# set up maximally complex model
discmodel1 <- brm(Answer ~ Block*ED + (Block*ED|sub) + (1|item_id),
             data = disc_df_brms,
             family = bernoulli,  #bernoulli
             chains = 2, cores = 2)

#save.image(file = "disc_maxmodel.RData", version = NULL, safe = TRUE)
#load("~/Desktop/hmax/python/compare_images/disc_maxmodel.RData", ex <- new.env())
# discmodel1 <- ex$discmodel1

summary(discmodel1)

#TODO:
# make block an unordered factor in data_exploration.ipynb
6
#TODO: visualize
plot(discmodel1, ask = FALSE)
pp_check(discmodel1)  # check posterior predictions
plot(marginal_effects(discmodel1), ask = FALSE)  # plot marginal predictions

