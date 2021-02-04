#!/usr/bin/python3

import brownie


# Was Reward Token 1 instantiated to Bob?
def test_reward_added(multi, accounts, reward_token, bob):
    assert multi.rewardData(reward_token)[0] == bob


# Was Reward Token 1 instantiated to Charlie?
def test_reward2_added(multi, accounts, reward_token2, charlie):
    assert multi.rewardData(reward_token2)[0] == charlie


# Owner cannot modify reward
def test_owner_cannot_modify_reward(multi, reward_token, alice):
    with brownie.reverts():
        multi.addReward(reward_token, alice, 3600, {"from": alice})


# Can distributor set reward?
def test_set_rewards_distributor(multi, reward_token, alice, bob):
    multi.setRewardsDistributor(reward_token, bob, {"from": alice})
    assert multi.rewardData(reward_token)[0] == bob


# Are owners able to update reward notification?
def test_owner_notify_reward_amount(multi, accounts, reward_token, alice, bob, base_token, chain):
    reward_token.approve(multi, 10 ** 19, {"from": alice})
    multi.setRewardsDistributor(reward_token, alice, {"from": alice})
    multi.notifyRewardAmount(reward_token, 10 ** 10, {"from": alice})
    assert multi.getRewardForDuration(reward_token) > 0


# Random users should not be able to access notifyRewardAmount
def test_rando_notify_reward_amount(multi, reward_token, alice, bob, charlie):
    multi.setRewardsDistributor(reward_token, bob, {"from": alice})
    with brownie.reverts():
        multi.notifyRewardAmount(reward_token, 10 ** 10, {"from": charlie})


# Cannot call notifyRewardAmount without Distributor set
def test_notify_without_distributor(multi, reward_token, alice):
    with brownie.reverts():
        multi.notifyRewardAmount(reward_token, 10 ** 10, {"from": alice})


# Reward per token paid accurate?
def test_reward_per_token_paid(multi, reward_token, alice, chain):
    reward_token.approve(multi, 10 ** 19, {"from": alice})
    multi.setRewardsDistributor(reward_token, alice, {"from": alice})
    multi.stake(10 ** 10, {"from": alice})

    for i in range(5):
        _last_val = multi.userRewardPerTokenPaid(alice, reward_token)
        multi.notifyRewardAmount(reward_token, 10 ** 10, {"from": alice})
        chain.mine(timedelta=60)
        multi.getReward()
        assert multi.userRewardPerTokenPaid(alice, reward_token) > _last_val


# Check block.timestamp before periodFinish 
def test_notify_reward_before_period_finish(multi, reward_token, alice, chain):
    reward_token.approve(multi, 10 ** 19, {"from": alice})
    multi.setRewardsDistributor(reward_token, alice, {"from": alice})
    multi.notifyRewardAmount(reward_token, 10 ** 15, {'from': alice})
   
    # Initial rate is set
    initial_rate = 10 ** 15 // 60 
    assert multi.rewardData(reward_token)['rewardRate'] == initial_rate

    # Within duration, update reward
    multi.notifyRewardAmount(reward_token, 10 ** 15, {'from': alice})
    assert multi.rewardData(reward_token)['rewardRate'] > initial_rate

    # Wait for duration to expire
    chain.mine(timedelta=1000)
    multi.notifyRewardAmount(reward_token, 10 ** 15, {'from': alice})
    assert multi.rewardData(reward_token)['rewardRate'] == initial_rate


    reward_token.approve(multi, 10 ** 19, {"from": alice})
    multi.setRewardsDistributor(reward_token, alice, {"from": alice})
    multi.notifyRewardAmount(reward_token, 10 ** 15, {'from': alice})
    with brownie.reverts("Previous rewards period must be complete before changing the duration for the new period"):
        multi.setRewardsDuration(reward_token, 9999999, {'from': alice})


# Cannot set previous rewards period
def test_reward_period_finish(multi, reward_token, alice):
    reward_token.approve(multi, 10 ** 19, {"from": alice})
    multi.setRewardsDistributor(reward_token, alice, {"from": alice})
    multi.notifyRewardAmount(reward_token, 10 ** 15, {'from': alice})
    with brownie.reverts("Previous rewards period must be complete before changing the duration for the new period"):
        multi.setRewardsDuration(reward_token, 9999999, {'from': alice})

# Can set duration after end
def test_update_reward_duration(multi, reward_token, alice, chain):
    reward_token.approve(multi, 10 ** 19, {"from": alice})
    multi.setRewardsDistributor(reward_token, alice, {"from": alice})
    multi.notifyRewardAmount(reward_token, 10 ** 15, {'from': alice})
    chain.mine(timedelta=100)
    multi.setRewardsDuration(reward_token, 1000, {'from': alice})


# Does reward per token update?
def test_reward_per_token_updates(multi, reward_token, alice, bob, base_token, chain):
    amount = 10 ** 10
    reward_token.approve(multi, 10 ** 19, {"from": alice})
    multi.setRewardsDistributor(reward_token, alice, {"from": alice})
    multi.notifyRewardAmount(reward_token, 10 ** 10, {"from": alice})

    base_token.approve(multi, amount, {"from": bob})
    multi.stake(amount, {"from": bob})
    chain.mine(timedelta=100)

    assert multi.rewardPerToken(reward_token) > 0

# Does correct balance transfer on reward set?
def test_reward_fail_on_insufficient_balance(multi, reward_token, alice):
    amount = reward_token.balanceOf(alice)
    reward_token.approve(multi, amount, {"from": alice})
    multi.setRewardsDistributor(reward_token, alice, {"from": alice})
    multi.notifyRewardAmount(reward_token, amount, {"from": alice})
    assert reward_token.balanceOf(alice) == 0
    assert multi.balanceOf(alice) == amount
 
# Fails on insufficient balance 
def test_reward_fail_on_insufficient_balance(multi, reward_token, alice):
    amount = 10 ** 30
    reward_token.approve(multi, amount, {"from": alice})
    multi.setRewardsDistributor(reward_token, alice, {"from": alice})
    with brownie.reverts():
        multi.notifyRewardAmount(reward_token, amount, {"from": alice})
 
