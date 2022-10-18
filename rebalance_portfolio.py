#!/usr/bin/python3
import argparse
import sys

RJMAX = 11 # Default, e.g. formats correctly up to $100,000.00
DOLLAR_PAD = 5 # In format_dollar, add 5 spaces for padding dollar sign, negative, and cents: "$", "-" ".56"

def format_dollar(n, rj=RJMAX):
    if n >= 0:
        return "${0:,.2f}".format(n).rjust(rj)
    else:
        return "-${0:,.2f}".format(-n).rjust(rj)

def format_perc(n):
    return "{0:.2f}%".format(100 * n).rjust(RJMAX)

# Optimal amounts to add to fund_num to make deviations from ideal proportion equal
def optimal_add(add_amount, fund_num, add_funds, owned, percs):
    sum_amount = sum([owned[i] for i in add_funds])
    sum_percs = sum([percs[i] for i in add_funds])

    # Expression derived by hand
    return percs[fund_num] * (add_amount + sum_amount) / sum_percs - owned[fund_num]

# Optimal amount to add to all other funds if fund_num has 0 added
# to make deviation from ideal proportion equal.
def optimal_add_others(fund_num, add_funds, owned, percs):
    sum_amount = sum([owned[i] for i in add_funds])
    sum_percs = sum([percs[i] for i in add_funds])

    # Expression derived by hand
    return owned[fund_num] * sum_percs / percs[fund_num] - sum_amount

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
    global RJMAX, DOLLAR_PAD

    # Currently these are targeting the VFFVX Vanguard Target Retirement 2055 Fund, and may need to be changed manually on each rebalance.
    args = parse_args()

    added = args.add

    if args.no_vtibx:
        percs = [args.vtsax_desired, args.vtiax_desired, args.vbtlx_desired + args.vtibx_desired]
        owned = [args.vtsax, args.vtiax, args.vbtlx]
        funds = ["VTSAX", "VTIAX", "VBTLX"]
    else:
        percs = [args.vtsax_desired, args.vtiax_desired, args.vbtlx_desired, args.vtibx_desired]
        owned = [args.vtsax, args.vtiax, args.vbtlx, args.vtibx]
        funds = ["VTSAX", "VTIAX", "VBTLX", "VTIBX"]

    funds_str = "".join(map(lambda x: x.rjust(RJMAX), funds))
    percs_str = "".join(map(lambda x: format_perc(x), percs))

    print("Funds:        " + funds_str)
    print("Ideal ratios: " + percs_str)

    current_total = sum(owned)

    MOST_DECIMALS = len(str(int((max([added,current_total])))))
    RJMAX = MOST_DECIMALS + DOLLAR_PAD

    print()

    if added < - current_total:
        print("You do not have enough money to withdraw the desired amount")
        sys.exit(1)

    # Initialize values
    ALL_FUNDS = range(len(owned))
    FLOAT_THRESHOLD = 0.01
    added_remaining = added
    add_to_each = list()
    for i in range(len(owned)):
        add_to_each.append(0)

    # Main step loop
    for step in range(len(owned)):
        # TODO: Selling not yet supported
        if abs(added_remaining) < FLOAT_THRESHOLD:
            break

        # Find owned plus added in the current step
        owned_plus_added = list()
        for i,v in enumerate(owned):
            owned_plus_added.append(v + add_to_each[i])

        # For each fund, find the amounts that would need to be added to all other funds
        # in order to make each fund equally weighted to all others.
        opt_adds = list()
        for fund_num, fund_owned in enumerate(owned):
            opt_adds.append((fund_num, optimal_add_others(fund_num, ALL_FUNDS, owned_plus_added, percs)))

        # Find the two smallest such unique numbers, and the two or more funds associated
        opt_adds.sort(key=lambda x: x[1])

        lowest_opt_add_others = opt_adds[0][1]
        funds_list = [opt_adds[0][0]]
        next_fund = -1
        for fund_num, opt_add_others in opt_adds[1:]:
            if opt_add_others - lowest_opt_add_others > FLOAT_THRESHOLD:
                next_fund = fund_num
                break

            funds_list.append(fund_num)

        # Find the optimal amount to add to the given funds_list to make the deviations
        # from proportion equal across all funds in that list. If there is not enough
        # added to get to the ideal proportion deviations, then set the amount added to each
        # fund proportional to the actual maximum amount able to be added.
        to_add = optimal_add_others(next_fund, funds_list + [next_fund], owned_plus_added, percs)

        if to_add > added_remaining or to_add < FLOAT_THRESHOLD:
            to_add = added_remaining

        for fund_num in funds_list:
            opt_add = optimal_add(to_add, fund_num, funds_list, owned_plus_added, percs)
            add_to_each[fund_num] += opt_add

        # Subtract the current amount added in this step from the total amount remaining
        added_remaining -= to_add

    # Stats before
    print("Current portfolio:")
    print()

    minimum_nosell_add_amount = 0

    for fund_num, fund_owned in enumerate(owned):
        opt_oth = optimal_add_others(fund_num, ALL_FUNDS, owned, percs)
        if opt_oth > minimum_nosell_add_amount:
            minimum_nosell_add_amount = opt_oth

        ratio = fund_owned / current_total if current_total else 0

        deviation = ratio / percs[fund_num]

        print("Fund", funds[fund_num],\
            "owned:", format_dollar(owned[fund_num]),\
            "  Ratio:", format_perc(ratio),\
            "  Deviation:", format_perc(deviation))

    print("Total: " + format_dollar(current_total))

    print()
    print("Adding", format_dollar(added))

    if added < minimum_nosell_add_amount:
        print("Minimum needed to add to rebalance perfectly without selling:", format_dollar(minimum_nosell_add_amount))
        print()

        print("Scheme for buying and selling funds for a perfect rebalance:")
        print()

        for fund_num, fund_owned in enumerate(owned):
            opt_this = optimal_add(added, fund_num, ALL_FUNDS, owned, percs)

            if opt_oth > minimum_nosell_add_amount:
                minimum_nosell_add_amount = opt_oth

            deviation = fund_owned / (current_total * percs[fund_num])

            print("Fund", funds[fund_num], \
                "owned:", format_dollar(owned[fund_num]), \
                "  Add or sell:", format_dollar(opt_this))

    if added > 0:
        print()
        # TODO: Add sell-only rebalance
        print("Scheme for only buying funds for a rebalance:")
        print()

        owned_plus_added = list()
        for i, v in enumerate(owned):
            owned_plus_added.append(v + add_to_each[i])

        suboptimal = False

        for fund_num, fund_owned in enumerate(owned_plus_added):
            ratio = fund_owned / (current_total + added) if current_total + added else 0

            deviation = ratio / percs[fund_num]

            if deviation != 1.0:
                suboptimal = True

            print("Fund", funds[fund_num],\
                "owned:", format_dollar(fund_owned),\
                "  To add:", format_dollar(add_to_each[fund_num]), \
                "  Ratio:", format_perc(ratio), \
                "  Deviation:", format_perc(deviation))

        if suboptimal:
            print()
            print("Buy-only rebalance is suboptimal")

main()
