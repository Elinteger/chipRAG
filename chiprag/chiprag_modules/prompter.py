"""
This module provides a single function which prompts an LLM with a users prompt and the
context/information gathered during querying the database.
"""
import ast
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
