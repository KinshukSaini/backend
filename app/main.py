import os
from dotenv import load_dotenv
from services.chatbot import Chatbot
from services.retriever import Retriever

def main():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found. Please create a .env file and set your API key.")
        return

    retriever = Retriever()
    chatbot = Chatbot(api_key=api_key, retriever=retriever)
    
    print("Welcome to the Legal Advice Chatbot!")
    
    while True:
        user_input = input("\nPlease enter your legal question (or type 'exit' to quit): ")
        if user_input.lower() == 'exit':
            print("Thank you for using the Legal Advice Chatbot. Goodbye!")
            break
        
        if not user_input.strip():
            continue

        response = chatbot.process_query(user_input)
        print("\nChatbot:", response)

if __name__ == "__main__":
    main()