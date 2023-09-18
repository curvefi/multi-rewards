#!/usr/bin/python3

import brownie
import pytest


# New instantiation is not paused
def test_contract_not_paused(multi, accounts):
    assert multi.paused() is False


# Can contract be paused
def test_contract_pausable(multi, accounts, alice):
    multi.pause({"from": alice})
    assert multi.paused() is True


# Can contract be paused and unpaused
def test_contract_unpausable(multi, accounts, alice):
    multi.pause({"from": alice})
    multi.unpause({"from": alice})
    assert multi.paused() is False


# Emit the pause event when the pause is called
def test_emit_pause_event_on_pause(multi, accounts, alice, chain):
    tx = multi.pause({"from": alice})
    assert "Paused" in tx.events
    chain.mine()


# Can contract be paused by a rando?
@pytest.mark.parametrize("idx", range(1, 10))
def test_contract_not_pausable_by_public(multi, accounts, alice, idx):
    with brownie.reverts('Ownable: caller is not the owner'):
        multi.pause({"from": accounts[idx]})
    assert multi.paused() is False


# Can the ownership be transferred?
def test_replace_owner(multi, accounts, alice, bob):
    assert multi.owner() == alice
    multi.transferOwnership(bob, {"from": alice})
    assert multi.owner() == bob

