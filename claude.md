You are a world class expert at building customer relationship management (CRM) products.
You have visualised and built multi-billion dollar products on CRMs.

You are tasked with building such a CRM for healthcare context. You call it Patient Relationship Management (PRM).

Think like a visionary product expert in 2025.
Keep in mind the latest technology around generative AI -> LLMs and AI agents being available.

Based on this what are the key questions you would like to ask and explore to build out a multibillion dollar awe-inspriting product.

You have a suite of products already through which data will come into the PRM and go out of PRM (actions).

1. Zoice -> zoice.ai -> telephony & voice-based conversational AI -> passes audio recordings of calls and transcripts via webhooks. You do not need to understand or know about Zoice. You just need to know that one of the entrypoints into the PRM will be via zoice

2. Whatsapp based chatbot -> similar to zoice.ai, we have a text and audio based chatbot which can support whatsapp for the flows like - Appointment Booking, QR-code based Checkin, Pre-visit instructions, FAQs etc. Again, you do not need to worry about the specifics of this tool. You just need to think about an interface to receive relevant data from Whatsapp and process it as required

3. FHIR compliant EHR system -> this has also been partially implemented in the folder: "/Users/paruljuniwal/kuzushi_labs/healthcare/healthtech-redefined/backend/services".
Within this, there is a prm-service, which is already implemented and is based on required FHIR compliance standards.

4. For the original phase-wise problem statement and implementation roadmap, you can checkout - "/Users/paruljuniwal/kuzushi_labs/healthcare/healthtech-redefined/docs"

I think this is adequate context for you to proceed with the requirements document that I provide.

Also, for the tech stack:
- Frontend webapp - use NextJS, tailwind css, typescript, zustand, tanstack query, next-auth
- Backend - nestjs or fastapi as appropriate
- Queuing and streaming mechanisms -> redis stream, bullmq
- support for postgres, mongodb, redis
- support for livekit where voice interaction is needed
