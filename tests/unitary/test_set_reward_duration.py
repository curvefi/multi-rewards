#!/usr/bin/python3

import brownie
import pytest


# No reward time at start
def test_no_last_time_reward(multi, reward_token):
    assert multi.lastTimeRewardApplicable(reward_token) == 0


# Does reward for duration get updated?
def test_reward_duration_updates(multi, reward_token, issue):
    assert multi.getRewardForDuration(reward_token) > 0


# Only callable by distributor (will fail because of onlyOwner modifier)
@pytest.mark.skip_coverage
def test_reward_duration_only_distributor(multi, bob_token, alice, bob, charlie):
    with brownie.reverts():
        multi.setRewardsDuration(bob_token, 10000, {"from": alice})
    with brownie.reverts():
        multi.setRewardsDuration(bob_token, 10000, {"from": charlie})

    tx = multi.setRewardsDuration(bob_token, 10000, {"from": bob})
    assert tx.events["RewardsDurationUpdated"].values()[1] == 10000


# Cannot set previous rewards period
def test_reward_period_finish(multi, reward_token, alice):
    reward_token._mint_for_testing(alice, 10 ** 18)
    reward_token.approve(multi, 10 ** 18, {"from": alice})
    multi.setRewardsDistributor(reward_token, alice, {"from": alice})
    multi.notifyRewardAmount(reward_token, 10 ** 15, {"from": alice})
    with brownie.reverts(
        "Previous rewards period must be complete before changing the duration for the new period"
    ):
        multi.setRewardsDuration(reward_token, 9999999, {"from": alice})


# Can set duration after end
def test_update_reward_duration(multi, reward_token, alice, chain, issue):
    chain.mine(timedelta=100)
    multi.setRewardsDuration(reward_token, 1000, {"from": alice})
    assert multi.rewardData(reward_token)["rewardsDuration"] == 1000


# Does not interfere with other rewards 
def test_update_reward_duration_noninterference(multi, reward_token, alice, chain, issue, slow_token):
    reward_length = multi.rewardData(reward_token)['rewardsDuration']
    slow_length = multi.rewardData(slow_token)['rewardsDuration']
    assert reward_length > 0
    assert slow_length > 0

    chain.mine(timedelta=100)
    multi.setRewardsDuration(reward_token, 10000, {"from": alice})

    assert multi.rewardData(reward_token)["rewardsDuration"] == 10000
    assert multi.rewardData(slow_token)["rewardsDuration"] == slow_length


