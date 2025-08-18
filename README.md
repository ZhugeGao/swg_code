# SWG Language Data Processing Pipeline

## 1. Project Overview

This repository contains a suite of Python scripts designed for processing linguistic data for the SWG (Spoken Language in Social Groups) project. The pipeline takes raw annotated speech data (in ELAN `.eaf` or Praat `.TextGrid` formats), processes it through various stages of cleaning, normalization, and feature extraction, and produces structured `.csv` files suitable for statistical analysis.

The primary focus of this pipeline is to handle German linguistic data, with specialized modules for tagging dialectal variation based on a custom lexicon.

## 2. Features

*   **EAF to TextGrid Conversion**: Converts ELAN annotation files (`.eaf`) into Praat TextGrid files (`.TextGrid`).
*   **Multi-level Linguistic Extraction**: Extracts various linguistic units, including:
    *   Words
    *   Clauses (including relative clauses)
    *   Phones
    *   Formants
*   **Lexicon-based Tagging**: Utilizes a custom lexicon to tag words for dialectal variation, standardization, and part-of-speech (POS).
*   **POS Tagging**: Integrates with the Stanford CoreNLP server for part-of-speech tagging.
*   **Data Enrichment**: Merges the extracted linguistic data with social information about the speakers (e.g., age, gender, group).
*   **Configurable Pipeline**: The main processing script is highly configurable, allowing users to enable or disable specific steps and select different data groups and extraction types.

## 3. Project Structure

```
.
├── Aligner_preparation/      # Scripts for preparing data for alignment (not fully explored).
├── SWG_main.py               # The main entry point and control script for the entire pipeline.
├── SWG_utils.py              # A collection of helper functions used across the project.
├── TextGrid_preparation/     # Scripts for converting and manipulating TextGrid files.
│   ├── Eaf2TextGrid.py       # Converts .eaf to .TextGrid.
│   └── ...
├── extracts/                 # Contains the core logic for extracting different linguistic units.
│   ├── words_extract.py
│   ├── clauses_extract.py
│   └── ...
├── add_social_info_to_csv.py # Script to add speaker metadata to the final extracts.
└── ...                       # Other utility and preparation scripts.
```

## 4. Setup and Configuration

### 4.1. Dependencies

This project requires several Python libraries. While a `requirements.txt` file is not provided, you will likely need to install the following:

```bash
pip install pandas openpyxl nltk spacy textgrid ordered-set regex
```

You will also need to download the German language model for spaCy:

```bash
python -m spacy download de_core_news_sm
```

### 4.2. CoreNLP Server

Part-of-speech (POS) tagging is performed using the CoreNLP parser, which requires a running CoreNLP server.

1.  Download and set up the [Stanford CoreNLP server](https://stanfordnlp.github.io/CoreNLP/).
2.  Run the server on `localhost:9002` (as specified in `SWG_main.py`).

### 4.3. Hardcoded Paths

**IMPORTANT**: The scripts contain hardcoded absolute paths that you **must** change to match your local environment. The main variable to change is `working_directory`, found at the top of:

*   `SWG_main.py`
*   `SWG_utils.py`

Update this path to point to the root directory of your project data.

## 5. Usage

The entire pipeline is controlled and executed from `SWG_main.py`.

### 5.1. Configuration

Before running, open `SWG_main.py` and configure the variables at the top of the script:

1.  **`date`**: Set the processing date string.
2.  **`lex_table_name`**: Specify the name of your lexicon file.
3.  **`speaker_groups`**: Choose the speaker groups to process (e.g., `["test"]`, `["panel"]`).
4.  **`extract_types`**: List the types of data you want to extract (e.g., `["words", "phones"]`).
5.  **Boolean Switches**:
    *   `move_downloaded_files`: Set to `True` to organize raw data from a downloads folder.
    *   `fix_lex`: Set to `True` to process and update the lexicon.
    *   `Elan_to_TextGrid`: Set to `True` to convert `.eaf` files.
    *   `run_extract`: Set to `True` to run the main data extraction process.

### 5.2. Running the Pipeline

Once configured, run the main script from your terminal:

```bash
python SWG_main.py
```

The script will execute the selected steps and generate output files in the corresponding `extracts/` subdirectories within your speaker group folders.

## 6. Input Data

The pipeline expects a specific directory structure and file formats:

*   **TextGrid Files**: `.TextGrid` files containing an annotation tier named `SWG`. These should be organized into folders by speaker group (e.g., `panel/TextGrid/1982/`).
*   **Lexicon File**: An `.xlsx` or `.csv` file containing the project's lexicon, with columns for variants, standard forms, POS tags, and custom variation codes (`word_vars`).
*   **Speaker Files**: `.csv` files containing social metadata for the speakers, linked by a transcript ID.

## 7. Output

The final output of the pipeline consists of `.csv` files located in the `extracts/` directory for each speaker group (e.g., `panel/extracts/`). These files contain the extracted linguistic data, enriched with lexicon tags and speaker metadata, ready for analysis.

## 8. Disclaimer

*   This pipeline is highly customized for the specific needs and data structure of the SWG project.
*   The scripts rely on hardcoded paths and are not immediately portable without modification.
*   The code contains several `TODO` comments, indicating areas for future improvement and potential bugs.
