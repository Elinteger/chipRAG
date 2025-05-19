"""
This module provides a single function which prompts an LLM with a users prompt and the
context/information gathered during querying the database.
"""
import ast
import openai
import os
import pandas as pd 
import yaml
from dotenv import load_dotenv


def extract_relevant_values(
    user_prompt: str,
    prompt_context: list[str]     
) -> str:
#TODO: add description, returns a pd.DataFrame in the end, str for now!    

    #TODO: add errorhandling for faulty inputs

    ## setup 
    load_dotenv()
    KIPITZ_API_TOKEN = os.getenv("KIPITZ_API_TOKEN")
    openai_client = openai.OpenAI(
***REMOVED***
        api_key=KIPITZ_API_TOKEN
    )

    with open("config/prompt.yaml", "r", encoding="utf-8") as f:
        prompts = yaml.safe_load(f)
    base_value_extraction_prompt = prompts["value_extraction_prompt"]

    extracted_data = []
    ## extract pesticides and values out of context
    for context in prompt_context:
        pesticide = context[0]
        text = context[1]
        prompt = base_value_extraction_prompt.format(
            prompt=user_prompt,
            pesticide=pesticide,
            text=text
            )
        
        completion = openai_client.chat.completions.create(
        model="casperhansen/llama-3.3-70b-instruct-awq",
        messages=[{"role": "user", "content": prompt}],   
        )

        answer = completion.choices[0].message.content
        data_list = ast.literal_eval(answer)
        data_list = [[pesticide] + sublist for sublist in data_list]
        extracted_data += data_list

    # and list into dataframe
    # return extracted_data
    final_df = pd.DataFrame(extracted_data, columns=['pesiticide', 'food', 'mrl'])

    return final_df
