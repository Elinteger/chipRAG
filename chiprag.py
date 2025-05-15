import os
import sys
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

#TODO: remove some inputs and swap them with a config (stuff like models and so on)
#TODO: maybe faulty arguments arent an issue? check if check is always needed
#TODO: chiprag_modules isnt known when starting program
#FIXME: Vektorisierung raus? Nochmal tests machen, ob embed ergebnisse gebraucht werden
#       -> wenn nein: aus allen raus!
#TODO: spalte für dokumentversion
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
    user_prompt = "Give me all maximum residue values for zoxamide."
    upload_new_document(test_document, start_tables, end_tables, start_outline, end_outline, outline_pest_number)
    print("-----------------------")
    answer = answer_prompt(user_prompt)
    print("-----------------------")
    print(answer)
    print(f"Took {divmod(int(time.time() - start_time), 60)[0]:02d}:{divmod(int(time.time() - start_time), 60)[1]:02d} overall")


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
    print(pest_df)
    print(f"3/5 Chunking document done - took {time.time() - start_time}!")
    load_dotenv()
    password_postgre = os.getenv("POSTGRE_PASSWORD_HOME")

    start_time = time.time()
    conn = establish_connection("pesticide_db", "postgres", password_postgre)
    print(f"4/5 Established connection! - took {time.time() - start_time}")
    start_time = time.time()
    upload_dataframe(pest_df, conn, True)
    print(f"5/5 Uploaded Dataframe to PostgreDB! - took {time.time() - start_time}")


def answer_prompt(user_prompt):
    print(f"I'll answer your prompt the chiprag way and return you a csv (soon)!")
    load_dotenv()
    password_postgre = os.getenv("POSTGRE_PASSWORD_HOME")
    start_time = time.time()
    conn = establish_connection(f"pesticide_db", "postgres", password_postgre)
    print(f"1/3 Established connection! - took {time.time() - start_time}")
    start_time = time.time()
    context_list = query_database(user_prompt, conn, True)
    print(f"2/3 Got context list! - took {time.time() - start_time}")
    start_time = time.time()
    final_str = extract_relevant_values(user_prompt, context_list)
    print(f"3/3 Got the final string! - took {time.time() - start_time}")
    return final_str

if __name__ == "__main__":
    main()
