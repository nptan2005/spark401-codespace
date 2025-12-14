from openai import OpenAI

client = OpenAI(api_key='sk-proj-OiIJPoY1H1znf0sW4c6qT3BlbkFJvhteD0l3Vqnbb6LTSsCM')




# Sử dụng ChatCompletion.create cho OpenAI GPT-3.5 hoặc GPT-4
response = client.chat.completions.create(model="gpt-3.5-turbo",
messages=[
  {"role": "system", "content": "You are a helpful assistant."},
  {"role": "user", "content": "Hello, OpenAI!"}
])

print(response.choices[0].message.content.strip())


