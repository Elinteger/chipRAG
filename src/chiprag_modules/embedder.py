"""
This module provides a single publicly available function that embeds a text into a vector representation for 
future semantic searching. Also has a private helper function to validate user input. 
Vector-dimensionality depends on the model. 
"""
import pandas as pd
from huggingface_hub import model_info
from huggingface_hub.utils import HfHubHTTPError
from transformers import AutoModel


def embed_text(
    df: pd.DataFrame,
    column_name: str = "text",
    hf_embed_model: str = "jinaai/jina-embeddings-v3"
) -> pd.DataFrame:
    pass
    """
    Converts the content of a specified column in a Pandas DataFrame into vector embeddings.

    Args:
        df (pd.DataFrame): The input DataFrame containing the text data to be vectorized.
        column_name (str): The name of the column whose content should be embedded.
        hf_embed_model (str): The model name of a Hugging Face embedding model to use. 
                              Defaults to "jinaai/jina-embeddings-v3".

    Returns:
        pd.DataFrame: The original DataFrame with an additional column named "embedding", 
                      containing the vector representations of the specified column.
    """
    ## faulty argument handling
    __validate_embed_text_inputs(df, column_name, hf_embed_model)

    ## embed text
    #FIXME: use flash_attn and triton to speed up process
    model = AutoModel.from_pretrained(hf_embed_model, trust_remote_code=True)
    embedded_texts = []

    for i, text in enumerate(df[column_name]):
        # embeddings using the default model 'jina_embeddings_v3' have a size of 1024 dimensions
        embedding = model.encode(text, task="text-matching")
        embedded_texts.append(embedding)
        # optional logger for debugging
        #logging.debug("Encoded text {i + 1}/{len(df)")
    df["embedding"] = embedded_texts  

    return df


def __validate_embed_text_inputs(
        df: pd.DataFrame,
        column_name: str,
        hf_embed_model: str
) -> None:
    """
    A private helper function to check if all inputs made to embed_text() are valid.

    Args:
        df (pd.DataFrame): The input DataFrame containing the text data to be vectorized.
        column_name (str): The name of the column whose content should be embedded.
        hf_embed_model (str): The model name of a Hugging Face embedding model to use. 
    """
    # Check that df is a DataFrame
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"'df' must be a pandas DataFrame, got {type(df).__name__}")
    
    # Check that column_name is a string
    if not isinstance(column_name, str):
        raise TypeError(f"'column_name' must be a string, got {type(column_name).__name__}")
    
    # Check that column_name exists in df
    if column_name not in df.columns:
        raise ValueError(f"Column '{column_name}' not found in given DataFrame df. Available columns: {list(df.columns)}")
    
    # check if content in the column is vectorizable (i.e., strings or list of strings)
    if not df[column_name].map(lambda x: isinstance(x, str)).all():
        raise ValueError(f"All entries in column '{column_name}' must be strings for embedding.")

    # Check that the Hugging Face model exists and is accessible
    try:
        info = model_info(hf_embed_model)  # Will raise if model is not found
    except HfHubHTTPError as e:
        raise ValueError(f"Hugging Face model '{hf_embed_model}' not found or inaccessible.") from e
