from pathlib import Path
from typing import Dict, Union

from brownie import Contract, compile_source

RETURN_TYPE: Dict = {
    True: " -> bool",
    False: " -> bool",
    None: "",
}

RETURN_STATEMENT: Dict = {
    True: "return True",
    False: "return False",
    None: "return",
}

FAIL_STATEMENT: Dict = {
    "revert": "raise",
    True: "return True",
    False: "return False",
    None: "return",
}

STRING_CONVERT: Dict = {
    "true": True,
    "false": False,
    "none": None,
}

with Path(__file__).parent.joinpath("token-template.vy").open() as fp:
    TEMPLATE = fp.read()


def ERC20(
    name: str = "Test Token",
    symbol: str = "TST",
    decimals: int = 18,
    success: Union[bool, str, None] = True,
    fail: Union[bool, str, None] = "revert",
) -> Contract:
    """
    Deploy an ERC20 contract for testing purposes.

    Arguments
    ---------
    name : str, optional
        Full name of the token.
    symbol: str, optional
        Short symbol for the token.
    decimals : int, optional
        Number of token decimal places.
    success : bool | None, optional
        Value returned upon successful transfer or approval.
    fail : bool | None | str, optional
        Value or action upon failed transfer or approval. Use "revert"
        to make the transaction revert.

    Returns
    -------
    Contract
        Deployed ERC20 contract
    """
    # understand success and fail when given as strings
    if isinstance(success, str) and success.lower() in STRING_CONVERT:
        success = STRING_CONVERT[success.lower()]
    if isinstance(fail, str) and fail.lower() in STRING_CONVERT:
        fail = STRING_CONVERT[fail.lower()]

    if success not in RETURN_STATEMENT:
        valid_keys = [str(i) for i in RETURN_STATEMENT.keys()]
        raise ValueError(f"Invalid value for `success`, valid options are: {', '.join(valid_keys)}")
    if fail not in FAIL_STATEMENT:
        valid_keys = [str(i) for i in FAIL_STATEMENT.keys()]
        raise ValueError(f"Invalid value for `fail`, valid options are: {', '.join(valid_keys)}")
    if None in (fail, success) and fail is not success:
        raise ValueError("Cannot use `None` for only one of `success` and `fail`.")

    source = TEMPLATE.format(
        return_type=RETURN_TYPE[success],
        return_statement=RETURN_STATEMENT[success],
        fail_statement=FAIL_STATEMENT[fail],
    )
    deployer = compile_source(source, vyper_version="0.2.8").Vyper

    return deployer.deploy(
        name,
        symbol,
        decimals,
        {"from": "0x0000000000000000000000000000000000001337", "silent": True},
    )
