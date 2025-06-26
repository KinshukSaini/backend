import google.generativeai as genai
from typing import List, Dict, Any, Optional

class Chatbot:
    def __init__(self, api_key: str, retriever):
        self.api_key = api_key
        self.retriever = retriever
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

    def generate_response_with_memory(self, query: str, context: list, conversation_history: List[Dict] = None):
        """Enhanced response with conversation memory"""

        is_first_message = not conversation_history or len(conversation_history) == 0
        
        greeting_keywords = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening', 'how are you']
        is_simple_greeting = any(keyword in query.lower() for keyword in greeting_keywords) and len(query.split()) <= 3
        
        system_prompt = """
        You are Lexley, a helpful, friendly, and knowledgeable legal assistant specializing in UK law.
        
        **IMPORTANT CONVERSATION RULES:**
        - Only greet the user with "Hello!" or similar if this is the very first message of the conversation
        - For continuing conversations, respond naturally without repetitive greetings
        - Build on previous conversation context when relevant
        - Be conversational and helpful
        
        **Conversation Style:**
        - Be warm, approachable, and professional
        - For casual greetings, respond naturally and ask how you can help
        - For legal questions, provide comprehensive, professional answers
        - Remember what was discussed earlier in the conversation
        
        **Legal Expertise:**
        You have access to current UK legislation, government guidance, legal case law, and professional legal practice guidance.
        
        **When responding to legal questions:**
        - Reference previous conversation context when relevant
        - Prioritize recent legislation and official sources
        - Cite specific Acts, sections, or statutory instruments when relevant
        - very important -> ""Always" cite your sources with URLs, if you can't cite a source, give the link to the uk government website where the user can find the information themselves.
        """

        # Build conversation context
        conversation_context = ""
        if conversation_history and len(conversation_history) > 0:
            conversation_context = "\n**Previous conversation:**\n"
            recent_history = conversation_history[-6:] if len(conversation_history) > 6 else conversation_history
            
            for msg in recent_history:
                role = "User" if msg['role'] == 'user' else "ZangerAI"
                conversation_context += f"{role}: {msg['content']}\n"
            conversation_context += "\n"

        if is_simple_greeting:
            if is_first_message:
                simple_prompt = f"""
                {system_prompt}
                
                Current user message: "{query}"
                
                This is the user's first message and it's a greeting. Welcome them warmly to Lexley 
                and ask how you can help with their legal questions today.
                """
            else:
                simple_prompt = f"""
                {system_prompt}
                
                {conversation_context}
                Current user message: "{query}"
                
                This is a casual greeting in an ongoing conversation. Respond naturally and 
                ask what you can help with next, referencing our previous discussion if appropriate.
                """
            return self.call_gemini_api(simple_prompt)


        formatted_context = ""
        if context:
            context_items = []
            for item in context[:5]: 
                if isinstance(item, dict):
                    title = item.get('title', 'Legal Source')
                    snippet = item.get('snippet', '')
                    url = item.get('url', '')
                    site = item.get('site', 'Legal Database')
                    
                    context_items.append(f"[{site}] {title}\n{snippet}\n(Source: {url})")
            
            if context_items:
                formatted_context = f"\n\nAvailable legal context:\n---\n" + "\n\n".join(context_items) + "\n---\n"

        # Build full prompt
        user_prompt = f"""
        {system_prompt}
        
        {conversation_context}
        Current user question: "{query}"
        {formatted_context}
        
        Please provide a comprehensive answer. Build on our previous conversation where relevant. 
        {'Include specific source citations when using the legal context above.' if formatted_context else 'Provide helpful guidance based on your legal knowledge.'}
        """

        return self.call_gemini_api(user_prompt)

    def call_gemini_api(self, prompt: str) -> str:
        """Call Gemini API"""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return "I apologize, but I'm experiencing technical difficulties. Please try again."

    # Keep backward compatibility
    def process_query(self, query: str):
        """Legacy method"""
        context = self.retriever.fetch_context_for_query(query)
        return self.generate_response_with_memory(query, context, [])
    
    def process_query_with_history(self, query: str, conversation_history: List[Dict] = None):
        """Process query with conversation history"""
        context = self.retriever.fetch_context_for_query(query)
        return self.generate_response_with_memory(query, context, conversation_history)
