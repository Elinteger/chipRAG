from chiprag_modules import ( 
    load_pesticide_chapters, 
    load_pesticide_names_from_outline, 
    chunk_report_by_sections,
    embed_text 
    )

#TODO: remove some inputs and swap them with a config (stuff like models and so on)
#TODO: maybe faulty arguments arent an issue? check if check is always needed
#TODO: chiprag_modules isnt known when starting program
#FIXME: Vektorisierung raus? Nochmal tests machen, ob embed ergebnisse gebraucht werden
#       -> wenn nein: aus allen raus!
#TODO: spalte für dokumentversion

def main():
    print("Hello Chiprag!")


def upload_new_document():
    print("I upload your stuff the chiprag way!")


def answer_prompt():
    print("I'll answer your prompt the chiprag way and return you a csv!")


if __name__ == "__main__":
    main()
