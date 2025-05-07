from typing import List, Dict, Union, Any, Optional,AsyncGenerator
from CustomException import handle_exception
import parameters
import asyncio
import re
import json
from openai import AsyncOpenAI
from chonkie import LateChunker
import pandas as pd
from docling.document_converter import DocumentConverter

# import google.generativeai as genai

# meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo
# "https://api.deepinfra.com/v1/openai"

# genai.configure(api_key=parameters.GEMINI_KEY)


async def process_and_save_chunks(text: str, df_path: str) -> Union[pd.DataFrame,Dict]:

    try:
        chunker = LateChunker(
            embedding_model="all-MiniLM-L6-v2",
            mode="sentence",
            chunk_size=512,
            min_sentences_per_chunk=1,
            min_characters_per_sentence=12,
            delim=['\\n', '##']
        )
        chunks = chunker(text) 
        df = pd.DataFrame({"chunks": chunks})
        df.to_excel(df_path, index=False)

        print(f"DataFrame saved successfully at {df_path}")
        return df

    except Exception as e:
        error = await handle_exception(e)
        return error


async def convert_document_to_markdown(doc_source: str) -> str:
    try:
        doc = DocumentConverter().convert(source=doc_source).document
        markdown_text = doc.export_to_markdown()
        return markdown_text
    except Exception as e:
        error = handle_exception(e)
        return error

async def generative_prompt(all_chunks : List[str],system :str) -> str:
    if not isinstance(all_chunks,list):
        raise ValueError("all_chunks must be a string")

    if len(all_chunks)>0:
        knowledge_source = ''
        for i,doc in enumerate(all_chunks):
            knowledge_source += f"content_{i}: {doc} \n\n"
    else:
        knowledge_source = "NO DATA"

    system_prompt = system.format(knowledge_source = knowledge_source)
    return system_prompt


