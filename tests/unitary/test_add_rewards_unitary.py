#!/usr/bin/python3

import brownie
from brownie_tokens.template import ERC20
from utils import withCustomError


# Only manager can call
def test_only_manager_can_call(multi, alice, bob):
    token = ERC20()
    with brownie.reverts(withCustomError('InsufficientPermission()')):
        multi.addReward(token, {"from": bob})


# Manager can add reward token
def test_manager_can_add_reward_token(multi, alice, bob):
    token = ERC20()
    multi.setManagers([alice], {"from": alice}) # alice is the owner so she can made herself the manager
    multi.addReward(token, {"from": alice})
    assert multi.rewardTokens(0) == token


# Reward Per Token works with No Supply
def test_reward_per_token_zero_supply(multi, alice):
    token = ERC20()
    multi.setManagers([alice], {"from": alice})
    multi.addReward(token, {"from": alice})
    assert multi.rewardData(token)["rewardPerToken"] == 0
