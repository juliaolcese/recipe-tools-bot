import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langchain.tools import tool
from fractions import Fraction
import logging
import unicodedata
from geminiAPI import GeminiAPI, Ingredient, IngredientList

logger = logging.getLogger(__name__) 

from dotenv import load_dotenv
load_dotenv()


# TODO TOOLS:
# Juntar todos los ingredientes repetidos y sumar las cantidades
# Juntar todos los ingredientes de distintas recetas y sumar las cantidades
# Convertir unidades en lista de ingredientes
# Convertir unidades en el texto de la receta
# Pensar cómo hacer si tiene varios componentes

ingredients_llm = GeminiAPI()
@tool
def get_ingredients(url: str) -> IngredientList:
    """Get the list of ingredients from a recipe URL.

    Args:
        url: The URL of the recipe to scrape
    """
    ingredients_list = ingredients_llm.get_ingredients(url)
    if not ingredients_list:
        return IngredientList(items=[])
    return IngredientList(items=ingredients_list)

# @tool
def resize_recipe(ingredients: IngredientList, resize_factor: float) -> IngredientList:
    """Resize the quantities of the ingredients by a given factor.
    Args:
        ingredients: List of ingredients with their quantities
        resize_factor: Factor by which to resize the quantities
    """
    new_ingredients = []
    for ingredient in ingredients.items:
        as_fraction = False
        print(f"Resizing ingredient: {ingredient}")
        new_quantity_str = ingredient.quantity 
        try:
            normalized_quantity = unicodedata.normalize('NFKC', ingredient.quantity)
            if '/' in normalized_quantity or '⁄' in normalized_quantity:
                as_fraction = True
            parts = normalized_quantity.split()
            parts = [part.replace('⁄', '/') for part in parts]
            quantity_num = sum(Fraction(part) for part in parts)
            new_quantity = quantity_num * resize_factor
            if as_fraction:
                new_quantity_str = str(Fraction(new_quantity).limit_denominator())
            else:
                new_quantity_str = str(new_quantity)
        except ValueError:
            logger.warning(f"Unable to convert quantity: '{ingredient.quantity}'")
            new_quantity_str = f"{ingredient.quantity} (x {resize_factor})"

        new_ingredients.append(Ingredient(name=ingredient.name, quantity=new_quantity_str, unit=ingredient.unit))
    
    return IngredientList(items=new_ingredients)

# TODO: Configurar agente para que si devuelve una lista de ingredientes,
# los formatee como una enumeración de ítems
class Agent():
    def __init__(self):
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
        )

        agent = create_agent(
            model = llm,
            tools = [get_ingredients, resize_recipe],
        )

        self.llm = llm
        self.agent = agent

    def invoke(self, prompt: str) -> str:
        response = self.agent.invoke(
            {"messages": [{"role": "user", "content": prompt}]},
        )

        final_message = response['messages'][-1]
        
        content = final_message.content
        
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            return content[0]['text']
        else:
            logger.error(f"Unknown response format: {content}")            
            raise TypeError(f"Unknown response format: {type(content)}")