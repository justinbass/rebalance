################################################################################
# Change these
################################################################################

# Funds owned
owned = ["$50,000.00", "$30,000.00", "$6,000.00", "$3,000.00"]

# Fund ratio desired (https://investor.vanguard.com/investment-products/mutual-funds/profile/vffvx#portfolio-composition)
desired = [54.20 / 100, 36.00 / 100, 6.9 / 100, 2.9 / 100]

# Amount to add to portfolio (if exchanging existing funds, this is 0)
add = 0

# Fund ticker names
names = ["VTSAX", "VTIAX", "VBTLX", "VTABX"]

################################################################################
# Change these
################################################################################

# Default, e.g. formats correctly up to $9,999,999.99
RIGHT_JUST_MAX = 14

# In format_dollar, add 5 spaces for padding dollar sign, negative, and cents: "$", "-" ".56"
DOLLAR_PAD = 5

FLOAT_THRESHOLD = 0.01

# Format owned
owned = [float(o.replace(",", "").replace("$", "")) for o in owned]

def format_dollar(n, rj=RIGHT_JUST_MAX):
    if n >= 0:
        return "${0:,.2f}".format(n).rjust(rj)
    else:
        return "-${0:,.2f}".format(-n).rjust(rj)


def format_percentage(n):
    return "{0:.2f}%".format(100 * n).rjust(RIGHT_JUST_MAX)


def optimal_add(add_amount, fund_num, add_funds, owned, percentages):
    """
    Optimal amounts to add to fund_num to make deviations from ideal proportion equal
    """
    sum_amount = sum([owned[i] for i in add_funds])
    sum_percentages = sum([percentages[i] for i in add_funds])

    # Expression derived by hand
    return percentages[fund_num] * (add_amount + sum_amount) / sum_percentages - owned[fund_num]


def optimal_add_others(fund_num, add_funds, owned, percentages):
    """
    Optimal amount to add to all other funds if fund_num has 0 added to make deviation from ideal proportion equal.
    """
    sum_amount = sum([owned[i] for i in add_funds])
    sum_percentages = sum([percentages[i] for i in add_funds])

    # Expression derived by hand
    return owned[fund_num] * sum_percentages / percentages[fund_num] - sum_amount


def main():
    global RIGHT_JUST_MAX, DOLLAR_PAD

    funds_str = "".join(map(lambda x: x.rjust(RIGHT_JUST_MAX), names))
    percentages_str = "".join(map(lambda x: format_percentage(x), desired))

    print("Funds:        " + funds_str)
    print("Ideal ratios: " + percentages_str)

    current_total = sum(owned)

    most_decimals = len(str(int((max([add, current_total])))))
    RIGHT_JUST_MAX = most_decimals + DOLLAR_PAD

    print()

    if add < - current_total:
        print("You do not have enough money to withdraw the desired amount")
        return

    # Initialize values
    all_funds = range(len(owned))

    # Stats before
    print("Current portfolio:")
    print()

    minimum_no_sell_add_amount = 0
    minimum_no_buy_remove_amount = 0
    for fund_num, fund_owned in enumerate(owned):
        opt_oth = optimal_add_others(fund_num, all_funds, owned, desired)
        minimum_no_sell_add_amount = max(minimum_no_sell_add_amount, opt_oth)
        minimum_no_buy_remove_amount = min(minimum_no_buy_remove_amount, opt_oth)

        ratio = fund_owned / current_total if current_total else 0

        deviation = ratio / desired[fund_num]
        print("Fund", names[fund_num],
              "owned:", format_dollar(owned[fund_num]),
              "  Ratio:", format_percentage(ratio),
              "  Deviation:", format_percentage(deviation))

    print("Total:" + format_dollar(current_total))
    print()
    print("Adding:", format_dollar(add))
    print("Minimum needed to add to rebalance perfectly without selling:", format_dollar(minimum_no_sell_add_amount))
    print("Minimum needed to sell to rebalance perfectly without buying:", format_dollar(minimum_no_buy_remove_amount))
    print()
    print("Scheme for buying and selling funds for a perfect rebalance:")
    print()

    optimal_change = list()
    for fund_num, fund_owned in enumerate(owned):
        opt_this = optimal_add(add, fund_num, all_funds, owned, desired)
        optimal_change.append(opt_this if opt_this < 0 and add < 0 or opt_this > 0 and add > 0 else 0)

        print("Fund", names[fund_num],
              "owned:", format_dollar(owned[fund_num]),
              "  Add or sell:", format_dollar(opt_this))

    if add != 0:
        suboptimal = 0 > add > minimum_no_buy_remove_amount or 0 < add < minimum_no_sell_add_amount
        suboptimal_string = "suboptimal" if suboptimal else "perfect"

        print()
        print(f"Scheme for only buying or only selling funds for a {suboptimal_string} rebalance:")
        print()

        add_to_each = list()
        for v in optimal_change:
            add_to_each.append(add * v / sum(optimal_change))

        owned_plus_added = list()
        for i, v in enumerate(owned):
            owned_plus_added.append(v + add_to_each[i])

        suboptimal = False

        for fund_num, fund_owned in enumerate(owned_plus_added):
            ratio = fund_owned / (current_total + add) if current_total + add else 0

            deviation = ratio / desired[fund_num]

            print("Fund", names[fund_num],
                  "owned:", format_dollar(fund_owned),
                  "  To add:", format_dollar(add_to_each[fund_num]),
                  "  Ratio:", format_percentage(ratio),
                  "  Deviation:", format_percentage(deviation))

        if suboptimal:
            print()
            print("Buy-only or sell-only rebalance is suboptimal")


main()