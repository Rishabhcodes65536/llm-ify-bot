from pymongo import MongoClient
from transformers import pipeline
from transformers import AutoTokenizer, AutoModelForCausalLM
from sentence_transformers import SentenceTransformer, util
from auto_gptq import AutoGPTQForCausalLM, BaseQuantizeConfig


# text_generator = pipeline("text-generation", model="lmsys/vicuna-7b-v1.5")
# text_generator = pipeline("text-generation", model="huggyllama/llama-7b")


# Connect to MongoDB
client = MongoClient('localhost', 27017)
db = client['chatbot_database']
conversations = db['conversations']

# Index the data
conversations.create_index("user_message")
conversations.create_index("bot_response")

# Initialize the transformer model
model_name_or_path = "lmsys/vicuna-7b-v1.5"
model_basename = "lmsys/vicuna-7b-v1.5"

tokenizer = AutoTokenizer.from_pretrained(model_name_or_path, use_fast=True)

model = AutoGPTQForCausalLM.from_quantized(
    model_name_or_path,
    model_basename=model_basename,
    use_safetensors=True,
    trust_remote_code=True,
    device_map='auto',
    use_triton=False,
    quantize_config=None
)

model.seqlen = 512

# Initialize the sentence transformer model for embeddings
embedder = SentenceTransformer('paraphrase-distilroberta-base-v1')

def get_most_relevant_conversations(user_query, num_matches=5):
    # Create an embedding for the user query
    query_embedding = embedder.encode(user_query, convert_to_tensor=True)
    
    # Fetch past conversations
    past_interactions = list(conversations.find())
    
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
    
    full_prompt = past_conversation + "You: " + prompt
    inputs = tokenizer.encode(full_prompt, return_tensors="pt", truncation=True, max_length=model.seqlen)
    outputs = model.generate(inputs, max_length=100, num_return_sequences=1, temperature=0.7)
    decoded_output = tokenizer.decode(outputs[0], skip_special_tokens=True).split("\n")[-1].split(": ")[-1]
    return decoded_output

def main():
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
