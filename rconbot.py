import disnake
import asyncio
from disnake.ext import commands
from mcrcon import MCRcon

TOKEN = 'token'
CHANNEL_ID = 1234567891234567

MINECRAFT_SERVER = 'ip'
MINECRAFT_RCON_PORT = 25568
MINECRAFT_RCON_PASSWORD = 'password'

intents = disnake.Intents.all()
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)


async def send_to_minecraft_server(command):
    try:
        with MCRcon(MINECRAFT_SERVER, MINECRAFT_RCON_PASSWORD, port=MINECRAFT_RCON_PORT) as mcr:
            response = mcr.command(command)
        return response
    except Exception as e:
        return e


async def send_application(interaction, command, evidence):
    if command.split()[0] not in ['kick', 'ban', 'mute', 'tempban', 'tempmute', 'tempmuteip', 'tempbanip', 'banip', 'muteip']:
        await interaction.response.send_message("Неправильный формат команды. Допустимые команды: kick, ban, mute, tempban, tempmute, tempmuteip, tempbanip, banip, muteip", ephemeral=True)
        return

    channel = bot.get_channel(CHANNEL_ID)

    embed = disnake.Embed(title=f"Новая заявка на блокировку от {interaction.user.display_name}", color=disnake.Color.orange())
    embed.add_field(name="Команда:", value=command, inline=False)
    embed.add_field(name="Доказательство:", value=evidence, inline=False)
    if interaction.user.avatar:
        avatar_url = interaction.user.avatar.url
    else:
        avatar_url = interaction.user.default_avatar.url
    embed.set_footer(text=f"Запросил: {interaction.user.display_name}", icon_url=avatar_url)

    try:
        message = await channel.send(embed=embed)
        await message.add_reaction('✅')
        await message.add_reaction('❌')
    except Exception as e:
        await interaction.response.send_message(f"Ошибка при отправке заявки: {e}", ephemeral=True)

    await interaction.response.send_message("Ваш запрос на блокировку успешно отправлен.", ephemeral=True, components=[

    ])


@bot.event
async def on_ready():
    print("Я запустился")
    await update_status()


@bot.event
async def on_close():
    print("Я выключился")
    await bot.close()

async def update_status():
    await bot.wait_until_ready()
    while not bot.is_closed():
        await bot.change_presence(activity=disnake.Game(name="your.server.ru"), status=disnake.Status.dnd)
        await asyncio.sleep(300)

bot.loop.create_task(update_status())


@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    message = reaction.message
    if message.channel.id == CHANNEL_ID:
        embed = message.embeds[0]
        if embed:
            if reaction.emoji == '✅':
                embed.color = disnake.Color.green()
                embed.set_footer(text=f'Наказание успешно выдано: {user.display_name}')
                command = embed.fields[0].value
                response = await send_to_minecraft_server(command)
                if isinstance(response, Exception):
                    embed.color = disnake.Color.red()
                    embed.set_footer(text=f'Ошибка при выполнении команды на сервере Minecraft: {response}')
                    await message.edit(embed=embed, components=[
                    ])
                else:
                    if response:  # Проверяем, что response не пустой
                        await message.channel.send(response)
                    else:
                        await message.channel.send("Наказание выдано")
            elif reaction.emoji == '❌':
                embed.color = disnake.Color.red()
                embed.set_footer(text=f'Наказание не выдано: {user.display_name}')
            await message.edit(embed=embed)
            await message.clear_reactions()



@bot.slash_command(name='submit', description='Отправить заявку на нарушителя')
async def submit(interaction, команда: str, доказательство: str):
    await send_application(interaction, команда, доказательство)


bot.run(TOKEN)
