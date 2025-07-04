"""
Functions that prompt a large language model (LLM) and return their outputs as pandas DataFrames.
"""
import ast
import logging
import numpy as np
import openai
import pandas as pd
import re
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
    ## extract pesticides and values with context/text chunks
    #TODO: takes a couple minutes for big prompt_context lists, perhaps parallelize?
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
        try:
            ## answer cleaning
            clean_answer = answer.strip()
            # ensure the answer starts with '[['
            flat_start = re.sub(r'\s+', '', clean_answer[:10])
            if not flat_start.startswith("[["):
                clean_answer = "[[" + clean_answer.lstrip("[").lstrip()
            # ensure the answer ends with ']]'
            flat_end = re.sub(r'\s+', '', clean_answer[-10:])
            if not flat_end.endswith("]]"):
                clean_answer = clean_answer.rstrip()
                if clean_answer.endswith("],"):
                    clean_answer = clean_answer[:-1] + "]]"
                elif clean_answer.endswith("]"):
                    clean_answer += "]"
                else:
                    clean_answer += "]]"

            answer = clean_answer

            data_list = ast.literal_eval(answer)
            # normalize to a list of lists, catch non nested lists
            # is doubled logic with LLM drifting, but never change a running system
            if isinstance(data_list, list):
                if all(isinstance(item, list) for item in data_list):
                    # already a list of lists
                    normalized_data = data_list
                else:
                    normalized_data = [data_list]

            normalized_data = [[pesticide] + sublist for sublist in normalized_data]
            extracted_data += normalized_data
        except (ValueError, SyntaxError) as e:
            logging.warning(f"Error type: {type(e).__name__}, Message: {e}")
            logging.warning(f"Not fully correctly formatted output by LLM. Check prompt, value has been lost! This was the LLMs answer: {completion.choices[0].message.content}\nand this the cleaned answer: {answer}")
            pass

    return pd.DataFrame(extracted_data, columns=['pesticide', 'food', 'mrl'])


