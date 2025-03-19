from openai import OpenAI
import base64
from PIL import Image
import json
import re
import os

def optimize_image(image_path, output_path="optimized_image.webp", max_size=720, quality=95):
    image = Image.open(image_path)
    if max(image.size) > max_size:
        image.thumbnail((max_size, max_size), Image.LANCZOS)
    image.save(output_path, format="JPEG", quality=quality)
    return output_path

def count_errors(response_json):
    errors = {}
    error_count = 0
    
    def traverse(obj, path=""):
        nonlocal error_count
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_path = f"{path}.{key}" if path else key
                if isinstance(value, dict):
                    if "correto" in value and value["correto"] == "não":
                        if not any(
                            isinstance(field_val, str) and field_val.strip().startswith("Não aplicável para")
                            for field_val in value.values()
                        ):
                            errors[new_path] = value
                            error_count += 1
                    traverse(value, new_path)
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        traverse(item, f"{new_path}[{i}]")
    
    traverse(response_json)
    return error_count, errors

def analyze_label(image_path, legislacao, prompt_path='prompt.txt'):
    client = OpenAI()
    optimized_image_path = optimize_image(image_path)
    
    with open(prompt_path, 'r', encoding='utf-8') as file:
        prompt_text = file.read().strip()
    
    with open(optimized_image_path, 'rb') as image_file:
        image_data = base64.b64encode(image_file.read()).decode('utf-8')
    
    messages = [
        {"role": "system", "content": "Você é um assistente especializado em análise de rótulos de produtos alimentícios."},
        {"role": "user", "content": [
            {"type": "text", "text": json.dumps(legislacao, ensure_ascii=False)},
            {"type": "text", "text": prompt_text},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
        ]}
    ]
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=1500,
        temperature=0.3
    )
    
    raw_response = response.choices[0].message.content.strip()

    
    try:
        match = re.search(r'\{.*\}', raw_response, re.DOTALL)
        if match:
            result = json.loads(match.group(0))
            error_count, errors = count_errors(result)
            
            return {
                "total_erros": error_count,
                "detalhes_erros": errors,
                "resultado_completo": result
            }
        else:
            return {"erro": "Nenhum JSON válido encontrado na resposta."}
    except json.JSONDecodeError:
        return {"erro": "Resposta não está em um formato JSON válido."}
    
    finally:
        if os.path.exists(optimized_image_path):
            os.remove(optimized_image_path)
