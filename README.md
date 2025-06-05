# chipRAG

> **Chi**nese **P**esticide **RAG**

**chipRAG** is an AI-powered tool designed to perform *Retrieval-Augmented Generation (RAG)*-based comparisons between pesticide residue limits defined in Chinese and European regulations. It utilizes English translations of the Chinese food safety standard ([GB Standards](https://www.fao.org/faolex/results/details/en/c/LEX-FAOC215904/), via [USDA translation](https://www.fas.usda.gov/data/china-national-food-safety-standard-maximum-residue-limits-pesticides-foods)) and the [EU DataLake](https://developer.datalake.sante.service.ec.europa.eu/).

Although chipRAG is tailored for this specific use case, it can serve as a blueprint for building RAG systems that extracts context out of structured data (CSV, XLSX, SQL) from unstructured or semi-structured sources (PDFs).

Created during an internship at the *German* [*Bundesamt für Verbraucherschutz und Lebensmittelsicherheit (BVL)*](https://www.bvl.bund.de/DE/Home/home_node.html),the **Federal Office of Consumer Protection and Food Safety**.

---

## Features

- Extract and structure data from English-translated Chinese pesticide regulation PDFs.
- Retrieve up-to-date EU pesticide regulations from the EU DataLake.
- Perform direct comparisons of pesticide limits between China and the EU by pesticide, product, or food category.
- Built with modularity in mind to allow future adaptation and fine-tuning.

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Elinteger/chipRAG.git
cd chipRAG
```

### 2. Install Dependencies

#### Recommended (via `pyproject.toml`)

```bash
pip install .
```

#### Alternative (manual setup)

```bash
pip install -r misc/requirements.txt
```

### 3. Configure Environment

Copy the example .env file from the misc folder to the project root and update it with your configuration:

```bash
cp misc/.env.example .env
```

---

## Database Setup

> chipRAG is built for **PostgreSQL**. Using another database requires significant code changes.

### 1. Create the Database

```sql
CREATE DATABASE pesticide_db;
```

If you use a different name, update the `.env` accordingly.

### 2. Create Required Tables

```sql
-- Chinese residues
CREATE TABLE chinese_pesticide_residues (
    id SERIAL PRIMARY KEY,
    pesticide TEXT UNIQUE NOT NULL,
    text TEXT NOT NULL,
    version TEXT NOT NULL
);

-- European residues
CREATE TABLE european_pesticide_residues (
    id SERIAL PRIMARY KEY,
    pesticide TEXT NOT NULL,
    product TEXT NOT NULL,
    mrl TEXT,
    applicability TEXT,
    application_date TEXT
);
```

If you rename the tables, make sure to update their names accordingly in `config/query.yaml`.

---

## Usage

### Upload Chinese Regulatory Documents

```bash
python chiprag.py doc "path_to_document" "document_version" begin_outline end_outline begin_tables end_tables pesticide_chapter_number
```

#### Arguments

| Argument               | Description                                                                                       |
|------------------------|---------------------------------------------------------------------------------------------------|
| `path_to_document`     | Path to PDF document which is to be scanned in                                                    |
| `document_version`     | Version of the document, following the format: `GB[Year]-[Document Number]`, e.g. "GB2021-001", "GB2021-002", "GB2022-001"          |
| `begin_outline`        | First page where the outline in which pesticides are listed begins                                |
| `end_outline`          | Last page which holds the outline in which the pesticides are listed                              |
| `begin_tables`         | First page which holds information/tables relevant to you                                         |
| `end_tables`           | Last page which holds information/tables relevant to you                                          |
| `pest_chapter_number`  | Chapter number with which pesticide sections begin. For example `4` for `4.15 Zoxamide` or `4.19 Deltamethrin` |

> Page numbers refer to those displayed in the PDF viewer, not the actual file index.

**Example:**

```bash
python chiprag.py doc "misc/Pesticides_21_EN.pdf" "GB2021-001" 4 19 31 460 4
```

Use consistent `document_version` values (e.g. `GB2021-001`, `GB2021-002`) to maintain data integrity when updating.

---

### Update EU Pesticide Database

```bash
python chiprag.py eu
```

> Fetches the latest values from the EU DataLake and updates the local database.

---

### Generate Comparison Report

Ensure you've uploaded the Chinese documents and updated the EU database before use.

```bash
python chiprag.py comp "keyword1" "keyword2" ... --output_path="path/to/output.xlsx"
```

#### Arguments

| Argument         | Description                                                                                            |
|------------------|--------------------------------------------------------------------------------------------------------|
| `keywords`       | Keywords like pesticide/food names to compare                                                        |
| `--output_path`  | Path where the Excel output should be saved to. Defaults to `output.xlsx` in the working directory |

> Keywords must exactly match (case-insensitive) the names in the Chinese document!

**Examples:**

```bash
python chiprag.py comp "Zoxamide" --output_path="zoxamide_comparison.xlsx"
python chiprag.py comp "Olive Oil" "Cheese"
python chiprag.py comp "Cereal"
python chiprag.py comp "Deltamethrin" "Cucumber" "Condiments" --output_path="another_example.xlsx"
```

---

## Troubleshooting

### PostgreSQL Errors

- Confirm the database and tables are created correctly.
- Ensure `.env` values are complete and accurate and `.env` is in the root directory.
- If you changed any names, update `.env` and `query.yaml` accordingly.

### Document Parsing Issues

chipRAG is tailored to specific USDA PDF formats, using the 2021 and 2022 English translations as references. If the document layout changes, you may need to:

- Modify the parsing logic in `loader.py` (see the `TODO:` comments for guidance).
- In particular, adjust the `cropbox` settings to properly exclude unwanted elements such as page numbers, which may have shifted position.

### Fine-Tuning Prompt Behavior

- Most fine-tuning is done by adapting the prompts found in `config/prompts.yaml`.
- Keep in mind that LLMs are inherently probabilistic, so outputs may vary with each run.
- The code expects the LLM to return properly formatted Python lists; if the output is malformed, the program can fail.
- The current prompts achieve a good rate of correctly formatted answers, but any changes should be thoroughly tested to ensure reliability.


---

## Pipeline

A short pipeline breakdown for quick understanding. Functions may call other helper functions internally; this is meant as a top-level representation. 

The format used is: `[module.py]function()` → connecting functions

### Upload documents

`chiprag.py:main()` → `document_uploader.py:upload_document()` → `loader.py:load_pesticide_chapters()` and `loader.py:load_pesticide_names_from_outline()` → `chunker.py:chunk_report_by_sections()` → `chi_postgres_store.py:upload_dataframe()`

### Update EU-database

`chiprag.py:main()` → `eu_data_updater.py:update_eu_data()` → `eu_data_tools.py:eu_fetch_api()` → `eu_postgres_store.py:store_pesticide_data()`

### Create comparison

`chiprag.py:main()` → `comparison_creater.py:create_comparison()` → `comparison_creater.py:_get_chi_values()` → `comparison_creater.py:_get_eu_values()` → `prompter.py:compare_values()` → `comparison_creater.py:_render_to_xlsx()`


---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details. The MIT License permits free use, modification, and distribution of the software.
