import os
from openai import OpenAI


os.environ["OPENAI_API_KEY"] = "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"
client = OpenAI()


def get_embedding(text, model="text-embedding-3-small"):
   text = text.replace("\n", " ")
   return client.embeddings.create(input = [text], model=model).data[0].embedding


print("xd")
text = "Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum."

emb = get_embedding(text)
print(type(emb))
print(len(emb))

# df['ada_embedding'] = df.combined.apply(lambda x: get_embedding(x, model='text-embedding-3-small'))
# df.to_csv('output/embedded_1k_reviews.csv', index=False)
