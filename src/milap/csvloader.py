import os
import pandas as pd
from milap.constants import MIDT_FLOW_FOLDER, TAX_ASSUMPTIONS_FILE, OAG_TOFROM_FOLDER


class DataFrameFolderLoader:
    """A class to load all csv files in a folder into a single dataframe.
    """
    def __init__(self, path):
        self.path = path
        self.files = os.listdir(self.path)
        self.df = self.__load_and_combine_csv()

    def __load_and_combine_csv(self) -> pd.DataFrame:
        assert os.path.isdir(self.path), f"Directory not found: {self.path}"
        # assert all(
        #     [file.endswith(".csv") for file in os.listdir(self.path)]
        # ), f"Not all files in {self.path} are csv files"
        # files = self.files
        files = [file for file in self.files if file.endswith(".csv")]
        df_list = [pd.read_csv(os.path.join(self.path, file)) for file in files]
        df_combined = pd.concat(df_list, ignore_index=True)
        df_combined = df_combined.drop_duplicates()
        return df_combined


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class OAGFolderLoader(DataFrameFolderLoader):
    pass


class ToFromFolderLoader(DataFrameFolderLoader):
    def __init__(self, path):
        super().__init__(path)
        self.add_date_columns()
        
    def add_date_columns(self):
        if not {'Month', 'Year'}.issubset(self.df.columns):
            assert 'Time series' in self.df.columns, "Time series column not found."
            self.df['Date'] = pd.to_datetime(self.df['Time series'], format='%d/%m/%Y')
            self.df['Month'] = self.df['Date'].dt.month
            self.df['Year'] = self.df['Date'].dt.year
            



# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class MIDTFolderLoader(DataFrameFolderLoader):
    pass


class FlowFolderLoader(DataFrameFolderLoader):
    def __init__(self, path):
        super().__init__(path)
        
        
    def merge_city_pairs(self, city_pairs: dict): # There could be a way where a decorator controls the names of the columns depending on the class. 
        """Adds a column to the dataframe with the city pair for each row.

        Args:
            city_pairs (dict): A dictionary with the airport pair as the key and the city pair as the value.
        """
        self.df["Airport Pair"] = (
            self.df["Leg Origin Airport"]
            + "-"
            + self.df["Leg Destination Airport"]
        )
        self.df["City Pair"] = self.df["Airport Pair"].map(city_pairs) 


class LoadFactorFolderLoader(MIDTFolderLoader):
    pass


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class IATAFolderLoader(DataFrameFolderLoader):
    pass


class PerSegmentFolderLoader(IATAFolderLoader):
    pass


class PerODFolderLoader(IATAFolderLoader):
    pass


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class DataFrameLoader:
    def __init__(self, path):
        self.path = path
        self.df = pd.read_csv(self.path)


class AssumptionsLoader(DataFrameLoader):
    pass


if __name__ == "__main__":
    flow_folder = FlowFolderLoader(MIDT_FLOW_FOLDER)
    tofrom_folder = ToFromFolderLoader(OAG_TOFROM_FOLDER)
    tax_folder = AssumptionsLoader(TAX_ASSUMPTIONS_FILE)
    print()