from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..db import crud
from .rag import retrieve_top_doctors
from ..core import utils
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import json

from langchain_groq import ChatGroq  # ✅ use Groq instead of OpenAI

load_dotenv()

router = APIRouter()

# Load Groq API key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    user_message = request.message.strip()
    if not user_message:
        return {"response": "Please provide a valid message.", "doctors": []}

    try:
        # 1️⃣ Retrieve top doctors via pipeline (with fallback to keyword search)
        doctors = retrieve_top_doctors(user_message, db)
        print(f"Found {len(doctors)} doctors for query: {user_message}")

        # 2️⃣ Convert doctor objects to structured data
        doctors_meta = []
        doctors_for_frontend = []
        
        if doctors:
            for d in doctors:
                doctors_meta.append({
                    "name": d.name, 
                    "speciality": d.speciality, 
                    "location": d.location,
                    "fee": getattr(d, 'fee', 'Contact for fee'),
                    "keywords": getattr(d, 'keywords', '')
                })
                
                doctors_for_frontend.append({
                    "name": d.name,
                    "speciality": d.speciality,
                    "location": d.location,
                    "fee": getattr(d, 'fee', 'Contact for fee')
                })

        # 3️⃣ Determine if this is a doctor search query
        query_lower = user_message.lower()
        is_doctor_search = any(word in query_lower for word in [
            'doctor', 'physician', 'specialist', 'cardiologist', 'gynae', 
            'dermatologist', 'neurologist', 'find', 'need', 'looking for',
            'heart', 'skin', 'bone', 'eye', 'brain', 'child', 'women', 'cardio',
            'ortho', 'pediatric', 'ent', 'surgeon', 'dentist', 'psychiatrist',
            'urologist', 'oncologist', 'radiologist', 'anesthesiologist'
        ]) or len(doctors) > 0  # ✅ If we found doctors, it's likely a doctor search

        # 4️⃣ Try Groq API, fallback to template response if it fails
        groq_response = None
        try:
            if GROQ_API_KEY and GROQ_API_KEY.strip():
                llm = ChatGroq(
                    groq_api_key=GROQ_API_KEY,
                    model="llama-3.1-8b-instant",
                    temperature=0.3,
                    max_tokens=200
                )

                # ✅ Updated prompt for better responses
                if is_doctor_search and doctors_meta:
                    prompt = f"""
                    User Query: {user_message}
                    
                    I found {len(doctors_meta)} healthcare providers. Please provide a brief, friendly response that:
                    1. Acknowledges the user's request
                    2. Mentions the number and type of doctors found
                    3. Keeps it short since doctor cards will be displayed separately
                    4. Does NOT list individual doctor names or details
                    
                    Example: "I've found {len(doctors_meta)} cardiologists in your area. Please review their profiles below and contact them directly for appointments."
                    """
                else:
                    prompt = utils.build_prompt(user_message, doctors_meta)

                response = llm.invoke([
                    {
                        "role": "system", 
                        "content": "You are Med-Bot, a friendly AI medical assistant. When doctors are found, keep responses brief since doctor cards will be displayed. Never list individual doctor details - just mention the count and specialty."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ])
                groq_response = response.content.strip()
                
        except Exception as groq_error:
            print(f"Groq API error: {groq_error}")
            groq_response = None

        # 5️⃣ Generate response - use Groq if available, otherwise template
        if groq_response:
            answer = groq_response
        else:
            answer = generate_template_response(user_message, doctors_meta, is_doctor_search)

        # 6️⃣ Return response with doctors array for frontend
        # ✅ Always return doctors if they were found and it's a doctor search
        response_payload = {
            "response": answer,
            "doctors": doctors_for_frontend if (is_doctor_search and doctors_for_frontend) else []
        }

        # ✅ Log full JSON in console
        print("📝 Response JSON:", json.dumps(response_payload, indent=2))
        
        return response_payload

    except Exception as e:
        print(f"General error in chat endpoint: {e}")
        
        # Emergency fallback
        try:
            from .rag import keyword_search_doctors
            fallback_doctors = keyword_search_doctors(user_message, db, 3)
            
            if fallback_doctors:
                fallback_doctors_frontend = [
                    {
                        "name": doc.name,
                        "speciality": doc.speciality,
                        "location": doc.location,
                        "fee": getattr(doc, 'fee', 'Contact for fee')
                    }
                    for doc in fallback_doctors
                ]
                
                answer = "I found some healthcare providers that might help. Please contact them directly for appointments."
                return {
                    "response": answer,
                    "doctors": fallback_doctors_frontend
                }
            else:
                return {
                    "response": "I'm experiencing technical difficulties. Please try again later or contact your healthcare provider directly for urgent medical concerns.",
                    "doctors": []
                }
        except:
            return {
                "response": "I'm experiencing technical difficulties. Please try again later or contact your healthcare provider directly for urgent medical concerns.",
                "doctors": []
            }


def generate_template_response(query: str, doctors_meta: list, is_doctor_search: bool) -> str:
    """Generate a template response when Groq API is not available"""
    
    if is_doctor_search and doctors_meta:
        specialty = doctors_meta[0]['speciality'].lower()
        location_hint = ""
        
        # Extract location from query if mentioned
        for word in ['rawalpindi', 'islamabad', 'karachi', 'lahore', 'peshawar', 'quetta']:
            if word in query.lower():
                location_hint = f" in {word.title()}"
                break
        
        if len(doctors_meta) == 1:
            response = f"I've found 1 {specialty} specialist{location_hint} for you. Please review their profile below and contact them directly for an appointment."
        else:
            response = f"I've found {len(doctors_meta)} {specialty} specialists{location_hint} for you. Please review their profiles below and contact them directly for appointments."
            
    elif is_doctor_search and not doctors_meta:
        response = f"I couldn't find specific doctors for '{query}' in our database. Here are some suggestions:\n\n"
        response += "• Try searching with more general terms (e.g., 'cardiologist' instead of 'heart specialist')\n"
        response += "• Check nearby cities or areas\n"
        response += "• Contact local hospitals for referrals\n"
        response += "• For urgent medical needs, visit the nearest emergency room"
        
    else:
        response = "I'm here to help you find healthcare providers and answer general health questions. "
        if doctors_meta:
            response += f"Based on your query, you might want to consult with a {doctors_meta[0]['speciality']} specialist. "
        response += "For specific medical advice, please consult with a qualified healthcare professional."
    
    return response