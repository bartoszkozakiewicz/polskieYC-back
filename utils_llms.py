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
   

class Describer:
   def __init__(self, model="gpt-4o-mini", max_requests: int =10):
      self.model = model
      self.client = AsyncOpenAI()
      self.max_requests = max_requests

   async def get_descriptions_for_batch(self, text_batch: str | list[str]):
      if isinstance(text_batch, list):
         text_batch = text_batch[0]

      messages = [
         {
            "role": "system",
            "content": (
               "You are a business expert with a background in academia.\n"
               "Your job is to summarize the researcher's skills, expertise and know-how based on their recent publications.\n"
               "You especially focus on the skills with high potential for commercialization.\n"
               "After each summary try to hypothesize what fields/industries, types of projects and problems in general the researcher's expertise could be useful for if any.\n"
               "[IMPORTANT] Please do not give general examples like `this could be used in healthcare` or this `could be used in finance`. Either we have a real life use case or we don't.\n"
               "At the end please give a score of 1-10 for the commercial potential of the researcher. This score should mainly reflect how likely the previous hypotheses are to be true and how powerful are those hypothesized implementations.\n"
            )
         },
         {
            "role": "user",
            "content": f"Please provide the summary and later scoring for the following researcher's recent publications:\n\n{text_batch}"
         }
      ]

      result =  await self.client.chat.completions.create(messages=messages, model=self.model)
      result = result.choices[0].message.content
      return result
   
   async def get_descriptions(self, text: str | list[str]):
      if isinstance(text, str):
         text = [text]

      semaphore = asyncio.Semaphore(self.max_requests)
      async def _get_descriptions_for_batch(text_batch):
         async with semaphore:
            return await self.get_descriptions_for_batch(text_batch)

      tasks = []
      batch_size = 1
      for i in range(0, len(text), batch_size):
         tasks.append(_get_descriptions_for_batch(text[i:i+batch_size]))
      results = []
      for res in await asyncio.gather(*tasks):
         results.append(res[0] if isinstance(res, list) else res)
      return results
   

if __name__ == "__main__":
   from dotenv import load_dotenv
   load_dotenv()
   text = "Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum."

   # embedder = Embedder()
   # emb = asyncio.run(embedder.get_embeddings([text] * 1))
   # print(emb)
   # print(type(emb))
   # print(len(emb))

   # df['ada_embedding'] = df.combined.apply(lambda x: get_embedding(x, model='text-embedding-3-small'))
   # df.to_csv('output/embedded_1k_reviews.csv', index=False)

   describer = Describer()
   descriptions = asyncio.run(describer.get_descriptions([text] * 6))