def compare_values(
        chi_df: pd.DataFrame,
        eu_df: pd.DataFrame,
        bridge_table: dict
) -> pd.DataFrame:
    """
    Prompts an LLM to create a comparison by matching European pesticide Maximum Residue Limit (MRL) values to Chinese MRL values.  
    Cleans the response and determines the valid MRL for each entry.

    Args:
        chi_df (pd.DataFrame): DataFrame containing Chinese pesticide information.
        eu_df (pd.DataFrame): DataFrame containing European pesticide information.
        bridge_table (dict): Dictionary mapping Chinese pesticide names to European pesticide names.

    Returns:
        pd.DataFrame: DataFrame comparing both datasets, including notes on the certainty of each result.
    """
    # create the dataframe for the final comparison
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
        ])

    ## setup 
    openai_client = openai.OpenAI(
        base_url=settings.kipitz_base_url,
        api_key=settings.kipitz_api_token
    )
    with open(settings.prompt_path, "r", encoding="utf-8") as f:
        prompts = yaml.safe_load(f)
    compare_all_values_prompt = prompts["compare_all_values_prompt"]

    ## prompt the LLM
    chi_pesticides = chi_df["pesticide"].unique().tolist()
    for chi_pesticide in chi_pesticides:
        # get dataframe with just that pesticide
        # pesticide, food, mrl
        chi_pest_df = chi_df[chi_df["pesticide"] == chi_pesticide]
        # get list of fitting european pesticides and their data
        eu_pest_df_list = []

        # if no european counterparts could be found to the chinese pesticide, add default line to final dataframe
        if len(bridge_table[chi_pesticide]) == 0:
            #TODO: maybe optimize this code, is currently just a (functioning) prove of concept
            df_to_add = chi_df[chi_df["pesticide"]==chi_pesticide]
            # pesticide, eu_pesticide, food, mrl
            df_to_add.insert(1, 'eu_pesticide', "/")
            # pesticide, eu_pesticide, food, eu_food, mrl
            df_to_add.insert(3, 'eu_food', "/")
            # pesticide, eu_pesticide, food, eu_food, mrl, eu_mrl
            df_to_add.insert(5, 'eu_mrl', "/")
            # pesticide, eu_pesticide, food, eu_food, mrl, eu_mrl, note
            df_to_add.insert(6, 'note', "No fitting eu-pesticide found.")
            # pesticide, eu_pesticide, food, eu_food, mrl, eu_mrl, note, valid_mrl
            df_to_add.insert(7, 'valid_mrl', "/")
            # swap column names with the ones from comparison df and append it to it
            df_to_add_trimmed = pd.DataFrame(df_to_add.values, columns=comparison_dataframe.columns)
            comparison_dataframe = pd.concat([comparison_dataframe, df_to_add_trimmed], ignore_index=True)
            continue

        # if there are possible european counterparts go through them, get applicable values out and prompt with those
        for fitting_pesticide in bridge_table[chi_pesticide]:
            match_df = eu_df[eu_df["eu_pesticide"]==fitting_pesticide]
            # only add if the eu_pesticide dataframe actually still has the pesticide 
            # -> is lost if its not yet applicable, as we only query for applicable values as of right now
            if not match_df.empty:
                eu_pest_df_list.append(match_df)

        for eu_pest_df in eu_pest_df_list:
            eu_pesticide = eu_pest_df["eu_pesticide"].iloc[0]
            # build prompt
            chi_data_csv_string = chi_pest_df[["food", "mrl"]].to_csv(index=False)
            eu_data_csv_string = eu_pest_df[["food", "mrl"]].to_csv(index=False)
            prompt = compare_all_values_prompt.format(
                chinese=chi_data_csv_string,
                european=eu_data_csv_string
            )
            # ask prompt
            completion = openai_client.chat.completions.create(
                model=settings.kipitz_model,
                messages=[{"role": settings.kipitz_role, "content": prompt}],   
            )
            # get answer and put it into dataframe
            answer = completion.choices[0].message.content
            try:
                ## answer cleaning
                clean_answer = answer.strip()
                # ensure the answer starts with '[['
                flat_start = re.sub(r'\s+', '', clean_answer[:10])
                if not flat_start.startswith("[["):
                    clean_answer = "[[" + clean_answer.lstrip("[").lstrip()
                # ensure the answer ends with ']]' or '],]'
                open_count = clean_answer.count('[')
                close_count = clean_answer.count(']')
                if close_count < open_count:
                    clean_answer += (']' * (open_count - close_count))
                # insert missing commas between sublists if needed
                if re.search(r"\]\s*\[", clean_answer):
                    clean_answer = re.sub(r"\]\s*\[", "], [", clean_answer)

                answer = clean_answer

                data_list = ast.literal_eval(answer)
                # normalize to a list of lists 
                if isinstance(data_list, list):
                    if all(isinstance(item, list) for item in data_list):
                        # already a list of lists
                        normalized_data_list = data_list
                    else:
                        normalized_data_list = [data_list]
                for sublist in normalized_data_list:
                    ## combine answer from LLM with the other infos to create a full row in the comparison DataFrame + sublist + -1 as temp mrl value
                    row = [chi_pesticide, eu_pesticide] + sublist + [-1]
                    comparison_dataframe.loc[len(comparison_dataframe)] = row
            except (ValueError, SyntaxError) as e:
                logging.warning(f"Error type: {type(e).__name__}, Message: {e}")
                logging.warning(f"Not fully correctly formatted output by LLM. Check prompt, value has been lost! This was the LLMs answer: {completion.choices[0].message.content}\nand this the cleaned answer: {answer}")
                pass

    ## set valid maximum residue limit values
    # column names as variables for easier access 
    chi, eu, valid = 'chi_mrl', 'eu_mrl', 'valid_mrl'
    # replace -2 with "/"
    comparison_dataframe[chi] = comparison_dataframe[chi].replace(-2, "/")
    # convert MRL columns to numeric for comparison
    comparison_dataframe[chi] = pd.to_numeric(comparison_dataframe[chi], errors='coerce')
    comparison_dataframe[eu] = pd.to_numeric(comparison_dataframe[eu], errors='coerce')
    # check scenarios of which columns have a value and determine valid_mrl accordingly
    # both missing -> "/"
    both_na = comparison_dataframe[chi].isna() & comparison_dataframe[eu].isna()
    comparison_dataframe.loc[both_na, valid] = np.nan
    # only eu present -> use EU value
    only_eu = comparison_dataframe[chi].isna() & comparison_dataframe[eu].notna()
    comparison_dataframe.loc[only_eu, valid] = comparison_dataframe.loc[only_eu, eu]
    # only chi present and there is a fitting european pesticide -> default 0.1 and note
    only_chi = comparison_dataframe[chi].notna() & comparison_dataframe[eu].isna() & (comparison_dataframe['eu_pesticide'].astype(str) != "/")
    comparison_dataframe.loc[only_chi, valid] = 0.01
    comparison_dataframe.loc[only_chi, 'note'] = "Defaults to 0.01, no value in EU. Check again."
    # both present -> take min
    both_present = comparison_dataframe[chi].notna() & comparison_dataframe[eu].notna()
    comparison_dataframe.loc[both_present, valid] = np.minimum(
        comparison_dataframe.loc[both_present, chi],
        comparison_dataframe.loc[both_present, eu]
    )

    # replace NaNs with "/" again for better visual understanding (NaN may not be clear for non-programmers)
    comparison_dataframe[chi] = comparison_dataframe[chi].astype(str).replace("nan", "/")
    comparison_dataframe[eu] = comparison_dataframe[eu].astype(str).replace("nan", "/")
    comparison_dataframe[valid] = comparison_dataframe[valid].astype(str).replace("nan", "/")

    # add . at the end of notes if they aren't there by default
    comparison_dataframe['note'] = comparison_dataframe['note'].apply(
        lambda x: x if pd.isna(x) or str(x).strip().endswith('.') else str(x).strip() + '.'
    )
    
    return comparison_dataframe
        