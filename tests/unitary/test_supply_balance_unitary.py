##!/usr/bin/python3

import pytest


# Initial accounts at zero
@pytest.mark.parametrize("idx", range(5))
def test_initial_approval_is_zero(multi, accounts, idx):
    assert multi.balanceOf(accounts[idx]) == 0


# No supply at start
def test_no_initial_supply(multi):
    assert multi.totalSupply() == 0


# Starting balance for owner is zero
def test_initial_stake_is_zero(multi, accounts, alice):
    assert multi.balanceOf(alice) == 0


# No owner earnings at start
def test_no_initial_earnings_alice(multi, reward_token, alice):
    assert multi.earned(alice, reward_token) == 0


# No bob earnings at start
def test_no_initial_earnings_bob(multi, reward_token, bob):
    assert multi.earned(bob, reward_token) == 0


# No charlie earnings at start
def test_no_initial_earnings_charlie(multi, reward_token, charlie):
    assert multi.earned(charlie, reward_token) == 0


# Ensure total supply and balance update correctly
def test_supply_balance_updates(multi, reward_token, alice):
    multi.stake(10000, {"from": alice})
    assert multi.balanceOf(alice) == 10000
    assert multi.totalSupply() == 10000
