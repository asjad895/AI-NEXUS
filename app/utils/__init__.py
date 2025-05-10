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
    # If we already have a valid structure with lead_data populated, return as is
    if response_dict.get('lead_data') is not None:
        return response_dict
        
    # Check if there's a JSON block in the response
    response_text = response_dict.get('response', '')
    json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
    
    if not json_match:
        # Try to find any JSON-like structure without code blocks
        json_match = re.search(r'({[\s\S]*"response"[\s\S]*"lead_data"[\s\S]*"cited_chunks"[\s\S]*})', response_text)
    
    if json_match:
        try:
            # Try to parse the JSON from inside the response
            inner_json = json_match.group(1)
            corrected_data = json.loads(inner_json)
            
            # Extract the clean response text (everything before the JSON block)
            clean_response = response_text.split('```json')[0].strip()
            
            # If clean_response is empty, use the response from the extracted JSON
            if not clean_response and 'response' in corrected_data:
                clean_response = corrected_data['response']
                
            # Create the corrected response dictionary
            return {
                'response': clean_response,
                'lead_data': corrected_data.get('lead_data', {}),
                'cited_chunks': corrected_data.get('cited_chunks', [])
            }
        except json.JSONDecodeError:
            # If we can't parse the JSON, return the original with empty lead_data
            return {
                'response': response_text.split('```')[0].strip(),  # Just take text before any code block
                'lead_data': {},
                'cited_chunks': response_dict.get('cited_chunks', [])
            }
    
    # If no JSON found in response, return original with empty lead_data
    return {
        'response': response_text,
        'lead_data': {},
        'cited_chunks': response_dict.get('cited_chunks', [])
    }