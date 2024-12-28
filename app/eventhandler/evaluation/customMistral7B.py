import json
import re

from langchain_community.llms.ollama import Ollama
from pydantic import BaseModel
from lmformatenforcer import JsonSchemaParser
from deepeval.models import DeepEvalBaseLLM


def extract_json_from_response(response_string: str):
    try:
        # Regular expression pattern to match JSON objects that start with "intentions" and end with the closing curly brace
        json_pattern = r'```json\n({.*?})\n```'

        # Find all matches of the pattern in the response string
        json_matches = re.findall(json_pattern, response_string, re.DOTALL)

        if json_matches:
            # Return the latest (last) JSON match
            latest_json = json_matches[-1]

            # Parse the latest JSON match
            latest_json_data = json.loads(latest_json)

            return latest_json_data
        else:
            return {"verdict": "no", "reason": "", "data": ""}
    except (ValueError, IndexError) as e:
        print(f"Error extracting JSON: {e}")
        return {"verdict": "no", "reason": "", "data": ""}

class CustomOllamaLLM(DeepEvalBaseLLM):
    def __init__(self, model_name="llama3.1"):
        self.model_name = model_name
        self.client = Ollama(model=model_name)

    def load_model(self):
        return self.client

    def generate(self, prompt: str, schema: BaseModel) -> BaseModel:
        client = self.load_model()

        # Generate output
        response = client.generate(
            prompts=[prompt],
            stop_sequences=["\n"],  # Define stop tokens for clean outputs
            temperature=0.7,
            max_tokens=2000,
            top_p=0.9,
            top_k=40,
        )

        # Extract the text output from the response
        generated_text = response.generations[0][0].text

        print(f"Result: {generated_text}")
        try:
            json_result = extract_json_from_response(generated_text)  # Assuming generated_text is valid JSON

            return schema(**json_result)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return {"verdict": "no", "reason": "", "data": ""}
        except Exception as e:
            print(f"Error validating output: {e}")
            return {"verdict": "no", "reason": "", "data": ""}

    async def a_generate(self, prompt: str, schema: BaseModel) -> BaseModel:
        return self.generate(prompt, schema)

    def get_model_name(self):
        return self.model_name

