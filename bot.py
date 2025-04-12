import discord
import os
import asyncio
import datetime
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# --- Configurações Globais ---
TOKEN = os.getenv("DISCORD_TOKEN")
ID_CARGO_PADRAO_STR = os.getenv('ID_DO_CARGO_PARA_ADICIONAR')
COMANDO_TELAGEM = "!telagem"  # Comando para iniciar o guia
CANAL_TELAGEM_NOME = "woo-chat"  # Nome EXATO do canal onde o comando funciona

# --- Lista de Passos da Telagem (Personalize!) ---
PASSOS_TELAGEM = [
    "Verifique os processos em execução no Gerenciador de Tarefas (Ctrl+Shift+Esc). Procure por nomes suspeitos ou uso excessivo de recursos.",
    "Analise o histórico de execução de programas (Prefetch). Vá em C:\\Windows\\Prefetch e ordene por data.",
    "Verifique pastas comuns de cheats: %appdata%, %localappdata%, Documentos. Procure por pastas/arquivos com nomes suspeitos.",
    "Use ferramentas como Process Hacker ou System Informer para uma análise mais profunda dos processos (verifique strings, módulos carregados).",
    "Verifique o histórico do navegador e downloads em busca de sites ou arquivos relacionados a cheats.",
    "Examine a lixeira em busca de arquivos suspeitos deletados recentemente.",
    "Utilize strings específicas conhecidas de cheats em ferramentas de busca de arquivos (ex: Everything) ou no próprio Process Hacker.",
    "Analise logs específicos de jogos ou launchers, se aplicável.",
    "Verifique configurações de sobreposição (overlay) de programas como Discord, MSI Afterburner, etc.",
    "Finalize a verificação e tome sua decisão.",
    # DPS EU ADD MAIS FODASE E ARRUMO TB 
]

# --- Validação do ID do Cargo ---
ID_CARGO_PADRAO = None
if ID_CARGO_PADRAO_STR:
    try:
        ID_CARGO_PADRAO = int(ID_CARGO_PADRAO_STR)
    except ValueError:
        print(f"Erro Crítico: O valor '{ID_CARGO_PADRAO_STR}' para 'ID_DO_CARGO_PARA_ADICIONAR' no arquivo .env não é um ID numérico válido.")
        exit()
else:
    print("Erro Crítico: A chave 'ID_DO_CARGO_PARA_ADICIONAR' não foi encontrada no arquivo .env.")
    exit()

# --- Configuração das Intents ---
intents = discord.Intents.default()
intents.members = True  # Necessária para on_member_join
intents.message_content = True  # <<< ADICIONADO: ESSENCIAL para ler mensagens!

# --- Inicialização do Bot ---
bot = discord.Client(intents=intents)

# --- Eventos do Bot ---

@bot.event
async def on_ready():
    """Evento chamado quando o bot está conectado e pronto."""
    print(f'Bot conectado como {bot.user.name}#{bot.user.discriminator}')
    print(f'ID do Bot: {bot.user.id}')
    # Mensagens combinadas de ambas as funcionalidades
    print(f'Pronto para adicionar cargo com ID: {ID_CARGO_PADRAO}')
    print(f'Pronto para guiar telagens no canal "{CANAL_TELAGEM_NOME}" com o comando "{COMANDO_TELAGEM}"')
    print('-------')

@bot.event
async def on_member_join(member: discord.Member):
    """Evento chamado quando um novo membro entra no servidor."""
    print(f'{member.name}#{member.discriminator} (ID: {member.id}) entrou no servidor {member.guild.name}.')
    guild = member.guild
    cargo_para_adicionar = guild.get_role(ID_CARGO_PADRAO)

    if cargo_para_adicionar:
        try:
            await member.add_roles(cargo_para_adicionar, reason="Cargo automático de entrada")
            print(f'Cargo "{cargo_para_adicionar.name}" (ID: {ID_CARGO_PADRAO}) adicionado a {member.name}#{member.discriminator}.')
        except discord.Forbidden:
            print(f'Erro de Permissão (on_member_join): Não foi possível adicionar o cargo "{cargo_para_adicionar.name}" a {member.name}. Verifique hierarquia/permissões.')
        except discord.HTTPException as e:
            print(f'Erro de Rede/HTTP (on_member_join) ao tentar adicionar o cargo a {member.name}: {e}')
        except Exception as e:
            print(f'Ocorreu um erro inesperado (on_member_join) ao processar {member.name}: {e}')
    else:
        print(f'Erro de Configuração (on_member_join): Cargo com ID {ID_CARGO_PADRAO} não encontrado no servidor "{guild.name}".')

@bot.event
async def on_message(message: discord.Message):
    """Evento chamado quando uma mensagem é enviada."""

    # Ignorar mensagens do próprio bot
    if message.author == bot.user:
        return

    # Verificar se a mensagem está no canal correto
    # TODO: Considerar usar ID do canal para robustez: if message.channel.id != SEU_ID_DE_CANAL_AQUI: return
    if message.channel.name != CANAL_TELAGEM_NOME:
        return

    # Verificar se a mensagem é o comando de telagem
    if message.content.lower().startswith(COMANDO_TELAGEM):
        print(f"Comando '{COMANDO_TELAGEM}' detectado de {message.author.name} no canal '{message.channel.name}'")

        agora = datetime.datetime.now()
        hora_inicio_formatada = agora.strftime("%H:%M:%S")

        try:
            await message.channel.send(f"Ok, {message.author.mention}! Iniciando guia de telagem às **{hora_inicio_formatada}**. Siga os passos:")
            await asyncio.sleep(1.5)

            for i, passo in enumerate(PASSOS_TELAGEM, 1):
                await message.channel.send(f"**Passo {i}:** {passo}")
                # Aumentei um pouco o delay para dar mais tempo de ler
                await asyncio.sleep(3.0)

            await message.channel.send(f"Guia de telagem concluído, {message.author.mention}. Boa sorte!")
            print(f"Guia de telagem enviado para {message.author.name}.")

        except discord.Forbidden:
            print(f"Erro de Permissão (on_message): Não tenho permissão para enviar mensagens no canal '{message.channel.name}' ({message.channel.id}).")
        except discord.HTTPException as e:
            print(f"Erro de Rede/HTTP (on_message) ao tentar enviar guia: {e}")
        except Exception as e:
            print(f"Ocorreu um erro inesperado (on_message) ao enviar guia: {e}")


# --- Execução do Bot ---
if TOKEN is None:
    print("Erro Crítico: Token do Discord (DISCORD_TOKEN) não encontrado no arquivo .env. Verifique o arquivo.")
else:
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("Erro Crítico: Falha no login. O token fornecido no arquivo .env é inválido.")
    except discord.PrivilegedIntentsRequired as e:
        print(f"Erro Crítico: Intents privilegiadas não estão habilitadas ({e}). Verifique as configurações do bot no Portal de Desenvolvedores (Members e **Message Content** devem estar ATIVAS).")
    except Exception as e:
        print(f"Ocorreu um erro fatal ao tentar iniciar ou rodar o bot: {e}")