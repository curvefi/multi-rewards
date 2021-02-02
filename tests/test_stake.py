#!/usr/bin/python3

import brownie
import pytest


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
