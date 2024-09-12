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
    reb_plotter = RebPlotter(df, gy, re, reb, reb_data)
    reb_plotter.plot_city_pairs()

    en = time.time()
    print(f"Time taken: {en - st}")

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


if __name__ == "__main__":
    template()
    print()
