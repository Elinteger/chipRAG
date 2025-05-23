import json
import pandas as pd
import requests


def eu_fetch_api() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    """
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    format = "json"
    language = "EN"

    response = requests.get(f"https://api.datalake.sante.service.ec.europa.eu/sante/pesticides/pesticide_residues_mrls/download?format={format}&language={language}&api-version=v2.0", headers=headers)
    data = response.json()
    return _eu_clean_data(data)


def _eu_clean_data(
        data: json
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    """
    df = pd.DataFrame(data)
    # only get columns of importance
    filtered_df = df[["pesticide_residue_name", "product_code", "product_name", "mrl_value_only", "applicability_text", "application_date"]]
    # remove duplicates
    filtered_df = filtered_df.drop_duplicates()
    # remove non-applicable values
    filtered_df = filtered_df[~filtered_df["applicability_text"].str.contains("No longer applicable")]
    # put not yet applicable values without a date in their own table and sort them
    not_yet_applicable_data = filtered_df[filtered_df["applicability_text"].str.contains("Not yet applicable") & filtered_df["application_date"].isna()]
    not_yet_applicable_data = not_yet_applicable_data.sort_values(by="pesticide_residue_name")
    # drop not yet applicable values from filtered_df
    applicable_data = filtered_df.drop(not_yet_applicable_data.index)
    # sort according to pesticide residue names and then their product code
    applicable_data = filtered_df.sort_values(by=["pesticide_residue_name", "product_code"])

    return applicable_data, not_yet_applicable_data
