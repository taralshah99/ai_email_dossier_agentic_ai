import re
import json

def parse_crewai_output(output_obj):
    """
    Parse CrewAI output which can be either a CrewOutput object or a string
    """
    # Handle CrewOutput object (newer CrewAI versions)
    if hasattr(output_obj, 'raw'):
        content = output_obj.raw
    elif hasattr(output_obj, 'tasks_output') and output_obj.tasks_output:
        # Get the raw content from the first task output
        first_task = output_obj.tasks_output[0]
        if hasattr(first_task, 'raw'):
            content = first_task.raw
        else:
            content = str(first_task)
    else:
        # Convert to string if it's a CrewOutput object without expected attributes
        content = str(output_obj)
    
    # If content is still not a string, convert it
    if not isinstance(content, str):
        content = str(content)
    
    # Try to parse as JSON string if it looks like JSON
    if content.strip().startswith('{') and content.strip().endswith('}'):
        try:
            json_output = json.loads(content)
            
            # Check for the 'raw' key, which is common for direct agent outputs
            if "raw" in json_output:
                content = json_output["raw"]
            # Check for 'tasks_output' which is a list of task results
            elif "tasks_output" in json_output and isinstance(json_output["tasks_output"], list):
                # Assuming we want the 'raw' content of the first task output if available
                if json_output["tasks_output"] and "raw" in json_output["tasks_output"][0]:
                    content = json_output["tasks_output"][0]["raw"]
                else:
                    content = str(json_output) # Fallback to string representation of the whole JSON
            else:
                content = str(json_output) # Fallback to string representation of the whole JSON
                
        except json.JSONDecodeError:
            # If JSON parsing fails, use the content as is
            pass
    
    # Clean up escaped characters if the content is a string
    if isinstance(content, str):
        content = content.replace("\\n", "\n")
        content = content.replace("\\\"", "\"")
        content = content.replace("\\t", "\t")
        # Handle HTML entities like &#39; for apostrophe
        content = content.replace("&#39;", "'")
        content = content.replace("&amp;", "&")
        content = content.replace("&quot;", "\"")
        content = content.replace("&lt;", "<")
        content = content.replace("&gt;", ">")

    return content