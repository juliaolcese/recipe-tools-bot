
from google import genai
import json
import os
from typing import List
from pydantic import BaseModel, Field, ValidationError
from google.genai.types import GenerateContentConfig
import logging

logger = logging.getLogger(__name__) 

API_KEY = os.getenv("GOOGLE_API_KEY")

class Ingredient(BaseModel):    
    name: str = Field(
        description="Ingredient name. E.g., 'sugar', 'flour', 'eggs'."
    )
    quantity: str = Field(
        description="Quantity of the ingredient. E.g., '1', '2', '300'."
    )
    unit: str = Field(
        description="Measurement unit of the ingredient quantity. E.g., 'cups', 'grams', 'tablespoons', 'units'."
    )

class IngredientList(BaseModel):
    items: List[Ingredient]



class GeminiAPI():
    def __init__(self):
        self.client = genai.Client(api_key = API_KEY)
        self.model = 'gemini-2.5-flash'

    def get_ingredients(self, recipe_link: str):
        tools = [
            {"url_context": {}},
            {"google_search": {}}
        ]

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=f"Get the complete list of ingredients from this recipe: {recipe_link}",
                config=GenerateContentConfig(
                    tools=tools,
                    temperature=0,
                ),
            )

            ingredients_text = response.text    

            # It's necessary to make two API calls because using tools doesn't allow response_schema
            # to be application/json directly.
            structured_response = self.client.models.generate_content(
                model=self.model,
                contents=f"Convert this text to JSON using schema IngredientList:\n{ingredients_text}",
                config=GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=IngredientList,
                    temperature=0,
                ),
            )

        except Exception as e:
            logger.error(f"Gemini call failed: {e}", exc_info=True) 
            raise RuntimeError(f"Gemini call failed: {e}") from e 

        try:
            ingredient_list = IngredientList.model_validate_json(structured_response.text)
            ingredients = ingredient_list.items 

        except ValidationError as e:
            logger.error(f"Pydantic validation failed: {e}", exc_info=True)
            raise ValueError(f"Gemini response didn't match schema: {e}") from e

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response: {e}", exc_info=True)
            raise ValueError(f"Response isn't a valid JSON: {structured_response.text[:200]}...") from e

        logger.debug(f"Extracted ingredients: {ingredients}")
        return ingredients    