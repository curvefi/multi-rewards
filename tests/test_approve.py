#!/usr/bin/python3

import brownie
import pytest


# Initial accounts at zero
@pytest.mark.parametrize("idx", range(5))
def test_initial_approval_is_zero(multi_reward, accounts, idx):
    assert multi_reward.balanceOf(accounts[idx]) == 0


# New instantiation is not paused
def test_contract_not_paused(multi_reward, accounts):
    assert multi_reward.paused() is False


# Can contract be paused
def test_contract_pausable(multi_reward, accounts, alice):
    multi_reward.setPaused(True, {"from": alice})
    assert multi_reward.paused() is True


# Can contract be paused and unpaused
def test_contract_unpausable(multi_reward, accounts, alice):
    multi_reward.setPaused(True, {"from": alice})
    multi_reward.setPaused(False, {"from": alice})
    assert multi_reward.paused() is False


# Can contract be paused by a rando?
@pytest.mark.parametrize("idx", range(1, 10))
def test_contract_not_pausable_by_public(multi_reward, accounts, alice, idx):
    with brownie.reverts():
        multi_reward.setPaused(True, {"from": accounts[idx]})
    assert multi_reward.paused() is False


# Can the ownership be transferred?
def test_replace_owner(multi_reward, accounts, alice, bob):
    multi_reward.nominateNewOwner(bob, {"from": alice})
    multi_reward.acceptOwnership({"from": bob})
    assert multi_reward.owner() == bob


# Unnominated person should not be able to swipe the contract's ownership
def test_cannot_accept_unassigned_ownership(multi_reward, accounts, bob):
    phrase = "You must be nominated before you can accept ownership"
    with brownie.reverts(phrase):
        multi_reward.acceptOwnership({"from": bob})
