import ollama
from pydantic import BaseModel
from deepeval.models import DeepEvalBaseLLM
import instructor
from openai import OpenAI

class CustomOllamaLLM(DeepEvalBaseLLM):
    def __init__(self, model_name="llama3.1"):
        self.model_name = model_name
        self.client = ollama.Client()

    def load_model(self):
        return self.client

    def generate(self, prompt: str, schema: BaseModel) -> BaseModel:
        client = instructor.from_openai(
            OpenAI(
                base_url="http://localhost:11434/v1",
                api_key="ollama",  # required, but unused
            ),
            mode=instructor.Mode.JSON
        )

        resp = client.messages.create(
            model=self.model_name,
            response_model=schema,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ]
        )
        print(resp.model_dump_json(indent=2))
        return resp

    async def a_generate(self, prompt: str, schema: BaseModel) -> BaseModel:
        return self.generate(prompt, schema)

    def get_model_name(self):
        return self.model_name

