#!/usr/bin/python3

import pytest
from brownie import CurveTokenV1, CurveTokenV2, CurveTokenV3


# Reset
@pytest.fixture(scope="function", autouse=True)
def isolate(fn_isolation):
    pass


# Instantiate MultiRewards contract and approve the base token for transfers
@pytest.fixture(scope="module")
def multi_reward(MultiRewards, base_token, alice, bob):
    _mr = MultiRewards.deploy(alice, base_token, {"from": alice})
    base_token.approve(_mr, 10 ** 19)
    return _mr


# Instantiate base token and provide 5 addresses a balance
@pytest.fixture(scope="module")
def base_token(accounts, alice):
    _token = CurveTokenV1.deploy("Base", "TST", 18, 10 ** 19, {"from": alice})
    for idx in range(1, 5):
        _token.mint(accounts[idx], 10 ** 19)
    return _token


# Alice creates a reward token $RWD1 for Bob
@pytest.fixture(scope="module")
def reward_token(multi_reward, accounts, alice, bob):
    _token = CurveTokenV2.deploy(
        "Reward Token 1", "RWD1", 18, 10 ** 18, {"from": alice}
    )
    _token.mint(alice, 10 ** 19)
    _token.mint(bob, 10 ** 19)
    multi_reward.addReward(_token, bob, 60, {"from": alice})
    return _token


# Alice creates a reward token $RWD2 for Charlie
@pytest.fixture(scope="module")
def reward_token2(multi_reward, accounts, alice, charlie):
    _token = CurveTokenV3.deploy("Reward Token 2", "RWD2", {"from": alice})
    _token.mint(charlie, 10 ** 19)
    multi_reward.addReward(_token, charlie, 60, {"from": alice})
    return _token


# Distribute rewards
@pytest.fixture(scope="module")
def issue_reward(multi_reward, reward_token, alice, bob, chain):
    multi_reward.stake(10 ** 18, {"from": alice})
    reward_token.approve(multi_reward, 10 ** 19)
    multi_reward.setRewardsDistributor(reward_token, alice, {"from": alice})
    multi_reward.notifyRewardAmount(reward_token, 10 ** 10, {"from": alice})
    _init_amount = reward_token.balanceOf(bob)
    chain.mine(timedelta=60)
    assert multi_reward.earned(alice, reward_token) > 0
    return _init_amount


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
