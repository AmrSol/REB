"""revenue.py contains the classes relevant to REB calculations.
It starts off with the `RebDataContainer` object that is initialised
with either `DataFrameLoader` or `DataFrameFolderLoader` objects.
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import time
import os

from milap.constants import (
    ANCILLARY_ASSUMPTIONS_FILE,
    DF_COLUMN_DICT,
    EXIT_LIMIT_ASSUMPTIONS_FILE,
    MIDT_FLOW_FOLDER,
    MIDT_LOADFACTOR_FOLDER,
    OAG_TOFROM_FOLDER,
    SEA_AIRPORT_AIRLINE_PAIRS,
    TAX_ASSUMPTIONS_FILE,
    LIST_OF_LHLCCS,
)
from milap.csvloader import (
    AssumptionsLoader,
    DataFrameFolderLoader,
    FlowFolderLoader,
    LoadFactorFolderLoader,
    ToFromFolderLoader,
)
from milap.pandastools import PandasTools as pdtools


def assert_df_size(func):
    """
    A decorator that asserts the size of a DataFrame before and after a function execution.

    Args:
        func: The function to be decorated.

    Returns:
        The result of the decorated function.
    """

    def wrapper(*args, **kwargs):
        # Assuming the first argument is 'self' and the DataFrame is an attribute of the class
        self = args[0]
        initial_row_size = self.df.shape[
            0
        ]  # Replace 'df' with the actual attribute name

        result = func(*args, **kwargs)

        final_row_size = self.df.shape[0]  # Check size after the function execution
        assert (
            initial_row_size == final_row_size
        ), "self.df size changed after function execution."

        return result

    return wrapper


def assert_gy_size(func):
    """
    A decorator that asserts the size of the 'gy' attribute of the class before and after the execution of a function.

    Args:
        func: The function to be decorated.

    Returns:
        The decorated function.
    """

    def wrapper(*args, **kwargs):
        # Assuming the first argument is 'self' and the DataFrame is an attribute of the class
        self = args[0]
        initial_row_size = self.gy.shape[
            0
        ]  # Replace 'gy' with the actual attribute name

        result = func(*args, **kwargs)

        final_row_size = self.gy.shape[0]  # Check size after the function execution
        assert (
            initial_row_size == final_row_size
        ), "self.gy size changed after function execution."

        return result

    return wrapper


def assert_re_size(func):
    """
    A decorator that asserts the size of the 're' attribute of a class before and after a function execution.

    Args:
        func: The function to be decorated.

    Returns:
        The decorated function.
    """

    def wrapper(*args, **kwargs):
        # Assuming the first argument is 'self' and the DataFrame is an attribute of the class
        self = args[0]
        initial_row_size = self.re.shape[
            0
        ]  # Replace 're' with the actual attribute name

        result = func(*args, **kwargs)

        final_row_size = self.re.shape[0]  # Check size after the function execution
        assert (
            initial_row_size == final_row_size
        ), "self.re size changed after function execution."

        return result

    return wrapper


def assert_reb_size(func):
    def wrapper(*args, **kwargs):
        # Assuming the first argument is 'self' and the DataFrame is an attribute of the class
        self = args[0]
        initial_row_size = self.reb.shape[
            0
        ]  # Replace 'reb' with the actual attribute name

        result = func(*args, **kwargs)

        final_row_size = self.reb.shape[0]  # Check size after the function execution
        assert (
            initial_row_size == final_row_size
        ), "self.reb size changed after function execution."

        return result

    return wrapper


class RebDataContainer:
    """This class is a container for all data pertaining to REB calculations.
    It contains all data cleaning and preparation steps relevant
    to Soliman et. al. 2022.
    """

    def __init__(
        self,
        flow_loader: DataFrameFolderLoader,
        load_factor_loader: DataFrameFolderLoader,
        tofrom_loader: DataFrameFolderLoader,
        tax_loader: DataFrameFolderLoader,
        ancillary_loader: DataFrameFolderLoader,
        exit_limit_loader: DataFrameFolderLoader,
    ):
        self.df = flow_loader.df
        self.df_lf = load_factor_loader.df
        self.df_to_from = tofrom_loader.df
        self.df_tax = tax_loader.df
        self.df_ancillary = ancillary_loader.df
        self.df_exit_limit = exit_limit_loader.df

        self.dataframes = {  # TODO: This dictionary is used only once and it contains the fatal flaw of not updating the dataframes after preprocessing. It should be removed.
            "df": self.df,
            "df_lf": self.df_lf,
            "df_to_from": self.df_to_from,
            "df_tax": self.df_tax,
            "df_ancillary": self.df_ancillary,
            "df_exit_limit": self.df_exit_limit,
        }

    def check_all_columns(self):
        for df_name, df in self.dataframes.items():
            pdtools.column_checker(df, DF_COLUMN_DICT[df_name])

    def filter_airlines(self, airport_airline_pairs):
        airlines_of_interest = set(
            value for sublist in airport_airline_pairs.values() for value in sublist
        )
        self.df = self.df[self.df["Leg Operating Airline"].isin(airlines_of_interest)]

    def count_stops(self, max_stops=1):
        """Method to count the number of stops in a flight into a "Stops" column.

        Args:
            max_stops (int, optional): _description_. Defaults to 1, as per REB requirements.
        """
        conditions = [
            (self.df["Leg 2"] == "   ")
            & (self.df["Leg 3"] == "   ")
            & (self.df["Leg 4"] == "   "),
            (self.df["Leg 2"] != "   ")
            & (self.df["Leg 3"] == "   ")
            & (self.df["Leg 4"] == "   "),
            (self.df["Leg 2"] != "   ")
            & (self.df["Leg 3"] != "   ")
            & (self.df["Leg 4"] == "   "),
            (self.df["Leg 2"] != "   ")
            & (self.df["Leg 3"] != "   ")
            & (self.df["Leg 4"] != "   "),
        ]

        choices = [0, 1, 2, 3]
        self.df["Stops"] = np.select(conditions, choices)
        self.df = self.df[self.df["Stops"] <= max_stops]

    def clean_to_from(self):
        # If theres Time series but no Month and Year then they should be created
        # B is assumed to be from to_from and is calculated using Flying Time column
        self.df_to_from["Date"] = pd.to_datetime(
            self.df_to_from["Time series"], format="%d/%m/%Y"
        )
        self.df_to_from["Month"] = self.df_to_from["Date"].dt.month
        self.df_to_from["Year"] = self.df_to_from["Date"].dt.year
        self.df_to_from[["Hours", "Minutes", "Seconds"]] = self.df_to_from[
            "Flying Time"
        ].str.split(":", expand=True)
        self.df_to_from[["Hours", "Minutes"]] = self.df_to_from[
            ["Hours", "Minutes"]
        ].astype(int)
        self.df_to_from["B"] = (
            self.df_to_from["Hours"] + self.df_to_from["Minutes"] / 60
        )

    def paper2_preprocess(self):
        self.check_all_columns()
        self.filter_airlines(SEA_AIRPORT_AIRLINE_PAIRS)
        self.count_stops()
        self.clean_to_from()


class RebCalculator:
    """RebCalculator calculates REB step-by-step as outlined
    in Soliman et. al. 2022.
    """

    def __init__(self, reb_data: RebDataContainer):
        self.reb_data = reb_data
        self.df = reb_data.df.loc[:, :]
        self.df_lf = reb_data.df_lf.loc[:, :]
        self.df_to_from = reb_data.df_to_from.loc[:, :]
        self.df_tax = reb_data.df_tax.loc[:, :]
        self.df_ancillary = reb_data.df_ancillary.loc[:, :]
        self.df_exit_limit = reb_data.df_exit_limit.loc[:, :]

        self.gy = None
        self.re = None
        self.reb = None

        self.time_frequency = None

        self.dataframes = {
            "df": self.df,
            "df_lf": self.df_lf,
            "df_to_from": self.df_to_from,
            "df_tax": self.df_tax,
            "df_ancillary": self.df_ancillary,
            "df_exit_limit": self.df_exit_limit,
        }

    def calculate_r_dir(self):
        conditions = [self.df["Stops"] == 0]
        choices = [self.df["Leg Avg. Base Fare (USD) Stline"] * self.df["Passengers"]]
        self.df["R_dir"] = np.select(conditions, choices)

    @assert_df_size
    def merge_feeder_distance(self):
        self.df = pdtools.merge_df1_and_df2(
            self.df,
            self.df_to_from,
            df1_columns=["Origin Airport", "Leg Origin Airport"],
            df2_columns=["Dep Airport Code", "Arr Airport Code"],
            df1_merging_columns=["D_feeder"],
            df2_merging_columns=["GCD (km)"],
        )

    @assert_df_size
    def merge_trunk_distance(self):
        self.df = pdtools.merge_df1_and_df2(
            self.df,
            self.df_to_from,
            df1_columns=["Leg Origin Airport", "Leg Destination Airport"],
            df2_columns=["Dep Airport Code", "Arr Airport Code"],
            df1_merging_columns=["D_trunk"],
            df2_merging_columns=["GCD (km)"],
        )

    @assert_df_size
    def merge_feeder_seats(self):
        # This might be subject to change
        self.df = pdtools.merge_df1_and_df2(
            self.df,
            self.df_to_from,
            df1_columns=[
                "Origin Airport",
                "Leg Origin Airport",
                "Leg 1 Operating Airline",
                "Month",
                "Year",
            ],
            df2_columns=[
                "Dep Airport Code",
                "Arr Airport Code",
                "Carrier Code",
                "Month",
                "Year",
            ],
            df1_merging_columns=["S_feeder_wavg"],
            df2_merging_columns=["Seats"],
            func="wavg",
            weights=["Seats (Total)"],
        )

    @assert_df_size
    def merge_trunk_seats(
        self,
    ):  # TODO: S_trunk should also be wieghted. And e should be merged here and weighted as well.
        # This might be subject to change
        self.df = pdtools.merge_df1_and_df2(
            self.df,
            self.df_to_from,
            df1_columns=[
                "Leg Origin Airport",
                "Leg Destination Airport",
                "Leg Operating Airline",
                "Month",
                "Year",
            ],
            df2_columns=[
                "Dep Airport Code",
                "Arr Airport Code",
                "Carrier Code",
                "Month",
                "Year",
            ],
            df1_merging_columns=["S_trunk"],
            df2_merging_columns=["Seats"],
        )

    def find_feeder_body_type(self):
        conditions = [
            (self.df["S_feeder_wavg"] < 236) & (self.df["S_feeder_wavg"] > 0),
            self.df["S_feeder_wavg"] >= 236,
        ]
        choices = ["NB", "WB"]
        self.df["Feeder_type"] = np.select(conditions, choices)

    def find_trunk_body_type(self):
        conditions = [
            (self.df["S_trunk"] < 236) & (self.df["S_trunk"] > 0),
            self.df["S_trunk"] >= 236,
        ]
        choices = ["NB", "WB"]
        self.df["Trunk_type"] = np.select(conditions, choices)

    def calculate_c_feeder(self):
        conditions = [
            (self.df["Stops"] == 1) & (self.df["Feeder_type"] == "NB"),
            (self.df["Stops"] == 1) & (self.df["Feeder_type"] == "WB"),
        ]
        choice = [
            2
            * (self.df["D_feeder"] + 2200)
            * (self.df["S_feeder_wavg"] + 211)
            * 0.0115
            / self.df["S_feeder_wavg"],
            2
            * (self.df["D_feeder"] + 277)
            * (self.df["S_feeder_wavg"] + 104)
            * 0.019
            / self.df["S_feeder_wavg"],
        ]
        self.df["C_feeder"] = np.select(conditions, choice)

    def calculate_c_trunk(self):
        conditions = [
            (self.df["Stops"] == 1) & (self.df["Trunk_type"] == "NB"),
            (self.df["Stops"] == 1) & (self.df["Trunk_type"] == "WB"),
        ]
        choice = [
            2
            * (self.df["D_trunk"] + 2200)
            * (self.df["S_trunk"] + 211)
            * 0.0115
            / self.df["S_trunk"],
            2
            * (self.df["D_trunk"] + 277)
            * (self.df["S_trunk"] + 104)
            * 0.019
            / self.df["S_trunk"],
        ]
        self.df["C_trunk"] = np.select(conditions, choice)

    def calculate_r_con(self):
        self.merge_feeder_distance()
        self.merge_trunk_distance()
        self.merge_feeder_seats()
        self.merge_trunk_seats()
        self.find_feeder_body_type()
        self.find_trunk_body_type()
        self.calculate_c_feeder()
        self.calculate_c_trunk()
        # Import the csv files unchanged
        # Calculate R_dir and R_con
        conditions = [self.df["Stops"] == 1]
        choices = [
            self.df["OD Avg. Base Fare(USD)"]
            * self.df["Passengers"]
            * (self.df["C_trunk"] / (self.df["C_trunk"] + self.df["C_feeder"]))
        ]
        self.df["R_con"] = np.select(conditions, choices)

    def calculate_yield_gross(self):
        # Group by ODs, airline, month, year, and get the r's and the p's
        self.gy = self.df.loc[
            :,
            [
                "Leg Origin Airport",
                "Leg Destination Airport",
                "Leg Operating Airline",
                "Month",
                "Year",
                "Passengers",
                "R_dir",
                "R_con",
            ],
        ]
        self.gy = (
            self.gy.groupby(
                [
                    "Leg Origin Airport",
                    "Leg Destination Airport",
                    "Leg Operating Airline",
                    "Month",
                    "Year",
                ]
            )
            .sum()
            .reset_index()
        )
        self.gy["R"] = self.gy["R_dir"] + self.gy["R_con"]
        self.gy["Yield_gross"] = self.gy["R"] / self.gy["Passengers"]

    @assert_gy_size
    def merge_tax(self):
        self.gy = pdtools.merge_df1_and_df2(
            self.gy,
            self.df_tax,
            df1_columns=["Leg Origin Airport", "Leg Destination Airport"],
            df2_columns=["Origin", "Destination"],
            df1_merging_columns=["Tax (USD)"],
            df2_merging_columns=["USD"],
        )

    @assert_gy_size
    def merge_ancillary(self):
        self.gy = pdtools.merge_df1_and_df2(
            self.gy,
            self.df_ancillary,
            df1_columns=["Leg Operating Airline"],
            df2_columns=["Leg Operating Airline"],
            df1_merging_columns=["ARPP (USD)"],
            df2_merging_columns=["ARPP($)"],
        )

    def calculate_net_yield(self):
        self.merge_tax()
        self.merge_ancillary()
        self.gy["Yield_net"] = (
            self.gy["Yield_gross"] - self.gy["Tax (USD)"] + self.gy["ARPP (USD)"]
        )

    @assert_gy_size
    def merge_load_factor(self):
        self.gy = pdtools.merge_df1_and_df2(
            self.gy,
            self.df_lf,
            df1_columns=[
                "Leg Origin Airport",
                "Leg Destination Airport",
                "Leg Operating Airline",
                "Month",
                "Year",
            ],
            df2_columns=[
                "Origin Airport",
                "Destination Airport",
                "Operating Airline",
                "Month",
                "Year",
            ],
            df1_merging_columns=["Load Factor"],
            df2_merging_columns=["Load Factor"],
        )
        self.gy["Load Factor"] = self.gy["Load Factor"] / 100

    @assert_gy_size
    def merge_seats_monthly(self):
        self.gy = pdtools.merge_df1_and_df2(
            self.gy,
            self.df_to_from,
            df1_columns=[
                "Leg Origin Airport",
                "Leg Destination Airport",
                "Leg Operating Airline",
                "Month",
                "Year",
            ],
            df2_columns=[
                "Dep Airport Code",
                "Arr Airport Code",
                "Carrier Code",
                "Month",
                "Year",
            ],
            df1_merging_columns=["Seats (Total)"],
            df2_merging_columns=["Seats (Total)"],
            func="sum",
        )

    def calculate_r_total(self):
        self.merge_load_factor()
        self.merge_seats_monthly()
        self.gy["R_total"] = (
            self.gy["Yield_net"] * self.gy["Load Factor"] * self.gy["Seats (Total)"]
        )

    @assert_gy_size
    def merge_specific_aircraft_code_and_seats(self):
        # I need specific aircraft codes for gy to merge their exit-limits onto it
        acc = self.df_to_from[
            [
                "Dep Airport Code",
                "Arr Airport Code",
                "Carrier Code",
                "Month",
                "Year",
                "Specific Aircraft Code",
                "Seats",
                "Seats (Total)",
            ]
        ]
        # I need the aircraft with the most seats for each month and year
        acc_idx = (
            acc.groupby(
                [
                    "Dep Airport Code",
                    "Arr Airport Code",
                    "Carrier Code",
                    "Month",
                    "Year",
                ]
            )["Seats (Total)"].transform("max")
            == acc["Seats (Total)"]
        )
        acc = acc[acc_idx]
        self.gy = pdtools.merge_df1_and_df2(
            self.gy,
            acc,
            df1_columns=[
                "Leg Origin Airport",
                "Leg Destination Airport",
                "Leg Operating Airline",
                "Month",
                "Year",
            ],
            df2_columns=[
                "Dep Airport Code",
                "Arr Airport Code",
                "Carrier Code",
                "Month",
                "Year",
            ],
            df1_merging_columns=["Specific Aircraft Code", "Actual Seats"],
            df2_merging_columns=["Specific Aircraft Code", "Seats"],
            groupby=False,
        )

    @assert_gy_size
    def merge_exit_limit(self):
        self.gy = pdtools.merge_df1_and_df2(
            self.gy,
            self.df_exit_limit,
            df1_columns=["Specific Aircraft Code"],
            df2_columns=["Specific Aircraft Code"],
            df1_merging_columns=["Exit Limit"],
            df2_merging_columns=["# of e-seats"],
            groupby=False,
        )

    def calculate_e(self):
        self.merge_specific_aircraft_code_and_seats()
        self.merge_exit_limit()
        self.gy["e"] = self.gy["Exit Limit"] / self.gy["Actual Seats"]
        self.gy["e"] = self.gy["e"].fillna(0)
        self.gy["E_total"] = self.gy["Seats (Total)"] * self.gy["e"]

    def calculate_re(self):
        if self.time_frequency == "yearly":
            # Summing for months here for R_total and E_total
            self.re = self.gy[
                [
                    "Leg Origin Airport",
                    "Leg Destination Airport",
                    "Leg Operating Airline",
                    "Year",
                    "R_total",
                    "E_total",
                ]
            ]
            self.re = (
                self.re.groupby(
                    [
                        "Leg Origin Airport",
                        "Leg Destination Airport",
                        "Leg Operating Airline",
                        "Year",
                    ]
                )
                .sum()
                .reset_index()
            )
        elif self.time_frequency == "monthly":
            self.re = self.gy[
                [
                    "Leg Origin Airport",
                    "Leg Destination Airport",
                    "Leg Operating Airline",
                    "Month",
                    "Year",
                    "R_total",
                    "E_total",
                ]
            ]
            self.re = (
                self.re.groupby(
                    [
                        "Leg Origin Airport",
                        "Leg Destination Airport",
                        "Leg Operating Airline",
                        "Month",
                        "Year",
                    ]
                )
                .sum()
                .reset_index()
            )
        self.re["RE"] = self.re["R_total"] / self.re["E_total"]
        self.re = self.re[self.re["RE"].notna()]

    @assert_reb_size
    def merge_b(self):
        # self.df_to_from['Flying Time'] = self.df_to_from['Flying Time'].astype(str)

        if self.time_frequency == "yearly":
            self.reb = pdtools.merge_df1_and_df2(
                self.reb,
                self.df_to_from,
                df1_columns=[
                    "Leg Origin Airport",
                    "Leg Destination Airport",
                    "Leg Operating Airline",
                    "Year",
                ],
                df2_columns=[
                    "Dep Airport Code",
                    "Arr Airport Code",
                    "Carrier Code",
                    "Year",
                ],
                df1_merging_columns=["B"],
                df2_merging_columns=["B"],
                func="wavg",
                weights=["Frequency"],
            )
        elif self.time_frequency == "monthly":
            self.reb = pdtools.merge_df1_and_df2(
                self.reb,
                self.df_to_from,
                df1_columns=[
                    "Leg Origin Airport",
                    "Leg Destination Airport",
                    "Leg Operating Airline",
                    "Month",
                    "Year",
                ],
                df2_columns=[
                    "Dep Airport Code",
                    "Arr Airport Code",
                    "Carrier Code",
                    "Month",
                    "Year",
                ],
                df1_merging_columns=["B"],
                df2_merging_columns=["B"],
                func="wavg",
                weights=["Frequency"],
            )

    def calculate_reb(self, time_frequency: str = "yearly"):
        self.time_frequency = time_frequency
        self.calculate_r_dir()
        self.calculate_r_con()
        self.calculate_yield_gross()
        self.calculate_net_yield()
        self.calculate_r_total()
        self.calculate_e()
        self.calculate_re()

        self.reb = self.re
        self.merge_b()
        self.reb["REB"] = self.reb["RE"] / self.reb["B"]

        return self.df, self.gy, self.re, self.reb


class RebPlotter:
    """RebPlotter plots the figures in Soliman et. al. 2022."""

    def __init__(self, df, gy, re, reb, reb_data: RebDataContainer):
        self.df = df
        self.gy = gy
        self.re = re
        self.reb = reb
        self.df_to_from = reb_data.df_to_from

        self.dataframes = {
            "df": self.df,
            "gy": self.gy,
            "re": self.re,
            "reb": self.reb,
        }

    def plot_city_pairs(self):
        """
        Plots a bar chart of REB (Revenue/e-seat/block hour) and a line chart of Yield/Passenger for each airline's city pairs.
        The chart also shows the average REB for each city pair and the distance between the two airports in each city pair.
        """

        self.plt_reb = self.reb
        # We are adding a city-pair column to self.plt_reb
        city_pair = {  # TODO: abstract this out
            "SIN-PER": "SIN-PER",
            "SIN-MEL": "SIN-MEL",
            "SIN-SYD": "SIN-SYD",
            "SIN-KIX": "SIN-OSA",
            "SIN-JED": "SIN-JED",
            "KUL-PER": "KUL-PER",
            "KUL-SYD": "KUL-SYD",
            "KUL-PEK": "KUL-BJS",  # AIRPORT-PAIR
            "KUL-KIX": "KUL-OSA",
            "KUL-HND": "KUL-TYO",  # AIRPORT-PAIR
            "KUL-NRT": "KUL-TYO",  # AIRPORT-PAIR
            "KUL-JED": "KUL-JED",
        }
        self.plt_reb["Airport Pair"] = (
            self.plt_reb["Leg Origin Airport"]
            + "-"
            + self.plt_reb["Leg Destination Airport"]
        )
        self.plt_reb["City Pair"] = self.plt_reb["Airport Pair"].map(city_pair)
        # We need distance between the two airports in each city pair. We will choose the average distance.
        self.plt_reb = pdtools.merge_df1_and_df2(
            self.plt_reb,
            self.df_to_from,
            df1_columns=["Leg Origin Airport", "Leg Destination Airport"],
            df2_columns=["Dep Airport Code", "Arr Airport Code"],
            df1_merging_columns=["D_trunk"],
            df2_merging_columns=["GCD (km)"],
        )
        self.plt_reb.sort_values(by="D_trunk", inplace=True)
        # We need the average REB for each city pair
        self.plt_reb = pdtools.merge_df1_and_df2(
            self.plt_reb,
            self.plt_reb,
            df1_columns=["City Pair"],
            df2_columns=["City Pair"],
            df1_merging_columns=["REB_mean"],
            df2_merging_columns=["REB"],
        )
        # We need the yield per passenger for each airport pair
        self.plt_reb = pdtools.merge_df1_and_df2(
            self.plt_reb,
            self.gy,
            df1_columns=[
                "Leg Origin Airport",
                "Leg Destination Airport",
                "Leg Operating Airline",
                "Year",
            ],
            df2_columns=[
                "Leg Origin Airport",
                "Leg Destination Airport",
                "Leg Operating Airline",
                "Year",
            ],
            df1_merging_columns=["Yield/P"],
            df2_merging_columns=["Yield_net"],
        )
        self.plt_reb["Yield/P/B"] = self.plt_reb["Yield/P"] / self.plt_reb["B"]
        # We need to label the airline models
        conditions = [
            self.plt_reb["Leg Operating Airline"].isin(["TR", "D7", "JQ"])
        ]  # TODO: variable A
        choices = ["LHLCC"]
        self.plt_reb["Airline Model"] = np.select(conditions, choices, default="FSNC")

        # The plot begins here
        fig, ax = plt.subplots(
            figsize=(15, 5)
        )  # Creates a figure with one axes for plotting
        ax2 = ax.twinx()
        # Lists of numbers
        x = np.arange(len(self.plt_reb))
        y = list(self.plt_reb["REB"])
        y2 = list(self.plt_reb["Yield/P"])
        airline_names = list(self.plt_reb["Leg Operating Airline"])
        airline_models = list(self.plt_reb["Airline Model"])
        # unique_airline_models = list(set(airline_models))
        # Plot parameters
        w = 0.65
        L = "#111111"  # 3273a8' # LHLC bar color blue
        f = "#989898"
        color_map = {"FSNC": f, "LHLCC": L}
        bar_colors = [color_map[x] for x in airline_models]
        ylim = max(y) + 0.2 * max(y)
        xlim = len(x)
        lw = 0.5
        y_cp = ylim - 2  # y position of city pair labels
        fscp = 9  # font size for city pair
        fs = 7  # font size for trunk distance
        lwavgs = 1  # linewidth for average lines
        yl = "#656565"
        y2lim = max(y2) + 1 * max(y2)
        # REB bar plot
        reb = ax.bar(x, y, w, color=bar_colors)
        ax.set_ylabel("REB - Revenue/ e-seat/ block hour (US$)")
        ax.set_xticks(x)
        ax.set_xticklabels(airline_names)
        ax.set_ylim(0, ylim)
        ax.set_xlim([0 - 0.5, xlim - 0.5])
        ax.bar_label(reb, padding=3, fmt="%.1f")
        # Yield/P plot
        yield_plot = ax2.plot(
            x, y2, ".", color=yl, label="Yield/Passenger"
        )  # changing this to a scatter plot
        ax2.set_ylabel("Yield / Passenger (US$)")
        ax2.set_ylim([0, y2lim])

        # Annotate each city pair with the city pair name at the center of the city pair range
        city_pair_lines = self.plt_reb["City Pair"].drop_duplicates().index
        # Append the total number of self.plt_reb rows to city_pair_lines so that the last city pair is annotated
        city_pair_lines = city_pair_lines.append(pd.Index([len(self.plt_reb)]))
        for i in range(len(city_pair_lines) - 1):
            bar_count = city_pair_lines[i + 1] - city_pair_lines[i]
            i_cp = city_pair_lines[i]
            if bar_count > 2:
                x_cp = i_cp + bar_count / 2 - 0.5
                ax.annotate(
                    self.plt_reb["City Pair"][i_cp],
                    xy=(x_cp, y_cp),
                    weight="bold",
                    horizontalalignment="center",
                    fontsize=fscp,
                )
                ax.annotate(
                    f"{int(self.plt_reb['D_trunk'][i_cp])} km",
                    xy=(x_cp, y_cp - 1.2),
                    horizontalalignment="center",
                    fontsize=fs,
                    style="italic",
                )
                ax.axvline(x=i_cp - 0.5, color="k", linewidth=lw)

            else:
                x_cp = i_cp + 0.5
                ax.annotate(
                    self.plt_reb["City Pair"][i_cp],
                    xy=(x_cp, y_cp),
                    weight="bold",
                    horizontalalignment="center",
                    fontsize=fscp,
                )
                ax.annotate(
                    f"{int(self.plt_reb['D_trunk'][i_cp])} km",
                    xy=(x_cp, y_cp - 1.2),
                    horizontalalignment="center",
                    fontsize=fs,
                    style="italic",
                )
                ax.axvline(x=i_cp - 0.5, color="k", linewidth=lw)
            x_l = city_pair_lines[i]
            x_l_aft = city_pair_lines[i + 1]
            mean = ax.plot(
                [x_l - 0.5, x_l_aft - 0.5],
                [self.plt_reb["REB_mean"][x_l], self.plt_reb["REB_mean"][x_l]],
                color="k",
                linewidth=lwavgs,
                linestyle="dashed",
                label="REB City-Pair mean",
            )
        # Adding the legends for the lines and bars
        lns = yield_plot + mean  # lines
        labs = [line.get_label() for line in lns]  # labels
        legend_lines = ax.legend(
            lns, labs, loc="lower center", ncol=2, bbox_to_anchor=(0, -0.17, 1.0, 0.102)
        )  # ,mode='expand'
        ax.add_artist(legend_lines)

        LHLCC_patch = mpatches.Patch(color=L, label="LHLCC")
        FSNC_patch = mpatches.Patch(color=f, label="FSNC")

        ax.legend(
            handles=[LHLCC_patch, FSNC_patch],
            loc="lower right",
            ncol=2,
            bbox_to_anchor=(0, -0.17, 0.9, 0.102),
        )

        plt.show()
        pass

    def plot_model_average(self):
        pass
        # fig, ax = plt.subplots(figsize= (3,5))
        # REB_type = self.plt_reb.groupby('Airline Model').sum().reset_index()[['Airline Model','REB','Passengers','P.REB']]
        # REB_type['REB_wa'] = REB_type['P.REB']/REB_type['Passengers']

        # airline_types = list(yield_type['Airline Type'])
        # y = list(REB_type['REB_wa'])
        # x = np.arange(len(yield_type['Airline Type']))

        # REB_plot = ax.bar(x, y, 0.6, color=[f,f])

        # ax.set_title('REB')
        # ax.set_ylabel('REB - Revenue/ e-seat/ block hour (US$)')
        # ax.set_xticks(x)
        # ax.set_xticklabels(airline_types)
        # ax.set_ylim([0,30])
        # ax.set_xlim([0-w2,1+w2])
        # ax.bar_label(REB_plot, padding=3, fmt='%.1f')

        # #Arrow
        # ax.plot([0,0,1],[26,27,27], color='k')
        # ax.arrow(1,27,0,-7,width=0.01,head_length=0.75,head_width=0.05, color='k')
        # ax.annotate('- 26.6%',xy=(0.5,27.5),horizontalalignment='center')
        # plt.show()

        # fig.tight_layout()
        # fig.savefig('p_REB_Avg.eps', format='eps')
        # fig.savefig('p_REB_Avg.png')

    def plot_big_6(
        self,
        figure_name_addons: str = "",
        savefolder: str = None,
    ):
        """The big 6 plot showing the yield, premium passengers, connecting revenue,
        and connecting passengers for each airline type.

        Args:
            figure_name_addons (str, optional): _description_. Defaults to "".
            savefolder (str, optional): _description_. Defaults to None.
        """
        if savefolder is not None:
            if not os.path.exists(savefolder):
                os.makedirs(savefolder)

        # We need to label the airline models #TODO: take it out of the function
        conditions = [self.df["Leg Operating Airline"].isin(LIST_OF_LHLCCS)]
        choices = ["LHLCC"]
        self.df["Airline Model"] = np.select(conditions, choices, default="FSNC")
        # We need to label the airline models #TODO: take it out of the function
        conditions = [self.gy["Leg Operating Airline"].isin(LIST_OF_LHLCCS)]
        choices = ["LHLCC"]
        self.gy["Airline Model"] = np.select(conditions, choices, default="FSNC")

        self.axy_data = {"year": [], "x": [], "y": [], "airline_model": []}
        self.axp_data = {"year": [], "x": [], "y": [], "airline_model": []}
        self.axa_data = {"year": [], "x": [], "y": [], "airline_model": []}
        self.axl_data = {"year": [], "x": [], "y": [], "airline_model": []}
        self.axs_data = {"year": [], "x": [], "y": [], "airline_model": []}

        self.axc_data = {
            "year": [],
            "x": [],
            "y_f_p_dir": [],
            "y_f_p_con": [],
            "y_f_r_dir": [],
            "y_f_r_con": [],
            "y_l_p_dir": [],
            "y_l_p_con": [],
            "y_l_r_dir": [],
            "y_l_r_con": [],
        }

        def append_plot_data(dictionary):
            dictionary["year"].append([year, year])
            dictionary["x"].append(x)
            dictionary["y"].append(y)
            dictionary["airline_model"].append(airline_model)

        for year in self.reb_post_plot["Year"].unique():
            self.plt_reb = self.reb_post_plot[self.reb_post_plot["Year"] == year]
            year = int(year)

            import matplotlib.ticker as mtick

            fig, (axy, axp, axc, axa, axl, axs) = plt.subplots(
                nrows=1,
                ncols=6,
                figsize=(15, 5),
                gridspec_kw={"width_ratios": [1, 1, 2, 1, 1, 1]},
            )

            # parameters #TODO: to be inserted into a dictionary attribute of the class
            w2 = 0.7  # bar width
            L = "#111111"  # 3273a8' # LHLC bar color blue
            f = "#989898"
            g = "#EBECF0"  # color for connecting revenue

            # Yield ##################################################
            # yield_type = (
            #     self.plt_reb.groupby("Airline Model")
            #     .mean()
            #     .reset_index()[["Airline Model", "Yield/P/B"]]
            # )
            yield_type = pdtools.calculate_weighted_average(
                self.plt_reb,
                value_column="Yield/P/B",
                weight_column="Passengers",
                groupby_columns=["Airline Model"],
            )

            airline_model = list(yield_type["Airline Model"])
            y = list(yield_type["Yield/P/B_wavg"])
            # y = [60, 20] # for testing drawing the arrow
            x = np.arange(len(yield_type["Airline Model"]))

            yield_plot = axy.bar(x, y, w2, color=[f, f])

            axy.set_title("YIELD")
            axy.set_ylabel("Yield/ passenger/ block hour (US$)")
            axy.set_xticks(x)
            axy.set_xticklabels(airline_model)
            ylim = [0,100]
            axy.set_ylim(ylim)
            axy.set_xlim([0 - w2, 1 + w2])
            axy.bar_label(yield_plot, padding=3, fmt="%.1f")

            # Arrow
            self.draw_u_turn_arrow(axy, y, ylim)

            append_plot_data(self.axy_data)

            # Premium Pass #######################################
            axp.set_title("PREMIUM PASS.")
            axp.set_ylabel("Premium passengers (%)")
            axp.yaxis.set_major_formatter(mtick.PercentFormatter())

            classes = self.df[self.df["Year"] == year]
            classes = (
                classes.groupby(["Airline Model", "Cabin Class"])
                .sum(numeric_only=True)
                .reset_index()[["Airline Model", "Cabin Class", "Passengers"]]
            )
            classes_total = (
                classes.groupby("Airline Model").sum(numeric_only=True).reset_index()
            )
            # remove rows with discount economy
            premium = classes[classes["Cabin Class"] != "Discount Economy"]
            premium_total = (
                premium.groupby("Airline Model").sum(numeric_only=True).reset_index()
            )
            premium_total = premium_total.rename(
                columns={"Passengers": "Premium Passengers"}
            )
            premium_percentage = pdtools.merge_df1_and_df2(
                premium_total,
                classes_total,
                df1_columns=["Airline Model"],
                df2_columns=["Airline Model"],
                df1_merging_columns=["Total Passengers"],
                df2_merging_columns=["Passengers"],
                groupby=False,
            )
            premium_percentage["Premium Percentage"] = (
                premium_percentage["Premium Passengers"]
                / premium_percentage["Total Passengers"]
                * 100
            )

            # calculated by hand
            y = list(premium_percentage["Premium Percentage"])
            x = [0, 1]

            premium_plot = axp.bar(x, y, w2, color=[f, f])

            axp.set_xticks(x)
            axp.set_xticklabels(list(premium_percentage["Airline Model"]))
            ylim = [0,30]
            axp.set_ylim(ylim)
            axp.set_xlim([0 - w2, 1 + w2])
            axp.bar_label(premium_plot, padding=3, fmt="%.1f")

            # Arrow
            self.draw_u_turn_arrow(axp, y, ylim, percentage_point=True)
            append_plot_data(self.axp_data)

            #  Connecting Revenue #######################################
            axc.set_title("CONNECTING REVENUE")
            axc.yaxis.set_major_formatter(mtick.PercentFormatter())

            cr = self.df[self.df["Year"] == year]
            cr = (
                cr.groupby(["Airline Model", "Leg Type"])
                .sum(numeric_only=True)
                .reset_index()[
                    ["Airline Model", "Leg Type", "Passengers", "R_dir", "R_con"]
                ]
            )

            F_R_dir = cr.loc[1, "R_dir"]
            F_R_con = cr.loc[0, "R_con"]
            F_P_dir = cr.loc[1, "Passengers"]
            F_P_con = cr.loc[0, "Passengers"]

            L_R_dir = cr.loc[3, "R_dir"]
            L_R_con = cr.loc[2, "R_con"]
            L_P_dir = cr.loc[3, "Passengers"]
            L_P_con = cr.loc[2, "Passengers"]

            F_P_dir_per = F_P_dir / (F_P_dir + F_P_con) * 100
            F_P_con_per = 100 - F_P_dir_per
            F_R_dir_per = F_R_dir / (F_R_dir + F_R_con) * 100
            F_R_con_per = 100 - F_R_dir_per

            L_P_dir_per = L_P_dir / (L_P_dir + L_P_con) * 100
            L_P_con_per = 100 - L_P_dir_per
            L_R_dir_per = L_R_dir / (L_R_dir + L_R_con) * 100
            L_R_con_per = 100 - L_R_dir_per

            # calculated by via index... might be a problem?
            labels = "FSNC FSNC LHLCC LHLCC".split()
            y_dir = [F_P_dir_per, F_R_dir_per, L_P_dir_per, L_R_dir_per]
            y_con = [F_P_con_per, F_R_con_per, L_P_con_per, L_R_con_per]
            x = [0, 1, 2, 3]

            cr_plot_dir = axc.bar(x, y_dir, w2, color=[f, f, f, f])
            cr_plot_con = axc.bar(x, y_con, w2, bottom=y_dir, color=[g, g, g, g])

            axc.set_xticks(x)
            axc.set_xticklabels(labels)
            axc.set_ylim([0, 100])
            axc.set_xlim([0 - w2, 3 + w2])
            axc.bar_label(cr_plot_dir, padding=-12, fmt="%.1f")

            self.axc_data["year"].append(year)
            self.axc_data["x"].append(x)
            self.axc_data["y_f_p_dir"].append(F_P_dir_per)
            self.axc_data["y_f_p_con"].append(F_P_con_per)
            self.axc_data["y_f_r_dir"].append(F_R_dir_per)
            self.axc_data["y_f_r_con"].append(F_R_con_per)
            self.axc_data["y_l_p_dir"].append(L_P_dir_per)
            self.axc_data["y_l_p_con"].append(L_P_con_per)
            self.axc_data["y_l_r_dir"].append(L_R_dir_per)
            self.axc_data["y_l_r_con"].append(L_R_con_per)

            # plot dotted diagonal lines
            axc.plot(
                [0 + w2 / 2, 1 - w2 / 2],
                [F_P_dir_per, F_R_dir_per],
                color="k",
                linestyle="--",
                linewidth=0.7,
            )

            axc.plot(
                [2 + w2 / 2, 3 - w2 / 2],
                [L_P_dir_per, L_R_dir_per],
                color="k",
                linestyle="--",
                linewidth=0.7,
            )

            fs = 9
            axc.annotate(
                "Direct Passengers",
                xy=(0, F_P_dir_per / 2 - 23 / 2),
                horizontalalignment="center",
                fontsize=fs,
                rotation=90,
            )
            axc.annotate(
                "Direct Revenue",
                xy=(1, F_R_dir_per / 2 - 23 / 2),
                horizontalalignment="center",
                fontsize=fs,
                rotation=90,
            )
            axc.annotate(
                "Direct Passengers",
                xy=(2, L_P_dir_per / 2 - 23 / 2),
                horizontalalignment="center",
                fontsize=fs,
                rotation=90,
            )
            axc.annotate(
                "Direct Revenue",
                xy=(3, L_R_dir_per / 2 - 23 / 2),
                horizontalalignment="center",
                fontsize=fs,
                rotation=90,
            )

            axc.annotate(
                "Conn.\nPass.",
                xy=(0, F_P_dir_per + 5),
                horizontalalignment="center",
                fontsize=fs,
                rotation=90,
            )
            axc.annotate(
                "Conn.\nRev.",
                xy=(1, F_R_dir_per + 5),
                horizontalalignment="center",
                fontsize=fs,
                rotation=90,
            )
            # axc.annotate(
            #     "(CR)", xy=(1.2, 75), horizontalalignment="center", fontsize=10, rotation=90
            # )
            axc.annotate(
                "Conn.\nPass.",
                xy=(2, L_P_dir_per + 5),
                horizontalalignment="center",
                rotation=90,
                fontsize=fs,
            )
            axc.annotate(
                "Conn.\nRev.",
                xy=(3, L_R_dir_per + 5),
                horizontalalignment="center",
                rotation=90,
                fontsize=fs,
            )
            # TODO: axc needs its own thing i think

            # Ancillaries #######################################
            self.gy["Ancillary Revenue"] = self.gy["ARPP (USD)"] * self.gy["Passengers"]
            self.plt_reb = pdtools.merge_df1_and_df2(
                self.plt_reb,
                self.gy,
                df1_columns=[
                    "Leg Origin Airport",
                    "Leg Destination Airport",
                    "Leg Operating Airline",
                    "Year",
                ],
                df2_columns=[
                    "Leg Origin Airport",
                    "Leg Destination Airport",
                    "Leg Operating Airline",
                    "Year",
                ],
                df1_merging_columns=["Ancillary Revenue"],
                df2_merging_columns=["Ancillary Revenue"],
                func="sum",
            )
            self.plt_reb["Ancillary Revenue/P/B"] = (
                self.plt_reb["Ancillary Revenue"]
                / self.plt_reb["Passengers"]
                / self.plt_reb["B"]
            )
            ancillary = pdtools.calculate_weighted_average(
                df=self.plt_reb,
                value_column="Ancillary Revenue/P/B",
                weight_column="Passengers",
                groupby_columns=["Airline Model"],
            )
            y = np.array(ancillary["Ancillary Revenue/P/B_wavg"])
            x = [0, 1]

            an_plot = axa.bar(x, y, w2, color=[f, f])
            axa.set_title("ANCILLARIES")

            axa.set_ylabel("Ancillary rev./ pass./ block hour (US$)")
            axa.set_xticks(x)
            axa.set_xticklabels(list(ancillary["Airline Model"]))
            ylim = [0,6]
            axa.set_ylim(ylim)
            axa.set_xlim([0 - w2, 1 + w2])
            axa.bar_label(an_plot, padding=3, fmt="%.1f")

            # Arrow
            self.draw_u_turn_arrow(axa, y, ylim)

            append_plot_data(self.axa_data)

            # Load Factor #######################################
            axl.set_title("LOAD FACTORS")
            axl.set_ylabel("Load Factor (%)")
            import matplotlib.ticker as mtick

            axl.yaxis.set_major_formatter(mtick.PercentFormatter())

            # lf = (
            #     self.gy.groupby(["Airline Model"])
            #     .mean()
            #     .reset_index()[["Airline Model", "Load Factor"]]
            # )
            gy = self.gy[self.gy["Year"] == year]
            lf = pdtools.calculate_weighted_average(
                df=gy,
                value_column="Load Factor",
                weight_column="Passengers",
                groupby_columns=["Airline Model"],
            )

            # calculated by hand
            y = np.array(lf["Load Factor_wavg"]) * 100
            x = [0, 1]

            lf_plot = axl.bar(x, y, w2, color=[f, f])

            axl.set_ylabel("Load factor (%)")
            axl.set_xticks(x)
            axl.set_xticklabels(list(lf["Airline Model"]))
            ylim = [50, 100]
            axl.set_ylim(ylim)
            axl.set_xlim([0 - w2, 1 + w2])
            axl.bar_label(lf_plot, padding=3, fmt="%.1f")

            # Arrow
            self.draw_u_turn_arrow(axl, y, ylim, percentage_point=True)

            append_plot_data(self.axl_data)

            # Seat Density #######################################
            axs.set_title("SEAT DENSITY")
            axs.set_ylabel("Seats/ e-seat (%)")
            axs.yaxis.set_major_formatter(mtick.PercentFormatter())

            # sd = (
            #     self.plt_reb.groupby(["Airline Model"])
            #     .mean()
            #     .reset_index()[["Airline Model", "s/e"]]
            # )

            self.plt_reb = pdtools.merge_df1_and_df2(
                self.plt_reb,
                self.gy,
                df1_columns=[
                    "Leg Origin Airport",
                    "Leg Destination Airport",
                    "Leg Operating Airline",
                    "Year",
                ],
                df2_columns=[
                    "Leg Origin Airport",
                    "Leg Destination Airport",
                    "Leg Operating Airline",
                    "Year",
                ],
                df1_merging_columns=["Seats (Total)"],
                df2_merging_columns=["Seats (Total)"],
                func="sum",
            )

            self.plt_reb["s/e"] = (
                self.plt_reb["Seats (Total)"] / self.plt_reb["E_total"] * 100
            )
            sd = pdtools.calculate_weighted_average(
                df=self.plt_reb,
                value_column="s/e",
                weight_column="Passengers",
                groupby_columns=["Airline Model"],
            )
            # calculated by hand
            y = np.array(sd["s/e_wavg"])
            x = [0, 1]

            sd_plot = axs.bar(x, y, w2, color=[f, f])

            axs.set_xticks(x)
            axs.set_xticklabels(list(sd["Airline Model"]))
            ylim = [0, 100]
            axs.set_ylim(ylim)
            axs.set_xlim([0 - w2, 1 + w2])
            axs.bar_label(sd_plot, padding=3, fmt="%.1f")

            # Arrow
            self.draw_u_turn_arrow(axs, y, ylim, percentage_point=True)

            append_plot_data(self.axs_data)

            fig.tight_layout()
            # plt.show()
            fig.savefig(
                f"{savefolder}/{year}_{figure_name_addons}_reb_big6.png",
                bbox_inches="tight",
                dpi=250,
            )
            # fig.savefig(
            #     f"{savefolder}/{year}_{figure_name_addons}_reb_big6.svg",
            #     bbox_inches="tight",
            # )

            plt.close()


if __name__ == "__main__":
    st = time.time()
    reb_data = RebDataContainer(
        FlowFolderLoader(MIDT_FLOW_FOLDER),
        LoadFactorFolderLoader(MIDT_LOADFACTOR_FOLDER),
        ToFromFolderLoader(OAG_TOFROM_FOLDER),
        AssumptionsLoader(TAX_ASSUMPTIONS_FILE),
        AssumptionsLoader(ANCILLARY_ASSUMPTIONS_FILE),
        AssumptionsLoader(EXIT_LIMIT_ASSUMPTIONS_FILE),
    )
    reb_data.paper2_preprocess()
    reb_calculator = RebCalculator(reb_data)
    df, gy, re, reb = reb_calculator.calculate_reb()
    reb_plotter = RebPlotter(df, gy, re, reb, reb_data)
    reb_plotter.plot_city_pairs()
    reb_plotter.plot_model_average()
    en = time.time()
    print(f"Time taken: {en-st}")
    print()
