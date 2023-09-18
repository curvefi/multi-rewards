#!/usr/bin/python3

import pytest
from web3 import Web3
import brownie
from brownie_tokens.template import ERC20


def test_only_owner_call_set_managers(multi, alice, bob):
    with brownie.reverts('Ownable: caller is not the owner'):
        multi.setManagers([bob], {"from": bob})

    with brownie.reverts('Ownable: caller is not the owner'):
        multi.removeManagers([bob], {"from": bob})


def test_owner_call_set_managers(multi, alice, bob):
    assert multi.managers(bob) == False
    multi.setManagers([bob], {"from": alice})
    assert multi.managers(bob) == True

    multi.removeManagers([bob], {"from": alice})
    assert multi.managers(bob) == False

