from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..db import crud
from .rag import retrieve_top_doctors, retrieve_resources
from ..core import utils
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import json
import asyncio
from concurrent.futures import TimeoutError

from langchain_groq import ChatGroq

load_dotenv()

router = APIRouter()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    user_message = request.message.strip()
    if not user_message:
        return {"response": "Please provide a valid message.", "doctors": [], "resources": []}

    print(f"\n{'='*60}")
    print(f"🔍 Processing query: {user_message}")
    print(f"{'='*60}")

    try:
        # 1️⃣ Retrieve doctors (with timeout protection)
        print("🔎 Searching for doctors...")
        try:
            doctors = retrieve_top_doctors(user_message, db, top_k=5)
            print(f"✅ Found {len(doctors)} doctors")
        except Exception as e:
            print(f"❌ Doctor retrieval error: {e}")
            doctors = []

        doctors_meta, doctors_for_frontend = [], []
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

        # 2️⃣ Retrieve resources (with timeout protection)
        print("📚 Searching for resources...")
        try:
            resources = retrieve_resources(user_message, top_k=5)
            print(f"✅ Found {len(resources)} resources")
        except Exception as e:
            print(f"❌ Resource retrieval error: {e}")
            resources = []

        resources_for_frontend = []
        if resources:
            for r in resources:
                resources_for_frontend.append({
                    "title": r.get("title"),
                    "url": r.get("url"),
                    "id": r.get("id")
                })

        # 3️⃣ Check doctor intent
        query_lower = user_message.lower()
        is_doctor_search = any(word in query_lower for word in [
            'doctor', 'physician', 'specialist', 'cardiologist', 'gynae',
            'dermatologist', 'neurologist', 'find', 'need', 'looking for',
            'heart', 'skin', 'bone', 'eye', 'brain', 'child', 'women', 'cardio',
            'ortho', 'pediatric', 'ent', 'surgeon', 'dentist', 'psychiatrist',
            'urologist', 'oncologist', 'radiologist', 'anesthesiologist', 'autism'
        ]) or len(doctors) > 0

        # 4️⃣ Groq API with timeout protection
        groq_response = None
        if GROQ_API_KEY and GROQ_API_KEY.strip():
            print("🤖 Calling Groq API...")
            try:
                llm = ChatGroq(
                    groq_api_key=GROQ_API_KEY,
                    model="llama-3.1-8b-instant",
                    temperature=0.4,
                    max_tokens=250,
                    timeout=10  # ✅ 10 second timeout for Groq
                )

                # Build prompt based on context
                if (is_doctor_search and doctors_meta) and resources_for_frontend:
                    prompt = f"""
                    User Query: {user_message}

                    I found {len(doctors_meta)} healthcare providers and {len(resources_for_frontend)} helpful articles/resources.  
                    Write a natural, friendly response that:
                    - Acknowledges the query
                    - Mentions both doctors and resources
                    - Encourages the user to review the cards
                    - Do not list details (frontend will show them)
                    """
                elif is_doctor_search and doctors_meta:
                    prompt = f"""
                    User Query: {user_message}

                    I found {len(doctors_meta)} healthcare providers. Please provide a warm, concise response that:
                    1. Acknowledges the request
                    2. Mentions the number/type of doctors
                    3. Encourages checking their profiles
                    4. Avoids listing details
                    """
                elif resources_for_frontend:
                    prompt = f"""
                    User Query: {user_message}

                    I found {len(resources_for_frontend)} helpful articles/resources.  
                    Write a supportive, conversational response that:
                    - Acknowledges their query
                    - Mentions that I found useful resources
                    - Encourages them to review the cards
                    - Avoids listing titles
                    """
                else:
                    prompt = utils.build_prompt(user_message, doctors_meta)

                # ✅ Call Groq with error handling
                response = llm.invoke([
                    {
                        "role": "system",
                        "content": "You are Med-Bot, a caring medical AI assistant. "
                                   "Keep responses natural, supportive, and expressive. "
                                   "If doctors/resources are found, mention counts but never details."
                    },
                    {"role": "user", "content": prompt}
                ])
                groq_response = response.content.strip()
                print(f"✅ Groq response received: {groq_response[:100]}...")

            except TimeoutError:
                print("⏱️ Groq API timeout - using fallback")
                groq_response = None
            except Exception as groq_error:
                print(f"❌ Groq API error: {groq_error}")
                groq_response = None
        else:
            print("⚠️ No Groq API key found")

        # 5️⃣ Final response (Groq or fallback)
        if groq_response:
            answer = groq_response
        else:
            print("📝 Using template response")
            answer = generate_template_response(
                user_message, doctors_meta, resources_for_frontend, is_doctor_search
            )

        # 6️⃣ Build payload
        response_payload = {
            "response": answer,
            "doctors": doctors_for_frontend if (is_doctor_search and doctors_for_frontend) else [],
            "resources": resources_for_frontend
        }

        print(f"\n✅ Response ready:")
        print(f"   - Text: {answer[:100]}...")
        print(f"   - Doctors: {len(doctors_for_frontend)}")
        print(f"   - Resources: {len(resources_for_frontend)}")
        print(f"{'='*60}\n")

        return response_payload

    except Exception as e:
        print(f"❌ CRITICAL ERROR in chat endpoint: {e}")
        import traceback
        traceback.print_exc()
        return {
            "response": "I'm experiencing some technical issues. Please try again later.",
            "doctors": [],
            "resources": []
        }


def generate_template_response(query: str, doctors_meta: list, resources_meta: list, is_doctor_search: bool) -> str:
    """Fallback if Groq API fails"""

    # ✅ Both doctors + resources
    if (is_doctor_search and doctors_meta) and resources_meta:
        specialty = doctors_meta[0]['speciality'].lower() if doctors_meta[0].get('speciality') else 'healthcare'
        return (f"I found {len(doctors_meta)} {specialty} specialists and also {len(resources_meta)} helpful resources "
                f"related to your query. Please review the profiles and articles below.")

    # ✅ Doctors only
    if is_doctor_search and doctors_meta:
        specialty = doctors_meta[0]['speciality'].lower() if doctors_meta[0].get('speciality') else 'healthcare'
        if len(doctors_meta) == 1:
            return f"I found 1 {specialty} specialist who may be able to help. Please check their profile below."
        return f"I found {len(doctors_meta)} {specialty} specialists who might match your needs. Explore their profiles below."

    # ✅ Resources only
    if resources_meta:
        if len(resources_meta) == 1:
            return "I came across a helpful article that may answer your question. Check it below."
        return f"I found {len(resources_meta)} useful articles that might help. Please review them below."

    # ✅ None
    return "I couldn't find relevant doctors or resources for that query. Try rephrasing or asking about a specific condition or specialty."