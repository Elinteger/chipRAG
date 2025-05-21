import os
import sys
# needed so that python can find our modules
#FIXME: "Use setup.py or pyproject.toml with package_dir={"": "src"}"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))  

import time
from dotenv import load_dotenv
from chiprag_modules import ( 
    load_pesticide_chapters, 
    load_pesticide_names_from_outline, 
    chunk_report_by_sections,
    establish_connection,
    upload_dataframe,
    query_database,
    extract_relevant_values
    )

#FIXME: spalte für dokumentversion in db
#FIXME: tests
def main():
    start_time = time.time()
    print("Hello Chiprag!")
    print("-----------------------")
    # Testing functions
    test_document = "misc/Pestizide_21_EN.pdf"
    start_tables = 31
    end_tables = 460
    start_outline = 4
    end_outline = 19
    outline_pest_number = 4
    user_prompt = "zoxamide" 

    upload = True
    if upload:
        upload_new_document(test_document, start_tables, end_tables, start_outline, end_outline, outline_pest_number)
        print("-----------------------")
    answer = answer_prompt(user_prompt)
    answer.to_csv("pestizid.csv")
    print(answer)
    print(f"Took {divmod(int(time.time() - start_time), 60)[0]:02d}:{divmod(int(time.time() - start_time), 60)[1]:02d} overall")
    return answer

#FIXME: update old values with new ones! -> need new table definition first for that
def upload_new_document(
        test_document, start_tables, end_tables,
        start_outline, end_outline, outline_pest_number
    ):
    print("I upload your stuff the chiprag way!")
    start_time = time.time()
    pdf_str = load_pesticide_chapters(test_document, start_tables, end_tables)
    print(f"1/5 Reading document done! - took {time.time() - start_time}")
    start_time = time.time()
    pdf_pest = load_pesticide_names_from_outline(test_document, start_outline, end_outline, outline_pest_number)
    print(f"2/5 Extracting pesticides from outline done! - took {time.time() - start_time}")
    start_time = time.time()
    pest_df = chunk_report_by_sections(pdf_str, pdf_pest)
    print(f"3/5 Chunking document done! - took {time.time() - start_time}")
    load_dotenv()
    name_postgre = os.getenv("NAME_POSTGRE")
    password_postgre = os.getenv("POSTGRE_PASSWORD_HOME")
    start_time = time.time()
    conn = establish_connection()
    print(f"4/5 Established connection! - took {time.time() - start_time}")
    start_time = time.time()
    upload_dataframe(pest_df, conn, True)
    print(f"5/5 Uploaded Dataframe to PostgreDB! - took {time.time() - start_time}")


def answer_prompt(user_prompt):
    print(f"I'll answer your prompt the chiprag way and return you a csv (soon)!")
    load_dotenv()
    password_postgre = os.getenv("POSTGRE_PASSWORD_HOME")
    start_time = time.time()
    conn = establish_connection()
    print(f"1/3 Established connection! - took {time.time() - start_time}")
    start_time = time.time()
    context_list = query_database(user_prompt, conn, True)
    print(f"2/3 Got context list! - took {time.time() - start_time}")
    start_time = time.time()
    final_dataframe = extract_relevant_values(user_prompt, context_list)
    print(f"3/3 Got the final string! - took {time.time() - start_time}")
    return final_dataframe

if __name__ == "__main__":
    main()
