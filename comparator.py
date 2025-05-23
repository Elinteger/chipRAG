import os
import sys
# needed so that python can find our modules
#FIXME: "Use setup.py or pyproject.toml with package_dir={"": "src"}"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))  

import ast
import chiprag
import openai
import pandas as pd
import yaml
from config.load_config import settings
from eu_data_tools import update_eu_data, query_pesticides_from_eu_api, get_all_pesticide_data_from_eu_api


def main():
    update_eu = False
    upload_document = False
    if update_eu:
        update_eu_data()
    prompt = "zoxamide; 2,4-DB"
    #TODO: not how it'll look in the end, just for testing purposes right now
    # df = chiprag.main(prompt, upload_document)
    # df.to_csv("superguterdf.csv")
    df = pd.read_csv("superguterdf.csv")
    #FIXME: JUST PROTOTYPING, CREATE OWN FUNCTION(S) IF NEEDED

    #extract unique pesticides from chinese result
    prompt_pesticides = df["pesticide"].unique().tolist()
    #extract all unique pesticides from eu db
    eu_pesticides = query_pesticides_from_eu_api()

    #check if pesticide from china is in eu
    openai_client = openai.OpenAI(
        base_url=settings.kipitz_base_url,
        api_key=settings.kipitz_api_token
    )

    with open(settings.prompt_path, "r", encoding="utf-8") as f:
        prompts = yaml.safe_load(f)
    compare_pesticides_prompt = prompts["compare_pesticides_prompt"]
    prompt_pesticides.append("pokemon")  # test so that it wont hallucinate if it cant find anything!
    result_dict = {}

    for propes in prompt_pesticides:
        possible_matches_list = []
        prompt = compare_pesticides_prompt.format(
            chinese_pesticide=propes,
            european_pesticides=eu_pesticides
        )
        completion = openai_client.chat.completions.create(
            model=settings.kipitz_model,
            messages=[{"role": settings.kipitz_role, "content": prompt}],   
        )
        answer = completion.choices[0].message.content
        possible_matches_list += ast.literal_eval(answer)
        result_dict[propes] = possible_matches_list
    
    #get values from eu
    values = get_all_pesticide_data_from_eu_api(result_dict[prompt_pesticides[0]])
    print(values)


    # get chipragdata from prompt X
    # chiprag.main(prompt) X
    # get all distinct pesticides X
    # see (somehow) if pesticide exists in eu data (fetch all pesticides for that, then either fuzzy or LLM) -> dataframe that keeps track of chinese and possible eu X
    # get data for all possible pesticides, ask LLM if there is a value for row from chinese in any of the EU  
    # get everything into one big dataframe -> thats a different "result dataframe"
    # dataframe to excel
    print("done")


if __name__ == "__main__":
    main()
