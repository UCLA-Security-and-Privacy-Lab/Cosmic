from openai import OpenAI

client = OpenAI()

SYSTEM_MSG = '''
You are a website analyzer. I will give you a screenshot of the website. Please answer me in the following format: {"Form Count": , "", "Forms":[List[Element_Type, Element Text], List[Element_Type, Element Text],]}

The Element_Type should be in the list ["STATIC_TEXT", "textbox", "button", "checkbox", "combobox", ]
'''


response = client.chat.completions.create(
  model="gpt-4o",
  messages=[
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "What’s in this image?"},
        {
          "type": "image_url",
          "image_url": {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg",
          },
        },
      ],
    }
  ],
  max_tokens=300,
)

print(response.choices[0])