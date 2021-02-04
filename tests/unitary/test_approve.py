#!/usr/bin/python3

import brownie
import pytest


# Initial accounts at zero
@pytest.mark.parametrize("idx", range(5))
def test_initial_approval_is_zero(multi, accounts, idx):
    assert multi.balanceOf(accounts[idx]) == 0


# New instantiation is not paused
def test_contract_not_paused(multi, accounts):
    assert multi.paused() is False


# Can contract be paused
def test_contract_pausable(multi, accounts, alice):
    multi.setPaused(True, {"from": alice})
    assert multi.paused() is True


# Can contract be paused and unpaused
def test_contract_unpausable(multi, accounts, alice):
    multi.setPaused(True, {"from": alice})
    multi.setPaused(False, {"from": alice})
    assert multi.paused() is False


# Only fire the pause event when the state changes
def test_only_fire_pause_event_on_state_change(multi, accounts, alice, chain):
    tx = multi.setPaused(True, {"from": alice})
    assert "PauseChanged" in tx.events
    chain.mine()
    tx = multi.setPaused(True, {"from": alice})
    assert "PauseChanged" not in tx.events


# Can contract be paused by a rando?
@pytest.mark.parametrize("idx", range(1, 10))
def test_contract_not_pausable_by_public(multi, accounts, alice, idx):
    with brownie.reverts():
        multi.setPaused(True, {"from": accounts[idx]})
    assert multi.paused() is False


# Can the ownership be transferred?
def test_replace_owner(multi, accounts, alice, bob):
    multi.nominateNewOwner(bob, {"from": alice})
    multi.acceptOwnership({"from": bob})
    assert multi.owner() == bob


# Unnominated person should not be able to swipe the contract's ownership
def test_cannot_accept_unassigned_ownership(multi, accounts, bob):
    phrase = "You must be nominated before you can accept ownership"
    with brownie.reverts(phrase):
        multi.acceptOwnership({"from": bob})


# No supply at start
def test_no_initial_supply(multi):
    assert multi.totalSupply() == 0


# No reward time at start
def test_no_last_time_reward(multi, reward_token):
    assert multi.lastTimeRewardApplicable(reward_token) == 0


# No owner earnings at start
def test_no_initial_earnings_alice(multi, reward_token, alice):
    assert multi.earned(alice, reward_token) == 0


# No bob earnings at start
def test_no_initial_earnings_bob(multi, reward_token, bob):
    assert multi.earned(bob, reward_token) == 0


# No charlie earnings at start
def test_no_initial_earnings_charlie(multi, reward_token, charlie):
    assert multi.earned(charlie, reward_token) == 0
