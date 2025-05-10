import json, re
def fix_assistant_response(response_dict):
    """
    Extracts proper JSON structure from response when the assistant incorrectly
    includes JSON inside the response field.
    
    Args:
        response_dict (dict): The original response dictionary from the assistant
        
    Returns:
        dict: A corrected response dictionary with the proper structure
    """
    print(f"response_dict: {response_dict}")
    if response_dict.get('lead_data') is not None:
        return response_dict
        
    response_text = response_dict.get('response', '')
    json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
    
    if not json_match:
        json_match = re.search(r'({[\s\S]*"response"[\s\S]*"lead_data"[\s\S]*"cited_chunks"[\s\S]*})', response_text)
    
    if json_match:
        try:
            inner_json = json_match.group(1)
            print(f"inner_json: {inner_json}")
            corrected_data = json.loads(inner_json)
            clean_response = response_text.split('```json')[0].strip()
            if not clean_response and 'response' in corrected_data:
                clean_response = corrected_data['response']
            return {
                'response': clean_response,
                'lead_data': corrected_data.get('lead_data', {}),
                'cited_chunks': corrected_data.get('cited_chunks', [])
            }
        except json.JSONDecodeError:
            return {
                'response': response_text.split('```')[0].strip(),
                'lead_data': {},
                'cited_chunks': response_dict.get('cited_chunks', [])
            }
    return {
        'response': response_text,
        'lead_data': {},
        'cited_chunks': response_dict.get('cited_chunks', [])
    }