#!/usr/bin/python3

import brownie
import pytest


# Starting balance for owner is zero
def test_initial_stake_is_zero(multi_reward, accounts, alice):
    assert multi_reward.balanceOf(alice) == 0


# Can owner stake?
def test_owner_place_stake(multi_reward, reward_token, alice):
    multi_reward.stake(10000, {"from": alice})
    assert multi_reward.balanceOf(alice) > 0


# Can other users stake?
@pytest.mark.parametrize("idx", range(1, 5))
def test_place_stake(multi_reward, accounts, base_token, reward_token, idx):
    base_token.approve(multi_reward, 1000000, {"from": accounts[idx]})
    multi_reward.stake(1000000, {"from": accounts[idx]})
    assert multi_reward.balanceOf(accounts[idx]) > 0


# Unbanked users should not be able to stake
@pytest.mark.parametrize("idx", range(6, 10))
def test_no_unbanked_stake(multi_reward, accounts, base_token, idx):
    base_token.approve(multi_reward, 1000000, {"from": accounts[idx]})
    with brownie.reverts():
        multi_reward.stake(1000000, {"from": accounts[idx]})
    assert multi_reward.balanceOf(accounts[idx]) == 0
