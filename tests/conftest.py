#!/usr/bin/python3

import pytest
from brownie_tokens.template import ERC20


# Reset
@pytest.fixture(scope="function", autouse=True)
def isolate(fn_isolation):
    pass


# Instantiate MultiRewards contract and approve the base token for transfers
@pytest.fixture(scope="module")
def multi(MultiRewards, base_token, alice, bob):
    _mr = MultiRewards.deploy(alice, base_token, {"from": alice})
    base_token.approve(_mr, 10 ** 19, {"from": alice})
    return _mr


# Instantiate base token and provide 5 addresses a balance
@pytest.fixture(scope="module")
def base_token(accounts, alice):
    token = ERC20()
    token._mint_for_testing(alice, 10 ** 18, {"from": alice})
    for idx in range(1, 5):
        token._mint_for_testing(accounts[idx], 10 ** 19)
    return token


# Alice creates a reward token $RWD1 for Bob
@pytest.fixture(scope="module")
def reward_token(multi, accounts, alice, bob):
    _token = ERC20()
    _token._mint_for_testing(alice, 10 ** 18, {"from": alice})
    _token._mint_for_testing(bob, 10 ** 19)
    multi.addReward(_token, bob, 60, {"from": alice})
    return _token


# Alice creates a reward token $RWD1 for Bob
@pytest.fixture(scope="module")
def slow_token(multi, accounts, alice):
    slow_token = ERC20()
    amount = 10 ** 19
    slow_token._mint_for_testing(alice, amount)
    multi.addReward(slow_token, alice, 2630000, {"from": alice})
    slow_token.approve(multi, amount, {"from": alice})
    multi.setRewardsDistributor(slow_token, alice, {"from": alice})
    multi.notifyRewardAmount(slow_token, amount, {"from": alice})
    return slow_token


# Alice creates a reward token $RWD2 for Charlie
@pytest.fixture(scope="module")
def reward_token2(multi, accounts, alice, charlie):
    _token = ERC20()
    _token._mint_for_testing(alice, 10 ** 18, {"from": alice})
    _token._mint_for_testing(charlie, 10 ** 18)
    multi.addReward(_token, charlie, 60, {"from": alice})
    return _token


# Set a reward
@pytest.fixture(scope="module")
def issue(multi, reward_token, alice, bob, chain):
    reward_token.approve(multi, 10 ** 18, {"from": alice})
    multi.setRewardsDistributor(reward_token, alice, {"from": alice})
    multi.notifyRewardAmount(reward_token, 10 ** 18, {"from": alice})
    init_amount = reward_token.balanceOf(alice)
    return init_amount


# Set a reward
@pytest.fixture(scope="module")
def bob_token(multi, reward_token, alice, bob, chain):
    multi.setRewardsDistributor(reward_token, bob, {"from": alice})
    reward_token.approve(multi, 10 ** 18, {"from": bob})
    multi.notifyRewardAmount(reward_token, 10 ** 18, {"from": bob})
    return reward_token


# Transfer a random token by err
@pytest.fixture(scope="module")
def err_token(multi, reward_token, alice, bob, chain):
    err_token = ERC20()
    amount = 10 ** 18
    err_token._mint_for_testing(alice, amount, {"from": alice})
    err_token.approve(multi, amount, {"from": alice})
    err_token.transfer(multi, amount, {"from": alice})

    return err_token


# Hi Alice
@pytest.fixture(scope="session")
def alice(accounts):
    yield accounts[0]


# Hey-a Bob
@pytest.fixture(scope="session")
def bob(accounts):
    yield accounts[1]


# Don't forget Charlie
@pytest.fixture(scope="session")
def charlie(accounts):
    yield accounts[2]
