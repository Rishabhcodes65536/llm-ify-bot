from flask import Flask, render_template, request, jsonify
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from omegaconf import OmegaConf
import sys

app = Flask(__name__)

# Load GPT-2 model and tokenizer
gpt2_model = AutoModelForCausalLM.from_pretrained("gpt2")
gpt2_tokenizer = AutoTokenizer.from_pretrained("gpt2")

# Load the TTS model
language = 'en'
model_id = 'v3_en'
device = torch.device('cpu')

model, example_text = torch.hub.load(repo_or_dir='snakers4/silero-models',
                                     model='silero_tts',
                                     language=language,
                                     speaker=model_id)
model.to(device)  # Use CPU

@app.route('/')
def index():
    print('This is flushed index html page', flush=True)
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    prompt = data['prompt']
    temperature = float(data['temperature'])  # Convert to float
    max_tokens = int(data['maxTokens'])       # Convert to int
    print('Data from the post request',data,prompt,temperature,max_tokens,flush=True)
    input_ids = gpt2_tokenizer(prompt, return_tensors="pt").input_ids
    gen_tokens = gpt2_model.generate(
        input_ids,
        do_sample=True,
        temperature=temperature,
        max_length=max_tokens,
    )
    gen_text = gpt2_tokenizer.batch_decode(gen_tokens, skip_special_tokens=True)[0]
    
    return jsonify(response=gen_text)

@app.route('/tts', methods=['POST'])
def tts():
    data = request.json
    text = data['text']
    sample_rate = 48000
    speaker = 'en_0'
    put_accent = True
    put_yo = True

    audio = model.apply_tts(text=text,
                            speaker=speaker,
                            sample_rate=sample_rate,
                            put_accent=put_accent,
                            put_yo=put_yo)
    
    audio_data = audio.numpy().tolist()
    return jsonify(audio=audio_data, sample_rate=sample_rate)

if __name__ == '__main__':
    app.run(debug=True)
