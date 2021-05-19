#!/usr/bin/env python3
import io
import re
import zipfile
from pathlib import Path
from typing import List, Optional
import sys
import csv

import requests
import typer

def sanitize_text(text: str, lowercase: bool = False) -> str:
    """Cleans text by removing whitespace, newlines and tabs and (optionally) lowercasing."""
    sanitized_text = " ".join(text.strip().split())
    sanitized_text = sanitized_text.lower() if lowercase else sanitized_text
    return sanitized_text

WIKITEXT_103_URL = "https://s3.amazonaws.com/research.metamind.io/wikitext/wikitext-103-raw-v1.zip"

# Emoji's used in typer.secho calls
# See: https://github.com/carpedm20/emoji/blob/master/emoji/unicode_codes.py"
SAVING = "\U0001F4BE"
DOWNLOAD = "\U00002B07"


def _write_output_to_disk(text: List[str], output_filepath: Path) -> None:
    """Writes a list of documents, `text`, to the file `output_filepath`, one document per line."""
    # Create the directory path if it doesn't exist
    output_filepath = Path(output_filepath)
    output_filepath.parents[0].mkdir(parents=True, exist_ok=True)

    with open(output_filepath, "w", encoding='UTF-8') as f:
        # TODO (John): In the future, it might make sense to both batch and shard:
        # 1) Batch, meaning write batches of documents to a file as opposed to 1 at a time
        # 2) Shard, meaning break a file up into shard_size // len(text) files, and return a
        #    directory instead. Loading a dataset like this is supported in AllenNLP (see:
        #    https://docs.allennlp.org/master/api/data/dataset_readers/sharded_dataset_reader/)
        with typer.progressbar(text, label="Writing to disk") as progress:
            for doc in progress:
                f.write(doc.strip() + "\n")

def main(
    input_filepath: Optional[Path] = 'raw_data/uitspraken_van_2018_tot_2021.csv',
    output_filepath: Optional[Path] = 'path/to/output/rechtspraak/train.txt',
    segment_sentences: bool = False,
    lowercase: bool = False,
    min_length: Optional[int] = None,
    max_instances: Optional[int] = None,
    pretrained_model_name_or_path: Optional[str] = None,
) -> None:
    """Downloads and lightly preprocesses WikiText-103. If `min_length is not None`, only documents
    with at least this many tokens are retained. If `pretrained_model_name_or_path` is not None, the
    tokenizer will be loaded as `AutoTokenizer.from_pretrained(pretrained_model_name_or_path)`
    using the HuggingFace Transformers library. Otherwise `str.split()` is used. This argument has
    no effect if `min-length is None`. If `segment_sentences` is provided, individual sentences
    will be returned instead of documents. You must have the `"en_core_web_sm"` spacy model
    installed to segment sentences.
    """
    # Setup the pre-trained tokenizer, if specified
    if min_length is not None:
        if pretrained_model_name_or_path is not None:
            # Import transformers here to prevent ImportError errors if the
            # user doesn't want to use it.
            from transformers import AutoTokenizer

            tokenizer = AutoTokenizer.from_pretrained(pretrained_model_name_or_path).tokenize
        else:
            tokenizer = lambda x: x.split()  # noqa
    else:
        tokenizer = None

    # Setup spacy lang object if we are segmenting sentences
    if segment_sentences:
        import spacy

        nlp = spacy.load("en_core_web_sm", disable=["ner"])


    # python scripts/preprocess_generaltext.py --output_filepath=path/to/output/rechtspraak/train.txt \
    # --input_filepath=raw_data/uitspraken_van_2018_tot_2021.csv --min-length 2048

    # Read data
    csv.field_size_limit(sys.maxsize)
    preprocessed_documents: List[str] = []
    with open(input_filepath, encoding='latin-1') as csv_file:

        csv_reader = csv.reader(csv_file, delimiter=',')

        line_count = 0
        for row in csv_reader:
            if row == 0:
                print('headers: {}'.format(row))

            else:
                document = row[1] # for each row, select document

                document = sanitize_text(document, lowercase=lowercase)
                if not document:
                    continue

                # Retain documents if the length of their shortest document is
                # equal to or greater than the minimum specified length
                if tokenizer is not None:
                    num_tokens = len(tokenizer(document))
                    if min_length and num_tokens < min_length:
                        continue

                if max_instances and len(preprocessed_documents) >= max_instances:
                    break

                preprocessed_documents.append(document)


    _write_output_to_disk(preprocessed_documents, output_filepath)

if __name__ == "__main__":
    typer.run(main)
