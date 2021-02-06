#!/usr/bin/python3

import brownie
from brownie_tokens.template import ERC20


# Only owner can call
def test_only_owner_can_call(multi, alice, bob):
    token = ERC20()
    with brownie.reverts("Only the contract owner may perform this action"):
        multi.addReward(token, alice, 60, {'from': bob})
    multi.addReward(token, alice, 60, {'from': alice})
    assert multi.rewardTokens(0) == token


# Reward was not already set (rewardDuration == 0)
def test_duration_not_prior_set(multi, alice, bob):
    token = ERC20()
    assert multi.rewardData(token)['rewardsDuration'] == 0
    multi.addReward(token, alice, 60, {'from': alice})
    assert multi.rewardData(token)['rewardsDuration'] == 60


# rewardsDistributor and rewardsDuration are set correctly
def test_rewards_properties_set(multi, alice, bob):
    token = ERC20()
    multi.addReward(token, alice, 60, {'from': alice})
    assert multi.rewardData(token)['rewardsDuration'] == 60
    assert multi.rewardData(token)['rewardsDistributor'] == alice
