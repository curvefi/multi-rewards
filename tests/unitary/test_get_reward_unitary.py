#!/usr/bin/python3


# Can user retrieve reward after a time cycle?
def test_get_reward(multi, base_token, reward_token, alice, issue, chain):
    amount = 10 ** 10
    init_reward_balance = reward_token.balanceOf(alice)
    base_token.approve(multi, amount, {"from": alice})
    multi.stake(amount, {"from": alice})

    chain.mine(timedelta=60)

    earnings = multi.earned(alice, reward_token)
    assert earnings > 0

    multi.getReward({"from": alice})
    final_reward_balance = reward_token.balanceOf(alice)
    assert final_reward_balance - init_reward_balance == earnings


# Reward per token over many cycles?
def test_multiuser_reward_per_token_paid(multi, reward_token, alice, chain):
    reward_token._mint_for_testing(alice, 10 ** 18, {"from": alice})
    reward_token.approve(multi, 10 ** 18, {"from": alice})
    multi.setRewardsDistributor(reward_token, alice, {"from": alice})
    multi.stake(10 ** 10, {"from": alice})

    for i in range(5):
        last_val = multi.userRewardPerTokenPaid(alice, reward_token)
        multi.notifyRewardAmount(reward_token, 10 ** 10, {"from": alice})
        chain.mine(timedelta=60)
        earnings = multi.earned(alice, reward_token)
        tx = multi.getReward()
        assert multi.userRewardPerTokenPaid(alice, reward_token) > last_val
        assert tx.events["RewardPaid"].values()[2] == earnings


# User should not be able to withdraw a reward if empty
def test_cannot_get_empty_reward(multi, reward_token, alice, chain):
    init_amount = reward_token.balanceOf(alice)
    chain.mine(timedelta=60)
    multi.getReward({"from": alice})
    final_amount = reward_token.balanceOf(alice)
    assert init_amount == final_amount


# User should not be able to withdraw a reward if empty
def test_no_action_on_empty_reward(multi, reward_token, charlie):
    tx = multi.getReward({"from": charlie})
    assert "RewardPaid" not in tx.events


# Call from a user who is staked should receive the correct amount of tokens
def test_staked_token_value(multi, reward_token, base_token, alice, charlie, issue, chain):
    amount = base_token.balanceOf(charlie)
    reward_init_bal = reward_token.balanceOf(charlie)
    base_token.approve(multi, amount, {"from": charlie})
    multi.stake(amount, {"from": charlie})
    assert base_token.balanceOf(charlie) == 0
    assert multi.balanceOf(charlie) == amount

    chain.mine(timedelta=60)
    reward_per_token = multi.rewardPerToken(reward_token)
    earned_calc = reward_per_token * amount // 10 ** 18
    assert earned_calc == multi.earned(charlie, reward_token)

    tx = multi.getReward({"from": charlie})
    assert tx.events["RewardPaid"].values()[2] == earned_calc
    assert reward_token.balanceOf(charlie) - reward_init_bal == earned_calc


# User at outset has no earnings
def test_fresh_user_no_earnings(multi, reward_token, charlie, issue):
    assert multi.earned(charlie, reward_token) == 0


# User has no earnings after staking
def test_no_earnings_upon_staking(multi, reward_token, base_token, charlie, issue):
    amount = base_token.balanceOf(charlie)
    base_token.approve(multi, amount, {"from": charlie})
    multi.stake(amount, {"from": charlie})
    assert multi.earned(charlie, reward_token) == 0


# User has earnings after staking and waiting
def test_user_accrues_rewards(multi, reward_token, base_token, charlie, issue, chain):
    amount = base_token.balanceOf(charlie)
    base_token.approve(multi, amount, {"from": charlie})
    multi.stake(amount, {"from": charlie})
    chain.mine(timedelta=60)
    period = (
        multi.lastTimeRewardApplicable(reward_token)
        - multi.rewardData(reward_token)["lastUpdateTime"]
    )
    calc_earn = period * (10 ** 18 / 60)
    assert calc_earn * 0.99 <= multi.earned(charlie, reward_token) <= calc_earn * 1.01


