import pandas as pd


class PandasTools:
    def __init__(self):
        pass
    
    @staticmethod
    def rename_columns(df, old_columns, new_columns) -> pd.DataFrame:
        assert len(old_columns) == len(
            new_columns
        ), "The length of the old and new columns must be the same."
        rename_dict = {}
        for i, old_column in enumerate(old_columns):
            rename_dict[old_column] = new_columns[i]
        df_renamed = df.rename(columns=rename_dict)
        df_renamed = df_renamed.drop_duplicates()
        return df_renamed

    @staticmethod
    def merge_df1_and_df2(
        df1: pd.DataFrame,
        df2: pd.DataFrame,
        df1_columns: list,
        df1_merging_columns: list,
        df2_columns: list,
        df2_merging_columns: list,
        fillna_value=0,
        groupby: bool = True,
        func: str = "mean",
        weights: list[str] = None,  # type: ignore
        indicator: bool = False,
    ) -> pd.DataFrame:
        """
        Merge two DataFrames based on specified columns and perform optional groupby operations.
        Example:
        df1 = pd.DataFrame({'A': ['a', 'b', 'c'], 'B': [1, 2, 3]})
        df2 = pd.DataFrame({'A': ['a', 'b', 'c'], 'C': [4, 5, 6]})

        Args:
            df1 (pd.DataFrame): The first DataFrame to merge.
            df2 (pd.DataFrame): The second DataFrame to merge.
            df1_columns (list): The columns from df1 to include in the merged DataFrame.
            df1_merging_columns (list): The columns from df1 to use for merging.
            df2_columns (list): The columns from df2 to include in the merged DataFrame.
            df2_merging_columns (list): The columns from df2 to use for merging.
            fillna_value (Any, optional): The value to fill NaN values with. Defaults to 0.
            groupby (bool, optional): Whether to perform groupby operations. Defaults to True.
            func (str, optional): The aggregation function to apply when groupby is True. Defaults to "mean".
            weights (list[str], optional): The weight column(s) to use for weighted aggregation. Defaults to None.
            indicator (bool, optional): Whether to include an indicator column. Defaults to False.

        Returns:
            pd.DataFrame: The merged DataFrame.
        """
        
        if groupby:
            if func == "wavg":
                assert len(df2_merging_columns) == 1, "Only one column can be weighted."
                assert len(weights) == 1, "Only one weight can be used."
                dfm2 = df2.loc[:, df2_columns + df2_merging_columns + weights]
                dfm2[f"weighted_{df2_merging_columns[0]}"] = (
                    dfm2[df2_merging_columns[0]] * dfm2[weights[0]]
                )
                grouped = dfm2.groupby(df2_columns).sum()
                grouped[f"{df2_merging_columns[0]}_wavg"] = (
                    grouped[f"weighted_{df2_merging_columns[0]}"] / grouped[weights[0]]
                )
                dfm2 = grouped.reset_index()
                dfm2 = dfm2[df2_columns + [f"{df2_merging_columns[0]}_wavg"]]
                dfm2 = PandasTools.rename_columns(
                    dfm2,
                    df2_columns + [f"{df2_merging_columns[0]}_wavg"],
                    df1_columns + df1_merging_columns,
                )
            else:
                dfm2 = df2[df2_columns + df2_merging_columns]
                dfm2 = dfm2.groupby(df2_columns).agg(func).reset_index()
                dfm2 = PandasTools.rename_columns(
                    dfm2,
                    df2_columns + df2_merging_columns,
                    df1_columns + df1_merging_columns,
                )
        else:
            dfm2 = df2[df2_columns + df2_merging_columns]
            dfm2 = PandasTools.rename_columns(
                dfm2,
                old_columns=df2_columns + df2_merging_columns,
                new_columns=df1_columns + df1_merging_columns,
            )
        df1 = df1.merge(dfm2, how="left", on=df1_columns, indicator=indicator)
        df1[df1_merging_columns] = df1[df1_merging_columns].fillna(
            fillna_value
        )  # fillna depending on the column type
        return df1
    
    @staticmethod
    def column_checker(df, columns):
        if not set(columns).issubset(df.columns):
            raise ValueError(f'Columns {columns} not found in dataframe.')
        return True
    
    @staticmethod
    def unique_ordered_list(seq) -> list:
        """
        Returns a list containing unique elements from the input sequence while preserving the original order.
        
        Args:
            seq (iterable): The input sequence from which unique elements are extracted.
            
        Returns:
            list: A list containing unique elements from the input sequence in the original order.
        """
        seen = set()
        seen_add = seen.add
        return [x for x in seq if not (x in seen or seen_add(x))]
