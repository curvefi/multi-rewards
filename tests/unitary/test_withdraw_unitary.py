#!/usr/bin/python3

import brownie


# Can user A and user B withdraw in correct proportion?
def test_withdraw_multiples(multi, base_token, reward_token, alice, bob, charlie, chain):
    reward_token.approve(multi, 10 ** 16, {"from": alice})

    multi.setRewardsDistributor(reward_token, alice, {"from": alice})
    multi.notifyRewardAmount(reward_token, 10 ** 15, {"from": alice})

    amount = 10 ** 12
    base_token.approve(multi, amount, {"from": bob})
    multi.stake(amount, {"from": bob})
    bob_stake_timestamp = multi.lastTimeRewardApplicable(reward_token)

    base_token.approve(multi, 10 * amount, {"from": charlie})

    # chain.mine(timedelta=1)
    charlie_stake_timestamp = (multi.lastTimeRewardApplicable(reward_token),)

    if charlie_stake_timestamp == bob_stake_timestamp:
        assert multi.earned(charlie, reward_token) // 10 == multi.earned(bob, reward_token)
    else:
        assert multi.earned(charlie, reward_token) // 10 <= multi.earned(bob, reward_token)
    assert multi.balanceOf(charlie) // 10 == multi.balanceOf(bob)

    bob_init_base_balance = base_token.balanceOf(bob)
    bob_init_reward_balance = reward_token.balanceOf(bob)
    bob_exit = multi.exit({"from": bob})
    bob_exit_val = bob_exit.events["Withdrawn"].values()[1]
    bob_final_base_balance = base_token.balanceOf(bob)
    bob_final_reward_balance = reward_token.balanceOf(bob)
    bob_final_base_gain = bob_final_base_balance - bob_init_base_balance
    bob_final_reward_gain = bob_final_reward_balance - bob_init_reward_balance

    charlie_init_base_balance = base_token.balanceOf(charlie)
    charlie_init_reward_balance = reward_token.balanceOf(charlie)
    charlie_exit = multi.exit({"from": charlie})
    charlie_exit_val = charlie_exit.events["Withdrawn"].values()[1]
    charlie_final_base_balance = base_token.balanceOf(charlie)
    charlie_final_reward_balance = reward_token.balanceOf(charlie)
    charlie_final_base_gain = charlie_final_base_balance - charlie_init_base_balance
    charlie_final_reward_gain = charlie_final_reward_balance - charlie_init_reward_balance

    assert charlie_exit_val // 10 == bob_exit_val
    if charlie_stake_timestamp == bob_stake_timestamp:
        assert charlie_final_reward_gain // 10 == bob_final_reward_gain
    else:
        assert charlie_final_reward_gain // 10 <= bob_final_reward_gain
    assert charlie_final_base_gain // 10 == bob_final_base_gain


# Test for token A reward != token B reward
def test_different_reward_amounts(
    multi, base_token, reward_token, reward_token2, alice, bob, chain
):
    amount = 10 ** 12

    reward_token.approve(multi, 10 ** 15, {"from": alice})
    multi.setRewardsDistributor(reward_token, alice, {"from": alice})
    multi.notifyRewardAmount(reward_token, 10 ** 15, {"from": alice})
    first_reward_timestamp = multi.lastTimeRewardApplicable(reward_token)

    # chain.mine(timedelta=1)
    reward_token2.approve(multi, 10 ** 18, {"from": alice})
    multi.setRewardsDistributor(reward_token2, alice, {"from": alice})
    multi.notifyRewardAmount(reward_token2, 10 ** 14, {"from": alice})
    second_reward_timestamp = multi.lastTimeRewardApplicable(reward_token2)

    base_token.approve(multi, amount, {"from": bob})
    multi.stake(amount, {"from": bob})

    chain.mine(timedelta=1000)
    if first_reward_timestamp == second_reward_timestamp:
        assert multi.earned(bob, reward_token) // 10000 == multi.earned(bob, reward_token2) // 1000
    else:
        assert multi.earned(bob, reward_token) >= multi.earned(bob, reward_token2)

    bob_init_base_balance = base_token.balanceOf(bob)
    bob_init_reward_balance = reward_token.balanceOf(bob)
    bob_init_reward2_balance = reward_token2.balanceOf(bob)

    multi.exit({"from": bob})

    bob_final_base_balance = base_token.balanceOf(bob)
    bob_final_reward_balance = reward_token.balanceOf(bob)
    bob_final_reward2_balance = reward_token2.balanceOf(bob)

    bob_final_base_gain = bob_final_base_balance - bob_init_base_balance
    bob_final_reward_gain = bob_final_reward_balance - bob_init_reward_balance
    bob_final_reward2_gain = bob_final_reward2_balance - bob_init_reward2_balance

    if first_reward_timestamp == second_reward_timestamp:
        assert bob_final_reward2_gain // 1000 == bob_final_reward_gain // 10000
    else:
        assert bob_final_reward2_gain // 1000 >= bob_final_reward_gain // 10000
    assert bob_final_base_gain == amount


# Can the owner stake and then withdraw?
def test_owner_withdraw(multi, alice, base_token):
    amount = base_token.balanceOf(alice)
    multi.stake(amount, {"from": alice})
    multi.withdraw(amount, {"from": alice})
    assert multi.balanceOf(alice) == 0
    assert base_token.balanceOf(alice) == amount


# Cannot withdraw 0
def test_cannot_withdraw_zero(multi, charlie):
    assert multi.balanceOf(charlie) == 0
    with brownie.reverts():
        multi.withdraw(1, {"from": charlie})


# Cannot withdraw more than deposit
def test_cannot_withdraw_more_than_deposit(multi, alice, base_token):
    amount = base_token.balanceOf(alice)
    multi.stake(amount, {"from": alice})

    with brownie.reverts():
        multi.withdraw(1 + amount, {"from": alice})


# Supply and balance change on withdraw
def test_supply_balance_changes_on_withdraw(multi, alice, base_token):
    amount = base_token.balanceOf(alice)
    multi.stake(amount, {"from": alice})
    init_supply = multi.totalSupply()
    init_balance = multi.balanceOf(alice)
    withdraw_amount = amount // 3
    multi.withdraw(withdraw_amount, {"from": alice})
    assert multi.totalSupply() == init_supply - withdraw_amount
    assert multi.balanceOf(alice) == init_balance - withdraw_amount
    assert base_token.balanceOf(alice) == withdraw_amount


# -call reverts when attempting to withdraw > the user's balance
