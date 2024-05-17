from pymongo import MongoClient
from transformers import pipeline
from sentence_transformers import SentenceTransformer, util

# Create a text generation pipeline
text_generator = pipeline("text-generation", model="huggyllama/llama-7b")
#text_generator = pipeline("translation", model="google-t5/t5-large")



# Connect to MongoDB
client = MongoClient('localhost', 27017)
db = client['chatbot_database']
conversations = db['conversations']

# Index the data
conversations.create_index("user_message")
conversations.create_index("bot_response")

embedder = SentenceTransformer('paraphrase-distilroberta-base-v1')

def get_most_relevant_conversations(user_query, num_matches=5):
    # Fetch past conversations
    past_interactions = list(conversations.find())
    query_embedding = embedder.encode(user_query, convert_to_tensor=True)
    
    # Store scores of each conversation with respect to the query
    scores = []

    for interaction in past_interactions:
        user_msg = interaction["user_message"]
        user_msg_embedding = embedder.encode(user_msg, convert_to_tensor=True)
        score = util.pytorch_cos_sim(query_embedding, user_msg_embedding)
        scores.append((score, interaction))

    # Sort interactions based on scores
    sorted_interactions = sorted(scores, key=lambda x: x[0], reverse=True)

    # Return top N relevant interactions
    relevant_conversations = [interaction[1] for interaction in sorted_interactions[:num_matches]]
    return relevant_conversations

def generate_response(prompt):
    # Fetch most relevant past conversations based on the current prompt
    relevant_conversations = get_most_relevant_conversations(prompt)
    past_conversation = ""
    for interaction in relevant_conversations:
        past_conversation += f'You: {interaction["user_message"]}\n'
        past_conversation += f'Bot: {interaction["bot_response"]}\n'
    
    # Generate a response based on the prompt using the text generation pipeline
    generated_response = text_generator(past_conversation + "You: " + prompt, max_length=100, temperature=0.7, num_return_sequences=1)
    print(generated_response)

    # Extract and return the generated text
    decoded_output = generated_response[0]['translation_text'].split("\n")[-1].split(": ")[-1]
    return decoded_output

def main():
    print("Bot: Hello! I'm your chatbot. Type 'exit', 'quit', or 'bye' to end the conversation.")
    
    while True:
        user_message = input("You: ")
        if user_message.lower() in ['exit', 'quit', 'bye']:
            print("Bot: Goodbye!")
            break

        bot_response = generate_response(user_message)
        print(f"Bot: {bot_response}")

        # Store the conversation in MongoDB
        conversation = {
            "user_message": user_message,
            "bot_response": bot_response
        }
        conversations.insert_one(conversation)

if __name__ == "__main__":
    main()
