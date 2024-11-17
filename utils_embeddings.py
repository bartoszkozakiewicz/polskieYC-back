import os
import asyncio
from openai import AsyncOpenAI


class Embedder:
   def __init__(self, model="text-embedding-3-small", max_requests: int =10):
      self.model = model
      self.client = AsyncOpenAI()
      self.max_requests = max_requests

   async def get_embedding_for_batch(self, text_batch: str | list[str]):
      if isinstance(text_batch, str):
         text_batch = [text_batch]

      result =  await self.client.embeddings.create(input=text_batch, model=self.model)
      result = [r.embedding for r in result.data]
      return result
   
   async def get_embeddings(self, text: str | list[str], batch_size: int = 16):
      if isinstance(text, str):
         text = [text]

      semaphore = asyncio.Semaphore(self.max_requests)
      async def _get_embedding_for_batch(text_batch):
         async with semaphore:
            return await self.get_embedding_for_batch(text_batch)

      tasks = []
      for i in range(0, len(text), batch_size):
         tasks.append(_get_embedding_for_batch(text[i:i+batch_size]))
      results = []
      for res in await asyncio.gather(*tasks):
         results.append(res[0])
      return results

if __name__ == "__main__":
   from dotenv import load_dotenv
   load_dotenv()
   print("xd")
   text = "Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum."

   embedder = Embedder()
   emb = asyncio.run(embedder.get_embeddings([text] * 1))
   print(emb)
   print(type(emb))
   print(len(emb))

   # df['ada_embedding'] = df.combined.apply(lambda x: get_embedding(x, model='text-embedding-3-small'))
   # df.to_csv('output/embedded_1k_reviews.csv', index=False)
