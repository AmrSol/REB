"""REB main file"""

import time

from milap.constants import (
    ANCILLARY_ASSUMPTIONS_FILE,
    EXIT_LIMIT_ASSUMPTIONS_FILE,
    MIDT_FLOW_FOLDER,
    MIDT_LOADFACTOR_FOLDER,
    OAG_TOFROM_FOLDER,
    SEA_CITY_PAIRS,
    TAX_ASSUMPTIONS_FILE,
)
from milap.csvloader import (
    AssumptionsLoader,
    FlowFolderLoader,
    LoadFactorFolderLoader,
    ToFromFolderLoader,
)
from milap.revenue import RebDataContainer, RebCalculator, RebPlotter


def template():
    """General template for development"""
    st = time.time()
    flow = FlowFolderLoader(MIDT_FLOW_FOLDER)
    flow.merge_city_pairs(
        SEA_CITY_PAIRS
    )  # I dont like this because I don't want to automatically add city pairs when importing Flow.

    reb_data = RebDataContainer(
        flow,
        LoadFactorFolderLoader(MIDT_LOADFACTOR_FOLDER),
        ToFromFolderLoader(OAG_TOFROM_FOLDER),
        AssumptionsLoader(TAX_ASSUMPTIONS_FILE),
        AssumptionsLoader(ANCILLARY_ASSUMPTIONS_FILE),
        AssumptionsLoader(EXIT_LIMIT_ASSUMPTIONS_FILE),
    )
    reb_data.paper2_preprocess()
    sea_reb_calculator = RebCalculator(reb_data)
    df, gy, re, reb = sea_reb_calculator.calculate_reb()
    # reb_plotter = RebPlotter(df, gy, re, reb, reb_data)
    # reb_plotter.plot_city_pairs()
    # reb_plotter.plot_big_6()

    # Sunny's analysis
    import pandas as pd
    import numpy as np
    import seaborn as sns
    import matplotlib.pyplot as plt
    import math

    # 1. Compare REB in city pairs departing selected city, by airlines
    def reb_by_depart(dep_city, year=2019):

        reb_city_depart = reb.loc[
            (reb["Leg Origin Airport"] == dep_city) & (reb["Year"] == year)
        ].copy()
        reb_city_depart["Airport Pair"] = (
            reb_city_depart["Leg Origin Airport"]
            + "-"
            + reb_city_depart["Leg Destination Airport"]
        )

        plt.figure(figsize=(15, 4))
        sns.barplot(
            data=reb_city_depart,
            x="Airport Pair",
            y="REB",
            hue="Leg Operating Airline",
            width=0.8,
        )
        plt.title(
            "REB comparison for routes departing " + dep_city + " in " + str(year)
        )
        plt.ylabel("REB")
        plt.xlabel("Route")
        plt.legend(title="Operating Airline", loc="lower left", bbox_to_anchor=(1, 0))
        plt.show()

    reb_by_depart("SIN")

    # 2. Airline routes REB analysis
    def airline_analysis(airline, year=2019):

        reb_airline = reb.loc[
            (reb["Leg Operating Airline"] == airline) & (reb["Year"] == year)
        ].copy()
        reb_airline["Airport Pair"] = (
            reb_airline["Leg Origin Airport"]
            + "-"
            + reb_airline["Leg Destination Airport"]
        )

        sns.barplot(
            data=reb_airline,
            x="Airport Pair",
            y="REB",
            order=reb_airline.sort_values("REB", ascending=False)["Airport Pair"],
        )
        plt.title(airline + " routes REB analysis " + str(year))
        plt.xlabel("Route")
        plt.ylabel("REB")
        plt.show()

    airline_analysis("SQ")

    # 3. Airline RASK analysis by route
    def rask_analysis(airline, year=2019):
        # getting distance data, city pairs, and slice by airline
        gy_rask = gy.merge(
            df[
                [
                    "Leg Origin Airport",
                    "Leg Destination Airport",
                    "D_trunk",
                    "Airport Pair",
                ]
            ],
            on=["Leg Origin Airport", "Leg Destination Airport"],
            how="left",
        )
        gy_rask["RASK"] = gy_rask["R_total"] / (
            gy_rask["Seats (Total)"] * gy_rask["D_trunk"]
        )
        gy_rask_sliced = gy_rask.loc[
            (gy_rask["Leg Operating Airline"] == airline) & (gy_rask["Year"] == year)
        ].copy()

        plt.figure(figsize=(12, 6))
        sns.lineplot(
            data=gy_rask_sliced, x="Month", y="RASK", hue="Airport Pair", marker="o"
        )
        plt.title(airline + " RASK analysis by route " + str(year))
        plt.xlabel("Month")
        plt.ylabel("RASK (USD)")
        plt.xticks(range(1, 13), range(1, 13))
        plt.legend(title="Routes", loc="upper left", bbox_to_anchor=(1, 1))
        plt.show()

    rask_analysis("MH")

    # 4. Revenue per equivalent-seat by route in 2019
    def r_per_eseat(airline, year=2019):
        # slice data and calculating R(total)/E-seat
        gy_rps = gy.loc[
            (gy["Leg Operating Airline"] == airline) & (gy["Year"] == year)
        ].copy()
        gy_rps["RPS"] = gy_rps["R_total"] / gy_rps["E_total"]
        gy_rps["Airport Pair"] = (
            gy_rps["Leg Origin Airport"] + "-" + gy_rps["Leg Destination Airport"]
        )
        gy_rps = gy_rps.sort_values(["Airport Pair", "Specific Aircraft Code", "Month"])

        g = sns.FacetGrid(
            gy_rps,
            col="Airport Pair",
            col_wrap=4,
            hue="Specific Aircraft Code",
            sharex=False,
        )
        g.map_dataframe(sns.scatterplot, x="Month", y="RPS", marker="o")

        g.figure.suptitle(
            airline + ": Revenue per equivalent seat by route in " + str(year)
        )
        for ax in g.axes.flat:
            ax.set_xticks(range(1, 13))
            ax.set_xticklabels(range(1, 13))
            ax.set_xlim(0.5, 12.5)
            ax.set_xlabel("Month")
            ax.tick_params(labelbottom=True)
            ax.xaxis.label.set_visible(True)
        g.set_axis_labels("Month", "R per e-seat (USD)")
        g.set_titles("Route: {col_name}")
        g.add_legend(bbox_to_anchor=(1, 0), loc="lower right")
        g.figure.tight_layout(rect=[0, 0, 1, 0.95])
        plt.show()

    r_per_eseat("D7")

    # 4.1 Revenue per equivalent seat per km by route in 2019
    def r_eseat_km(airline, year=2019):
        gy_rsk = gy.merge(
            df[
                [
                    "Leg Origin Airport",
                    "Leg Destination Airport",
                    "D_trunk",
                    "Airport Pair",
                ]
            ],
            on=["Leg Origin Airport", "Leg Destination Airport"],
            how="left",
        )
        gy_rsk["RPS"] = gy_rsk["R_total"] / gy_rsk["E_total"]
        gy_rsk["RSK"] = gy_rsk["RPS"] / gy_rsk["D_trunk"]
        gy_rsk_sliced = gy_rsk.loc[
            (gy_rsk["Leg Operating Airline"] == airline) & (gy_rsk["Year"] == year)
        ].copy()
        gy_rsk_sliced = gy_rsk_sliced.sort_values(
            ["Airport Pair", "Specific Aircraft Code", "Month"]
        )

        g = sns.FacetGrid(
            gy_rsk_sliced,
            col="Airport Pair",
            col_wrap=4,
            hue="Specific Aircraft Code",
            sharex=False,
        )
        g.map_dataframe(sns.scatterplot, x="Month", y="RSK", marker="o")

        g.figure.suptitle(
            airline + ": Revenue per equivalent seat by route in " + str(year)
        )
        for ax in g.axes.flat:
            ax.set_xticks(range(1, 13))
            ax.set_xticklabels(range(1, 13))
            ax.set_xlim(0.5, 12.5)
            ax.set_xlabel("Month")
            ax.tick_params(labelbottom=True)
            ax.xaxis.label.set_visible(True)
        g.set_axis_labels("Month", "R per e-seat (USD)")
        g.set_titles("Route: {col_name}")
        g.add_legend(bbox_to_anchor=(1, 0), loc="lower right")
        g.figure.tight_layout(rect=[0, 0, 1, 0.95])
        plt.show()

    r_eseat_km("MH")

    # 5. Passengers per route by airline (just try playing with matplotlib... not competent yet)
    def passengers_per_route():
        gy_seats_route = gy.merge(
            df[["Leg Origin Airport", "Leg Destination Airport", "Airport Pair"]],
            on=["Leg Origin Airport", "Leg Destination Airport"],
            how="left",
        )

        routes = gy_seats_route["Airport Pair"].unique()

        ncols = 5
        nrows = math.ceil(len(routes) / ncols)

        fig, axes = plt.subplots(nrows, ncols, figsize=(2 * ncols, 2 * nrows))
        axes = axes.flatten()

        for ax, route in zip(axes, routes):
            totals = (
                gy_seats_route[gy_seats_route["Airport Pair"] == route]
                .groupby("Leg Operating Airline")["Passengers"]
                .sum()
            )

            ax.pie(totals, labels=totals.index)
            ax.set_title(f"Route {route}")

        for ax in axes[len(routes) :]:
            ax.set_visible(False)

        plt.tight_layout()
        plt.show()

    passengers_per_route()

    en = time.time()
    print(f"Time taken: {en - st}")
    print()


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


if __name__ == "__main__":
    template()
    print()
    print("Amr is here.")
    print("Will this push to origin?")
    print("Sunny's first push to origin with branch protection.")
    print("Sunny's second push to origin with branch protection.")
    print("Sunny's third push to origin with branch protection.")
    print("Can I push without branching?")

# Sunny was here
# Sunny is here again and ready to push to origin.
