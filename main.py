import discord
import os
from dotenv import load_dotenv
import google.generativeai as genai

#load dotenv
load_dotenv()

# Configure Gemini API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Create the model
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config
)

# Load chat context from a file
def load_chat_context(file_choice):
    file_mapping = {
        "1": "chat1.txt",
        "2": "chat2.txt",
        "3": "chat3.txt",
    }
    file = file_mapping.get(file_choice, "chat1.txt")

    try:
        with open(file, "r") as f:
            return f.read()
    except FileNotFoundError:
        return ""

chat_context = load_chat_context("1")  # Default to chat1.txt

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message):
        global chat_context
        if message.author.bot or not message.content:
            return  # Ignore bot messages and empty messages

        if message.content.startswith("!setcontext"):
            # Change the context file
            try:
                file_choice = message.content.split()[1]
                new_context = load_chat_context(file_choice)
                if new_context:
                    chat_context = new_context
                    await message.reply(f"Context changed to chat{file_choice}.txt")
                else:
                    await message.reply(f"Failed to load chat{file_choice}.txt. Please check the file number.")
            except IndexError:
                await message.reply("Please provide a file number (1, 2, or 3) after the !setcontext command.")
            return

        chat_context += f"{message.author}: {message.content}\n"
        print(f'Message from {message.author}: {message.content}')

        # Check if the bot is mentioned in the message
        if message.mentions and any(m.id == self.user.id for m in message.mentions):
            # Extract the question or prompt without the mention
            content = message.content.strip()
            content = content.split(maxsplit=1)[1] if len(content.split()) > 1 else ""

            if content:
                try:
                    # Generate response using the Gemini API
                    prompt = f"{chat_context}\nBot:"
                    result = model.generate_content(prompt)
                    response_text = result.text[:1999]  # Discord message cutoff

                    # Append the bot's response to the chat context
                    chat_context += f"Bot: {response_text}\n"

                    print(response_text)
                    await message.reply(response_text)
                except Exception as e:
                    print(f"Error: {e}")
            else:
                # If no content after mention, prompt user to include a question
                await message.reply(f"Hi {message.author.mention}, it seems you mentioned me but didn't ask a question! Feel free to ask anything, and I'll do my best to help.")
        else:
            # If bot is not mentioned, suggest mentioning it for a response
            await message.reply(f"Hi {message.author.mention}, to get a response from me, you can mention me (like you did in other chats) followed by your question or prompt.")

# Discord bot token
token = os.getenv("SECRET_KEY")

# Create Discord client with intents
intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)

# Run the Discord bot
client.run(token)