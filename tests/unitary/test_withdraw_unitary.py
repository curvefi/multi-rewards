#!/usr/bin/python3

import brownie


# Can user A and user B withdraw in correct proportion?
def test_withdraw_multiples(multi, base_token, slow_token, bob, charlie, chain):
    amount = 10 ** 10
    base_token._mint_for_testing(bob, amount)
    base_token._mint_for_testing(charlie, amount)

    base_token.approve(multi, amount, {"from": bob})
    multi.stake(amount, {"from": bob})
    base_token.approve(multi, 10 * amount, {"from": charlie})
    multi.stake(amount * 10, {"from": charlie})

    chain.mine(timedelta=60 * 60)
    earn_c = multi.earned(charlie, slow_token)
    earn_b = multi.earned(bob, slow_token)

    bob_init_base_balance = base_token.balanceOf(bob)
    bob_init_reward_balance = slow_token.balanceOf(bob)
    charlie_init_base_balance = base_token.balanceOf(charlie)
    charlie_init_reward_balance = slow_token.balanceOf(charlie)

    bob_exit = multi.exit({"from": bob})
    bob_exit_val = bob_exit.events["Withdrawn"].values()[1]
    bob_final_base_balance = base_token.balanceOf(bob)
    bob_final_reward_balance = slow_token.balanceOf(bob)
    bob_final_base_gain = bob_final_base_balance - bob_init_base_balance
    bob_final_reward_gain = bob_final_reward_balance - bob_init_reward_balance

    charlie_exit = multi.exit({"from": charlie})
    charlie_exit_val = charlie_exit.events["Withdrawn"].values()[1]
    charlie_final_base_balance = base_token.balanceOf(charlie)
    charlie_final_reward_balance = slow_token.balanceOf(charlie)
    charlie_final_base_gain = charlie_final_base_balance - charlie_init_base_balance
    charlie_final_reward_gain = charlie_final_reward_balance - charlie_init_reward_balance

    assert earn_b > 0
    assert earn_c > 0
    assert earn_b * 0.99 <= earn_c // 10 <= earn_b * 1.01
    assert multi.balanceOf(charlie) // 10 == multi.balanceOf(bob)
    assert charlie_exit_val // 10 == bob_exit_val
    assert (
        bob_final_reward_gain * 0.99
        <= charlie_final_reward_gain // 10
        <= bob_final_reward_gain * 1.01
    )
    assert charlie_final_base_gain // 10 == bob_final_base_gain


# Test for token A reward != token B reward
def test_different_reward_amounts(
    multi, base_token, reward_token, reward_token2, alice, bob, chain
):
    amount = 10 ** 12

    reward_token.approve(multi, 10 ** 15, {"from": alice})
    multi.setRewardsDistributor(reward_token, alice, {"from": alice})
    multi.notifyRewardAmount(reward_token, 10 ** 15, {"from": alice})

    reward_token2.approve(multi, 10 ** 18, {"from": alice})
    multi.setRewardsDistributor(reward_token2, alice, {"from": alice})
    multi.notifyRewardAmount(reward_token2, 10 ** 14, {"from": alice})

    base_token.approve(multi, amount, {"from": bob})
    multi.stake(amount, {"from": bob})

    chain.mine(timedelta=1000)

    reward_1_earnings = multi.earned(bob, reward_token)
    reward_2_earnings = multi.earned(bob, reward_token2)

    init_base_balance = base_token.balanceOf(bob)
    init_reward_balance = reward_token.balanceOf(bob)
    init_reward2_balance = reward_token2.balanceOf(bob)

    multi.exit({"from": bob})

    final_base_balance = base_token.balanceOf(bob)
    final_reward_balance = reward_token.balanceOf(bob)
    final_reward2_balance = reward_token2.balanceOf(bob)

    final_base_gain = final_base_balance - init_base_balance
    final_reward_gain = final_reward_balance - init_reward_balance
    final_reward2_gain = final_reward2_balance - init_reward2_balance

    assert reward_2_earnings * 0.98 <= reward_1_earnings // 10 <= reward_2_earnings * 1.02
    assert final_reward2_gain * 0.98 <= final_reward_gain // 10 <= final_reward2_gain * 1.02
    assert final_base_gain == amount


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


def test_cannot_withdraw_more_than_deposit_if_balance_exists(multi, alice, bob, base_token):
    amount = base_token.balanceOf(alice)
    multi.stake(amount, {"from": alice})
    base_token.approve(multi, amount, {"from": bob})
    multi.stake(amount, {"from": bob})
    with brownie.reverts("SafeMath: subtraction overflow"):
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
