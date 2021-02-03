#!/usr/bin/python3

import brownie
import pytest
from brownie_tokens.template import ERC20


# Starting balance for owner is zero
def test_initial_stake_is_zero(multi, accounts, alice):
    assert multi.balanceOf(alice) == 0


# Can owner stake?
def test_owner_place_stake(multi, reward_token, alice):
    multi.stake(10000, {"from": alice})
    assert multi.balanceOf(alice) > 0


# Can other users stake?
@pytest.mark.parametrize("idx", range(1, 5))
def test_place_stake(multi, accounts, base_token, reward_token, idx):
    base_token.approve(multi, 1000000, {"from": accounts[idx]})
    multi.stake(1000000, {"from": accounts[idx]})
    assert multi.balanceOf(accounts[idx]) > 0


# Unbanked users should not be able to stake
@pytest.mark.parametrize("idx", range(6, 10))
def test_no_unbanked_stake(multi, accounts, base_token, idx):
    base_token.approve(multi, 1000000, {"from": accounts[idx]})
    with brownie.reverts():
        multi.stake(1000000, {"from": accounts[idx]})
    assert multi.balanceOf(accounts[idx]) == 0


# Will n staked addresses all earn rewards?
def test_n_rewards(multi, accounts, alice, base_token, chain):
    n = 5
    _tokens = {}
    for i in range(n):
        _tokens[i] = ERC20()
        _tokens[i]._mint_for_testing(accounts[i], 10 ** 18)
        _tokens[i].approve(multi, 10 ** 18, {"from": accounts[i]})
        base_token.approve(multi, 10 ** 18, {"from": accounts[i]})

        multi.addReward(_tokens[i], accounts[i], 60, {"from": alice})
        multi.setRewardsDistributor(_tokens[i], accounts[i], {"from": alice})
        multi.notifyRewardAmount(_tokens[i], 10 ** 10, {"from": accounts[i]})
        multi.stake(10000, {"from": accounts[i]})

    chain.mine(timedelta=120)
    for i in range(5):
        assert multi.earned(accounts[i], _tokens[i]) > 0


# Does reward for duration get updated?
def test_reward_duration_updates(multi, reward_token, issue):
    assert multi.getRewardForDuration(reward_token) > 0


# Does reward per token update?
def test_reward_per_token_updates(multi, reward_token, issue):
    assert multi.rewardPerToken(reward_token) > 0
