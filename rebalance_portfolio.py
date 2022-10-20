#!/usr/bin/python3
import argparse
import sys

# Default, e.g. formats correctly up to $100,000.00
RIGHT_JUST_MAX = 11

# In format_dollar, add 5 spaces for padding dollar sign, negative, and cents: "$", "-" ".56"
DOLLAR_PAD = 5

FLOAT_THRESHOLD = 0.01


def format_dollar(n, rj=RIGHT_JUST_MAX):
    if n >= 0:
        return "${0:,.2f}".format(n).rjust(rj)
    else:
        return "-${0:,.2f}".format(-n).rjust(rj)


def format_perc(n):
    return "{0:.2f}%".format(100 * n).rjust(RIGHT_JUST_MAX)


def optimal_add(add_amount, fund_num, add_funds, owned, percs):
    """
    Optimal amounts to add to fund_num to make deviations from ideal proportion equal
    """
    sum_amount = sum([owned[i] for i in add_funds])
    sum_percentages = sum([percs[i] for i in add_funds])

    # Expression derived by hand
    return percs[fund_num] * (add_amount + sum_amount) / sum_percentages - owned[fund_num]


def optimal_add_others(fund_num, add_funds, owned, percentages):
    """
    Optimal amount to add to all other funds if fund_num has 0 added to make deviation from ideal proportion equal.
    """
    sum_amount = sum([owned[i] for i in add_funds])
    sum_percentages = sum([percentages[i] for i in add_funds])

    # Expression derived by hand
    return owned[fund_num] * sum_percentages / percentages[fund_num] - sum_amount


def parse_args():
    parser = argparse.ArgumentParser(description='Rebalance a Vanguard three or four-fund portfolio.')
    parser.add_argument('add', type=float, help="Amount to add to portfolio")
    parser.add_argument('vtsax', type=float, help="VTSAX amount owned")
    parser.add_argument('vtiax', type=float, help="VTIAX amount owned")
    parser.add_argument('vbtlx', type=float, help="VBTLX amount owned")
    parser.add_argument('vtibx', type=float, help="VTIBX amount owned")
    parser.add_argument('--vtsax-desired', type=float, default=0.535, help="VTSAX amount desired")
    parser.add_argument('--vtiax-desired', type=float, default=0.362, help="VTIAX amount desired")
    parser.add_argument('--vbtlx-desired', type=float, default=0.071, help="VBTLX amount desired")
    parser.add_argument('--vtibx-desired', type=float, default=0.032, help="VTIBX amount desired")
    parser.add_argument('--no-vtibx', action='store_true', help="exclude VTIBX from consideration")

    return parser.parse_args()


def main():
    global RIGHT_JUST_MAX, DOLLAR_PAD

    args = parse_args()

    added = args.add

    if args.no_vtibx:
        percentages = [args.vtsax_desired, args.vtiax_desired, args.vbtlx_desired + args.vtibx_desired]
        owned = [args.vtsax, args.vtiax, args.vbtlx]
        funds = ["VTSAX", "VTIAX", "VBTLX"]
    else:
        percentages = [args.vtsax_desired, args.vtiax_desired, args.vbtlx_desired, args.vtibx_desired]
        owned = [args.vtsax, args.vtiax, args.vbtlx, args.vtibx]
        funds = ["VTSAX", "VTIAX", "VBTLX", "VTIBX"]

    funds_str = "".join(map(lambda x: x.rjust(RIGHT_JUST_MAX), funds))
    percentages_str = "".join(map(lambda x: format_perc(x), percentages))

    print("Funds:        " + funds_str)
    print("Ideal ratios: " + percentages_str)

    current_total = sum(owned)

    most_decimals = len(str(int((max([added, current_total])))))
    RIGHT_JUST_MAX = most_decimals + DOLLAR_PAD

    print()

    if added < - current_total:
        print("You do not have enough money to withdraw the desired amount")
        sys.exit(1)

    # Initialize values
    all_funds = range(len(owned))

    # Stats before
    print("Current portfolio:")
    print()

    minimum_no_sell_add_amount = 0
    minimum_no_buy_remove_amount = 0
    for fund_num, fund_owned in enumerate(owned):
        opt_oth = optimal_add_others(fund_num, all_funds, owned, percentages)
        minimum_no_sell_add_amount = max(minimum_no_sell_add_amount, opt_oth)
        minimum_no_buy_remove_amount = min(minimum_no_buy_remove_amount, opt_oth)

        ratio = fund_owned / current_total if current_total else 0

        deviation = ratio / percentages[fund_num]

        print("Fund", funds[fund_num],
              "owned:", format_dollar(owned[fund_num]),
              "  Ratio:", format_perc(ratio),
              "  Deviation:", format_perc(deviation))

    print("Total:" + format_dollar(current_total))
    print()
    print("Adding:", format_dollar(added))
    print("Minimum needed to add to rebalance perfectly without selling:", format_dollar(minimum_no_sell_add_amount))
    print("Minimum needed to sell to rebalance perfectly without buying:", format_dollar(minimum_no_buy_remove_amount))
    print()
    print("Scheme for buying and selling funds for a perfect rebalance:")
    print()

    optimal_change = list()
    for fund_num, fund_owned in enumerate(owned):
        opt_this = optimal_add(added, fund_num, all_funds, owned, percentages)
        optimal_change.append(opt_this if opt_this < 0 and added < 0 or opt_this > 0 and added > 0 else 0)

        print("Fund", funds[fund_num],
              "owned:", format_dollar(owned[fund_num]),
              "  Add or sell:", format_dollar(opt_this))

    if added != 0:
        suboptimal = 0 > added > minimum_no_buy_remove_amount or 0 < added < minimum_no_sell_add_amount
        suboptimal_string = "suboptimal" if suboptimal else "perfect"

        print()
        print(f"Scheme for only buying or only selling funds for a {suboptimal_string} rebalance:")
        print()

        add_to_each = list()
        for v in optimal_change:
            add_to_each.append(added * v / sum(optimal_change))

        owned_plus_added = list()
        for i, v in enumerate(owned):
            owned_plus_added.append(v + add_to_each[i])

        suboptimal = False

        for fund_num, fund_owned in enumerate(owned_plus_added):
            ratio = fund_owned / (current_total + added) if current_total + added else 0

            deviation = ratio / percentages[fund_num]

            print("Fund", funds[fund_num],
                  "owned:", format_dollar(fund_owned),
                  "  To add:", format_dollar(add_to_each[fund_num]),
                  "  Ratio:", format_perc(ratio),
                  "  Deviation:", format_perc(deviation))

        if suboptimal:
            print()
            print("Buy-only or sell-only rebalance is suboptimal")


main()
