"""
Provides functions to fetch data from APIs listed on the EU DataLake (https://developer.datalake.sante.service.ec.europa.eu/apis), clean it, and extract specific information using an LLM.
"""
import ast
import json
import openai
import pandas as pd
import requests
import yaml
from config.load_config import settings
from chiprag.postgres_utils import get_all_pesticides
from rapidfuzz import fuzz


def eu_fetch_api() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Fetches all pesticide, product, and MRL data from the EU DataLake.

    Cleans the retrieved data using the helper function `_eu_clean_data()`.

    Returns:
        tuple[pd.DataFrame, pd.DataFrame]: A tuple of two DataFrames —
            the first with currently applicable values,
            the second with values not yet applicable.
            Columns include: "pesticide_residue_name", "product_code", "product_name",
            "mrl_value_only", "applicability_text", "application_date".
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
    Cleans the JSON data fetched by `eu_fetch_api`.

    Removes unnecessary columns, splits the data into "applicable" and "not yet applicable" groups, 
    and sorts each group by pesticide name and then by product code.

    Returns:
        tuple[pd.DataFrame, pd.DataFrame]: A tuple of two DataFrames —
            the first with currently applicable values,
            the second with values not yet applicable.
            Columns include: "pesticide_residue_name", "product_code", "product_name",
            "mrl_value_only", "applicability_text", "application_date".
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
    not_yet_applicable_data = not_yet_applicable_data.sort_values(by=["pesticide_residue_name", "product_code"])
    # drop not yet applicable values from filtered_df
    applicable_data = filtered_df.drop(not_yet_applicable_data.index)
    # sort according to pesticide residue names and then their product code
    applicable_data = filtered_df.sort_values(by=["pesticide_residue_name", "product_code"])

    return applicable_data, not_yet_applicable_data


def get_fitting_pesticides(
        pesticide_df: pd.DataFrame
) -> dict:
    """
    Returns matching pesticides from the European database corresponding to entries in the Chinese pesticide residue dataset.

    Args:
        pesticide_df (pd.DataFrame): DataFrame containing Chinese pesticides, food products, and their maximum residue limits.

    Returns:
        FIXME: nothing as of now
    """
    # prompt to compare chinese pesticide to all european ones
    with open(settings.prompt_path, "r", encoding="utf-8") as f:
        prompts = yaml.safe_load(f)
    compare_pesticides_prompt = prompts["compare_pesticides_prompt"]

    openai_client = openai.OpenAI(
        base_url=settings.kipitz_base_url,
        api_key=settings.kipitz_api_token
    )

    # get unique pesticides from chinese data
    chi_pesticides = pesticide_df["pesticide"].unique().tolist()

    # get all pesticides from eu database
    raw_data = get_all_pesticides()
    all_eu_pesticides = [row[0].strip() for row in raw_data]

    ## to pre-filter out possible matches so we don't send too much to the LLM later on
    #TODO: could be bad practice, if there are entirely different names for pesticides! -> do domain research
    threshold = 50
    # common english words in the dataset we don't want in our match
    stop_words = {"and", "its", "as", "of", "sum", "expressed", "including", "other"}

    possible_matches_dict = {}
    # do exact search with the leftover pesticide list using an LLM
    for chi_pest in chi_pesticides:
        # pre filter
        rough_fuzzy_matches = [
            (eu_pest)
            for chi_word in chi_pest.split()
            for eu_pest in all_eu_pesticides
            for eu_word in eu_pest.split()
            if eu_word.lower() not in stop_words
            and fuzz.ratio(chi_word.lower(), eu_word.lower()) >= threshold
        ]
        # remove duplicates
        rough_fuzzy_matches = list(set(rough_fuzzy_matches))
        # prepare prompt
        prompt = compare_pesticides_prompt.format(
            chinese_pesticide=chi_pest,
            european_pesticides = rough_fuzzy_matches
        )
        # prompt LLM with the fuzzy matches
        possible_matches_list = []
        completion = openai_client.chat.completions.create(
        model=settings.kipitz_model,
        messages=[{"role": settings.kipitz_role, "content": prompt}],   
        )
        answer = completion.choices[0].message.content
        possible_matches_list = ast.literal_eval(answer)
        possible_matches_dict[chi_pest] = possible_matches_list

    return possible_matches_dict
