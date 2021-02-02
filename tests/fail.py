# def test_distributor_notify_reward_amount(multi_reward, accounts, reward_token, alice, bob, base_token, chain):
#    reward_token.approve(multi_reward, 10**19)
#    reward_token.approve(bob, 10**19)
#    reward_token.approve(alice, 10**19)
#    multi_reward.setRewardsDistributor(reward_token, bob, {'from': alice})
#    multi_reward.notifyRewardAmount(reward_token, 10**10, {'from': bob})
#    assert multi_reward.getRewardForDuration(reward_token) > 0


# Interactions with multiple tokens
# Make sure no weirdness with one reward distributor messing with another person's reward amounts
# Hit all the fail paths
# Brownie GUI
# Alice, Bob...
