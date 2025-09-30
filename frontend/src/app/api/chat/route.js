// frontend/src/app/api/chat/route.js
import { NextResponse } from 'next/server';

async function fetchWithTimeout(resource, options = {}, timeout = 90000) { // ✅ Increased to 90s (1.5 minutes)
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);
  
  try {
    const response = await fetch(resource, {
      ...options,
      signal: controller.signal,
    });
    clearTimeout(id);
    return response;
  } catch (error) {
    clearTimeout(id);
    throw error;
  }
}

export async function POST(request) {
  try {
    const { message } = await request.json();

    if (!message || !message.trim()) {
      return NextResponse.json(
        { error: 'Message is required' },
        { status: 400 }
      );
    }

    const backendUrl =
      process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000';

    console.log('🔄 Sending request to backend:', message);

    const response = await fetchWithTimeout(
      `${backendUrl}/api/chat`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: message.trim() }),
      },
      450000 // 45 second timeout
    );

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend error response:', errorText);
      throw new Error(`Backend responded with status: ${response.status}`);
    }

    const data = await response.json();
    console.log('✅ Backend response received:', data);
    return NextResponse.json(data);

  } catch (error) {
    console.error('❌ API Route Error:', error);

    // Better error messages
    if (error.name === 'AbortError') {
      return NextResponse.json(
        {
          response: "The request is taking longer than expected. Your query is being processed. Please try again in a moment.",
          error: 'Request timeout',
        },
        { status: 504 }
      );
    }

    return NextResponse.json(
      {
        response: "I'm currently experiencing technical difficulties. Please try again later.",
        error: error.message,
      },
      { status: 500 }
    );
  }
}