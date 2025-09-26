# ----------------------------
# Helper functions for Med-Bot
# ----------------------------

def format_doctor_text(doctor):
    """
    Convert doctor object/metadata into readable text for prompts.
    """
    return f"{doctor.get('name')}, {doctor.get('speciality')}, {doctor.get('location')}"

def build_prompt(user_message, doctors_metadata):
    """
    Construct AI prompt with user query and doctor info.
    Works with Groq (LLM) or any chat model.
    """
    if doctors_metadata:
        doctor_texts = "\n".join([format_doctor_text(d) for d in doctors_metadata])
    else:
        doctor_texts = "No matching doctors found."
    
    return f"""
You are Med-Bot, a friendly and professional AI medical assistant. 
Use the following doctor information to help answer the user's query:

{doctor_texts}

Question: {user_message}

Provide a clear, concise, and helpful response.
"""
