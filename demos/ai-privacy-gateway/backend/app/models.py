from pydantic import BaseModel


class ProcessRequest(BaseModel):
    prompt: str


class ProcessResponse(BaseModel):
    original_prompt: str
    anonymized_prompt: str
    llm_raw_response: str
    final_deanonymized_response: str
