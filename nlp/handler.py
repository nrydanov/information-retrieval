from http.server import BaseHTTPRequestHandler

import logging
import json
import torch
import re

from transformers import GPT2TokenizerFast, GPT2LMHeadModel

class RequestHandler(BaseHTTPRequestHandler):
  
  tokenizer = GPT2TokenizerFast.from_pretrained("sberbank-ai/mGPT")
  model = GPT2LMHeadModel.from_pretrained("sberbank-ai/mGPT")
  
  def calculate_weight(self, word, synonym, text):
    inputs = self.tokenizer(
      text, add_special_tokens=False, return_tensors="pt"
    )
    
    with torch.no_grad():
      outputs = self.model(**inputs, labels=inputs["input_ids"])
      base_loss = outputs.loss
    
    inputs = self.tokenizer(
      re.sub(f"${word}* ", synonym, text), add_special_tokens=False, return_tensors="pt"
    )
    
    with torch.no_grad():
      outputs = self.model(**inputs, labels=inputs["input_ids"])
      synonym_loss = outputs.loss
      
    return base_loss - synonym_loss
    
  def do_POST(self):
      logging.info("POST request,\nPath: %s\nHeaders:\n%s\n",
                   str(self.path), str(self.headers))
      length = int(self.headers['content-length'])
      data = self.rfile.read(length).decode('utf-8')
      json_data = json.loads(data)
      self.send_response(200)
      self.send_header('Content-type', 'text/html')
      self.end_headers()
      
      response = []
      
      text = json_data['text']
      for entry in json_data['replacements']:
        word = entry['word']
        synonym = entry['synonym']
        weight = self.calculate_weight(word, synonym, text)
        response.append({"word": word, "synonym": synonym, "weight": weight})
      
      self.wfile.write(json.dumps(response).encode("utf-8"))