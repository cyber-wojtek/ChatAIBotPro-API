# ChatAIBotPro-API

Unofficial async Python client for [chataibot.pro](https://chataibot.pro).

> **Disclaimer:** This library reverse-engineers the chataibot.pro browser API.
> It is not affiliated with or endorsed by chataibot.pro.

## Installation

```sh
pip install chataibotpro-webapi
```

## Authentication

Get your JWT token from the `token` cookie after logging in at
[chataibot.pro](https://chataibot.pro/app/chat).

```py
import asyncio
from chataibotpro_webapi import ChatAIBotProClient

async def main():
    async with ChatAIBotProClient("YOUR_JWT_TOKEN") as client:
        async for chunk in client.stream_message("Hello!"):
            print(chunk.delta, end="", flush=True)
        print()

asyncio.run(main())
```

## Usage

### Single-turn (non-streaming)

```py
r = await client.send_message("What is the capital of Poland?")
print(r.text)
```

### Streaming

```py
async for chunk in client.stream_message("Write me a haiku."):
    print(chunk.delta, end="", flush=True)
print()
```

### Multi-turn session

```py
chat = client.start_chat()
r1 = await chat.send("My name is Alice.")
r2 = await chat.send("What is my name?")
print(r2.text)  # "Your name is Alice."

# Streaming within a session
async for chunk in chat.stream("Tell me a story."):
    print(chunk.delta, end="", flush=True)
```

### Image generation

```py
from chataibotpro_webapi import ImageModel

img = await client.generate_image(
    "A golden sunset over Warsaw, oil painting",
    model=ImageModel.FLUX_PRO,
)
await img.save("./outputs")
```

### Video generation

```py
from chataibotpro_webapi import VideoModel

video = await client.generate_video(
    "A drone shot flying over Warsaw at sunset",
    model=VideoModel.KLING_2_6_PRO,
    duration="5",
)
await video.save("./outputs")

# Image to video
video2 = await client.image_to_video(
    "https://example.com/frame.jpg",
    prompt="Camera slowly pans left",
)
```

### Gallery

```py
images = await client.get_image_gallery()
videos = await client.get_video_gallery()

for item in images:
    await item.save("./gallery")
```

### File upload

```py
rec = await client.upload_file("report.pdf")
r   = await client.send_message("Summarise this document.")
```

### Token estimation

```py
usage = await client.calculate_tokens("Write me an essay", model="gpt-4.1-nano")
print(usage.token_count, usage.credit_cost)
```

### Pricing

```py
prices = await client.get_subscription_prices()
tariff = await client.get_subscription_tariff()
```

### User info

```py
user = await client.get_current_user()
print(user.email, user.plan)

stats = await client.get_answers_count()
```

## API Reference

| Method | Description |
|---|---|
| `stream_message(text, ...)` | Stream a chat response |
| `send_message(text, ...)` | Send message, collect full response |
| `start_chat(model, ...)` | Create a `ChatSession` |
| `create_context(title, model)` | Create server-side chat thread |
| `get_context(chat_id)` | Fetch chat metadata |
| `calculate_tokens(text, ...)` | Estimate token cost |
| `change_context_model(chat_id, model)` | Change model for a chat |
| `get_chat_messages(chat_id)` | Fetch message history |
| `generate_image(prompt, model, ...)` | Generate image |
| `generate_video(prompt, model, ...)` | Generate video |
| `image_to_video(image_url, prompt, ...)` | Animate image to video |
| `get_gallery(...)` | Fetch media gallery |
| `get_image_gallery(...)` | Images only |
| `get_video_gallery(...)` | Videos only |
| `upload_file(file_path, ...)` | Upload & parse file |
| `get_current_user()` | Fetch user profile |
| `get_answers_count()` | Fetch usage stats |
| `get_subscription_prices(...)` | Fetch pricing |
| `get_subscription_tariff(...)` | Fetch tariff details |
| `get_telegram_link(...)` | Get Telegram deep-link |
| `landing_hello()` | Ping / landing data |
| `logout()` | Invalidate server session |

## License

MIT
