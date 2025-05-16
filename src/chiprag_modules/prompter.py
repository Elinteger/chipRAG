"""
This module provides a single function which prompts an LLM with a users prompt and the
context/information gathered during querying the database.
"""
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


    ## extract pesticides and values out of context
    final_df = pd.DataFrame(columns=['pesiticide', 'values'])
    listfornow = []
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

        # #TODO: check if list of values is wanted
        # values = eval(completion.choices[0].message.content)
        # #TODO: add to dataframe
        # final_str += values + "\n"
        listfornow.append(completion.choices[0].message.content)

    return listfornow #FIXME: should be final_df
