import json
import re

import ollama
from pydantic import BaseModel
from deepeval.models import DeepEvalBaseLLM
from InstructorEmbedding import INSTRUCTOR


def extract_json_from_response(response_string: str):
    try:
        # Combined regular expression pattern to match JSON blocks
        json_pattern = r'```json\n({.*?})\n```|```\n({.*?})\n```|\n({.*?})\n'
        # Search for the latest JSON block in the response string
        json_match = re.findall(json_pattern, response_string, re.DOTALL)

        if json_match:
            # Get the last match and find the first non-empty group
            latest_json = next(filter(None, json_match[-1]))

            # Remove any trailing commas to make it valid JSON
            latest_json = latest_json.rstrip(",")

            # Parse the JSON string
            latest_json_data = json.loads(latest_json)
            return latest_json_data
        else:
            return {"verdict": "no", "reason": "", "intentions": [], "data": {}}
    except (ValueError, IndexError) as e:
        print(f"Error extracting JSON: {e}")
        return {"verdict": "no", "reason": "", "intentions": [], "data": {}}

class CustomOllamaLLM(DeepEvalBaseLLM):
    def __init__(self, model_name="llama3.1", instructor_model_name: str = "hkunlp/instructor-large"):
        self.model_name = model_name
        self.instructor_model = INSTRUCTOR(instructor_model_name)
        self.client = ollama.Client()

    def load_model(self):
        return self.client

    def generate(self, prompt: str, schema: BaseModel) -> BaseModel:
        # Generate embeddings using Instructor
        task = "Enhance this prompt for an LLM response."
        instruction_text = [task, prompt]
        embedding = self.instructor_model.encode([instruction_text])

        # Use embeddings to enhance the prompt
        embedding_summary = f"The embedding vector has been generated with dimensions {len(embedding[0])}. Use this context to refine your response."

        # Construct the full prompt for Ollama
        schema_description = schema.model_json_schema()
        full_prompt = f"""
                You are an assistant that strictly adheres to the provided JSON schema.

                Schema:
                {schema_description}

                Context:
                {embedding_summary}

                Task:
                {prompt}

                Ensure your response strictly conforms to the JSON schema provided.
                """

        # Query the Ollama model
        client = self.load_model()
        response = client.generate(
            model=self.model_name,
            prompt=full_prompt)

        print(f"Response: {response}]")

        # Generate output
        # response = client.generate(
        #     prompts=[prompt],
        #     stop_sequences=["\n"],  # Define stop tokens for clean outputs
        #     temperature=0.7,
        #     max_tokens=2000,
        #     top_p=0.9,
        #     top_k=40,
        # )

        # Extract the text output from the response
        # generated_text = response.generations[0][0].text
        #
        # print(f"Result: {generated_text}")
        # try:
        #     json_result = extract_json_from_response(generated_text)  # Assuming generated_text is valid JSON
        #
        #     return schema(**json_result)
        # except json.JSONDecodeError as e:
        #     print(f"Error decoding JSON: {e}")
        #     return {"verdict": "no", "reason": "", "intentions": [], "data": {}}
        # except Exception as e:
        #     print(f"Error validating output: {e}")
        #     return {"verdict": "no", "reason": "", "intentions": [], "data": {}}

    async def a_generate(self, prompt: str, schema: BaseModel) -> BaseModel:
        return self.generate(prompt, schema)

    def get_model_name(self):
        return self.model_name

