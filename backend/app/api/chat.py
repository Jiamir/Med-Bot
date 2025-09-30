from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..db import crud
from .rag import retrieve_top_therapists, retrieve_resources
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
        return {"response": "Please provide a valid message.", "therapists": [], "resources": []}

    print(f"\n{'='*60}")
    print(f"🔍 Processing query: {user_message}")
    print(f"{'='*60}")

    try:
        # 1️⃣ Retrieve therapists (with timeout protection)
        print("🔎 Searching for therapists...")
        try:
            therapists = retrieve_top_therapists(user_message, db, top_k=5)
            print(f"✅ Found {len(therapists)} therapists")
        except Exception as e:
            print(f"❌ Therapist retrieval error: {e}")
            therapists = []

        therapists_meta, therapists_for_frontend = [], []
        if therapists:
            for t in therapists:
                therapists_meta.append({
    "provider_name": t.provider_name,
    "provider_type": t.provider_type,
    "company_name": t.company_name,
    "address": t.address,
    "city": t.city,
    "state": t.state,
    "email": t.email or "Not provided",
    "keywords": getattr(t, 'keywords', '')
})

                therapists_for_frontend.append({
    "provider_name": t.provider_name,
    "provider_type": t.provider_type,
    "company_name": t.company_name,
    "address": t.address,
    "city": t.city,
    "state": t.state,
    "email": t.email or "Not provided"
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

        # 3️⃣ Check therapist intent
        query_lower = user_message.lower()
        is_therapist_search = any(word in query_lower for word in [
            'therapist', 'counselor', 'psychologist', 'psychiatrist', 'autism', 'speech', 'behavioral', 'child therapy',
            'mental', 'wellness', 'rehabilitation', 'occupational', 'physical', 'find', 'need', 'looking for'
        ]) or len(therapists) > 0

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
                    timeout=10
                )

                if (is_therapist_search and therapists_meta) and resources_for_frontend:
                    prompt = f"""
                    User Query: {user_message}

                    I found {len(therapists_meta)} therapists and {len(resources_for_frontend)} helpful articles/resources.  
                    Write a natural, friendly response that:
                    - Acknowledges the query
                    - Mentions both therapists and resources
                    - Encourages the user to review the cards
                    - Do not list details
                    """
                elif is_therapist_search and therapists_meta:
                    prompt = f"""
                    User Query: {user_message}

                    I found {len(therapists_meta)} therapists. Provide a warm, concise response that:
                    1. Acknowledges the request
                    2. Mentions the number/type of therapists
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
                    prompt = utils.build_prompt(user_message, therapists_meta)

                response = llm.invoke([
                    {
                        "role": "system",
                        "content": "You are Med-Bot, a caring medical AI assistant. "
                                   "Keep responses natural, supportive, and expressive. "
                                   "If therapists/resources are found, mention counts but never details."
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
                user_message, therapists_meta, resources_for_frontend, is_therapist_search
            )

        # 6️⃣ Build payload
        response_payload = {
            "response": answer,
            "therapists": therapists_for_frontend if (is_therapist_search and therapists_for_frontend) else [],
            "resources": resources_for_frontend
        }

        print(f"\n✅ Response ready:")
        print(f"   - Text: {answer[:100]}...")
        print(f"   - Therapists: {len(therapists_for_frontend)}")
        print(f"   - Resources: {len(resources_for_frontend)}")
        print(f"{'='*60}\n")

        return response_payload

    except Exception as e:
        print(f"❌ CRITICAL ERROR in chat endpoint: {e}")
        import traceback
        traceback.print_exc()
        return {
            "response": "I'm experiencing some technical issues. Please try again later.",
            "therapists": [],
            "resources": []
        }


def generate_template_response(query: str, therapists_meta: list, resources_meta: list, is_therapist_search: bool) -> str:
    """Fallback if Groq API fails"""

    if (is_therapist_search and therapists_meta) and resources_meta:
        return (f"I found {len(therapists_meta)} therapists and also {len(resources_meta)} helpful resources "
                f"related to your query. Please review the profiles and articles below.")

    if is_therapist_search and therapists_meta:
        if len(therapists_meta) == 1:
            return f"I found 1 therapist who may be able to help. Please check their profile below."
        return f"I found {len(therapists_meta)} therapists who might match your needs. Explore their profiles below."

    if resources_meta:
        if len(resources_meta) == 1:
            return "I came across a helpful article that may answer your question. Check it below."
        return f"I found {len(resources_meta)} useful articles that might help. Please review them below."

    return "I couldn't find relevant therapists or resources for that query. Try rephrasing or asking about a specific type of therapy or condition."
