"""
#FIXME: update!
This module provides a single function which prompts an LLM with a users prompt and the
context/information gathered during querying the database.
"""
import ast
import logging
import openai
import pandas as pd 
import yaml
from config.load_config import settings

def extract_relevant_values(
        user_prompt: str,
        prompt_context: list[str]     
) -> pd.DataFrame:
    """
    Prompts an LLM to extract Food/Maximum Residue Limit value pairs from the extracted context based on the users input. 

    Args:
        user_prompt (str): Keywords given by the user, split by ';'. This is not enforced by code, but is a requirement.
        prompt_context list[str]: List of all sections of the PDF matching the users prompt.

    Returns:
        pd.DataFrame: Pandas DataFrame with the columns ['pesiticide', 'food', 'mrl'] extracted from the given context by an LLM.
    """
    ## faulty argument handling
    if not isinstance(user_prompt, list):
        raise TypeError(f"'user_prompt' must be a list, got {type(user_prompt).__name__}")

    ## setup 
    openai_client = openai.OpenAI(
        base_url=settings.kipitz_base_url,
        api_key=settings.kipitz_api_token
    )

    with open(settings.prompt_path, "r", encoding="utf-8") as f:
        prompts = yaml.safe_load(f)
    base_value_extraction_prompt = prompts["value_extraction_prompt"]

    extracted_data = []
    ## extract pesticides and values out of context
    for context in prompt_context:
        pesticide = context[0]
        text = context[1]
        keyword = context[2]
        prompt = base_value_extraction_prompt.format(
            prompt=keyword,
            pesticide=pesticide,
            text=text
            )
        completion = openai_client.chat.completions.create(
        model=settings.kipitz_model,
        messages=[{"role": settings.kipitz_role, "content": prompt}],   
        )
        answer = completion.choices[0].message.content
        data_list = ast.literal_eval(answer)
        data_list = [[pesticide] + sublist for sublist in data_list]
        extracted_data += data_list

    return pd.DataFrame(extracted_data, columns=['pesticide', 'food', 'mrl'])


def compare_values(
        chi_df: pd.DataFrame,
        eu_df: pd.DataFrame,
        bridge_table: dict
) -> pd.DataFrame:
    """
    FIXME: better comments/structure and this thing
    """
    comparison_dataframe = pd.DataFrame(
        columns=[
            "chi_pesticide",
            "eu_pesticide",
            "chi_food",
            "eu_food",
            "chi_mrl",
            "eu_mrl",
            "note",
            "valid_mrl"
        ]
    )

     ## setup 
    openai_client = openai.OpenAI(
        base_url=settings.kipitz_base_url,
        api_key=settings.kipitz_api_token
    )

    with open(settings.prompt_path, "r", encoding="utf-8") as f:
        prompts = yaml.safe_load(f)
    compare_all_values_prompt = prompts["compare_all_values_prompt"]

    # build the prompt
    chi_pesticides = chi_df["pesticide"].unique().tolist()
    data_listes = []
    for chi_pesticide in chi_pesticides:
        # get dataframe with just that pesticide
        chi_pest_df = chi_df[chi_df["pesticide"] == chi_pesticide]
        # get list of fitting european pesticides and their data
        eu_pest_df_list = []
        for fitting_pesticide in bridge_table[chi_pesticide]:
            match_df = eu_df[eu_df["eu_pesticide"]==fitting_pesticide]
            # only add if the eu_pesticide dataframe actually still has the pesticide ->
            # could be lost if its not yet applicable!
            if not match_df.empty:
                eu_pest_df_list.append(match_df)
        for eu_pest_df in eu_pest_df_list:
            eu_pesticide = eu_pest_df["eu_pesticide"].iloc[0]
            # now build the comparing prompt between the chi_pest_df and the eu_pest_df
            # TODO: try clear text and csv - csv first
            chi_data_csv_string = chi_pest_df[["food", "mrl"]].to_csv(index=False)
            eu_data_csv_string = eu_pest_df[["food", "mrl"]].to_csv(index=False)
            #PROMPT
            prompt = compare_all_values_prompt.format(
            chinese=chi_data_csv_string,
            european=eu_data_csv_string
            )
            completion = openai_client.chat.completions.create(
            model=settings.kipitz_model,
            messages=[{"role": settings.kipitz_role, "content": prompt}],   
            )
            answer = completion.choices[0].message.content
            print(answer)
            try:
                # [[pesticide] + sublist for sublist in data_list]
                data_list = ast.literal_eval(answer)
                for sublist in data_list:
                    #FIXME: issue with "Celeriac" which is part of multiple pesticides, check logic there again: TypeError: can only concatenate list (not "str") to list
                    ## add other values for full list, -1 for valid mrl now, actual comparison later to keep things in order
                    row = [chi_pesticide, eu_pesticide] + sublist + [-1]
                    comparison_dataframe.loc[len(comparison_dataframe)] = row
            except (ValueError, SyntaxError):
                logging.warning(f"Non list has been returned my LLM in comparing step. Check prompt, value has been lost! This was the LLMs answer: { completion.choices[0].message.content}")
                pass
    comparison_dataframe.to_csv("llmcomp.csv")
    #FIXME: ACTUAL COMPARISON LEFT :)
        