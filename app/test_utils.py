from utils import(
    # to_signed_amt_str,
    filter_daily_entries
)

# Not used anymore
# def test_to_signed_amt_str():
#     assert to_signed_amt_str(10.531, decimals=True) == "+10.53"
#     assert to_signed_amt_str(10.531, decimals=False) == "+11"

def test_filter_daily_entries():
    assert filter_daily_entries([]) == []
    # Set up some entries
    # 1. no filters, returns same list
    # 2. only date from
    # 3. Only date to
    # 4. both filters
    # 4. bad window => returns empty list