# User has no earnings after withdrawing
def test_no_earnings_post_withdrawal(
    multi, reward_token, slow_token, base_token, alice, charlie, issue, chain
):
    amount = base_token.balanceOf(charlie)
    base_token.approve(multi, amount, {"from": charlie})
    multi.stake(amount, {"from": charlie})
    chain.mine(timedelta=30)
    assert multi.earned(charlie, reward_token) > 0
    multi.getReward({"from": charlie})
    multi.withdraw(multi.balanceOf(charlie), {"from": charlie})
    chain.mine(timedelta=30)
    assert multi.earned(charlie, reward_token) == 0


# Call from a user who is staked should receive the correct amount of tokens
# Also confirm earnings at various stages
def test_staked_tokens_multi_durations(
    multi, reward_token, slow_token, base_token, alice, charlie, issue, chain
):
    reward_init_bal = reward_token.balanceOf(charlie)
    slow_init_bal = slow_token.balanceOf(charlie)

    amount = base_token.balanceOf(charlie)
    base_token.approve(multi, amount, {"from": charlie})
    multi.stake(amount, {"from": charlie})

    for i in range(1):
        reward_init_bal = reward_token.balanceOf(charlie)
        slow_init_bal = slow_token.balanceOf(charlie)
        charlie_paid_reward = multi.userRewardPerTokenPaid(charlie, reward_token)
        charlie_paid_slow = multi.userRewardPerTokenPaid(charlie, slow_token)
        chain.mine(timedelta=30)

        reward_per = multi.rewardPerToken(reward_token)
        slow_per = multi.rewardPerToken(slow_token)
        reward_calc = (amount * (reward_per - charlie_paid_reward)) // 10 ** 18
        slow_calc = (amount * (slow_per - charlie_paid_slow)) // 10 ** 18

        assert reward_calc == multi.earned(charlie, reward_token)
        assert slow_calc == multi.earned(charlie, slow_token)

        multi.getReward({"from": charlie})

        # Reward may have changed in the second it takes to getReward
        reward_per_act = multi.rewardPerToken(reward_token)
        slow_per_act = multi.rewardPerToken(slow_token)
        reward_calc_act = (amount * (reward_per_act - charlie_paid_reward)) // 10 ** 18
        slow_calc_act = (amount * (slow_per_act - charlie_paid_slow)) // 10 ** 18

        assert reward_token.balanceOf(charlie) - reward_init_bal == reward_calc_act
        assert slow_token.balanceOf(charlie) - slow_init_bal == slow_calc_act


# A user that has withdrawn should still be able to claim their rewards
def test_withdrawn_user_can_claim(multi, slow_token, base_token, alice, charlie, issue, chain):
    amount = base_token.balanceOf(charlie)
    reward_init_bal = slow_token.balanceOf(charlie)
    base_token.approve(multi, amount, {"from": charlie})
    multi.stake(amount, {"from": charlie})

    # Confirm charlie staked
    assert base_token.balanceOf(charlie) == 0
    assert multi.balanceOf(charlie) == amount

    chain.mine(timedelta=60)
    multi.withdraw(amount, {"from": charlie})

    # Confirm Charlie withdrew as expected
    reward_per_token = multi.rewardPerToken(slow_token)
    earned_calc = reward_per_token * amount // 10 ** 18
    assert multi.balanceOf(charlie) == 0
    assert reward_per_token > 0
    assert earned_calc == multi.earned(charlie, slow_token)

    # Does Charlie still get rewarded?
    tx = multi.getReward({"from": charlie})
    for e in tx.events["RewardPaid"]:
        if e["user"] == charlie and e["rewardsToken"] == slow_token:
            token_log = e
    assert token_log["reward"] == earned_calc
    assert slow_token.balanceOf(charlie) - reward_init_bal == earned_calc
