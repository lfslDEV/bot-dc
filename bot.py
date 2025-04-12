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
COMANDO_TELAGEM = "!telagem"        # Comando para iniciar o guia
CANAL_TELAGEM_NOME = "chat-woo"     # Nome EXATO do canal onde o comando de telagem funciona
COMANDO_CLEAR = "!clear"            # <<< NOVO >>> Comando para limpar mensagens

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
]

# --- Validação do ID do Cargo ---
ID_CARGO_PADRAO = None
if ID_CARGO_PADRAO_STR:
    try:
        ID_CARGO_PADRAO = int(ID_CARGO_PADRAO_STR)
    except ValueError:
        print(f"Erro Crítico: O valor '{ID_CARGO_PADRAO_STR}' para 'ID_DO_CARGO_PARA_ADICIONAR' no .env não é um número válido.")
        exit()
else:
    print("Erro Crítico: A chave 'ID_DO_CARGO_PARA_ADICIONAR' não foi encontrada no .env.")
    exit()

# --- Configuração das Intents ---
intents = discord.Intents.default()
intents.members = True          # Necessária para on_member_join
intents.message_content = True  # Necessária para ler comandos (!telagem, !clear)

# --- Inicialização do Bot ---
bot = discord.Client(intents=intents)

# --- Eventos do Bot ---

@bot.event
async def on_ready():
    """Evento chamado quando o bot está conectado e pronto."""
    print(f'Bot conectado como {bot.user.name}#{bot.user.discriminator}')
    print(f'ID do Bot: {bot.user.id}')
    print(f'Pronto para adicionar cargo com ID: {ID_CARGO_PADRAO}')
    print(f'Pronto para guiar telagens no canal "{CANAL_TELAGEM_NOME}" com o comando "{COMANDO_TELAGEM}"')
    print(f'Pronto para limpar mensagens com o comando "{COMANDO_CLEAR}"') # <<< NOVO >>>
    print('-------')

@bot.event
async def on_member_join(member: discord.Member):
    """Evento chamado quando um novo membro entra no servidor."""
    # Código para adicionar cargo (sem alterações)
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

    # Ignorar mensagens do próprio bot ou de outros bots
    if message.author.bot:
        return

    # --- Lógica do Comando !telagem ---
    # Verificar se a mensagem está no canal correto para !telagem
    if message.channel.name == CANAL_TELAGEM_NOME and message.content.lower().startswith(COMANDO_TELAGEM):
        print(f"Comando '{COMANDO_TELAGEM}' detectado de {message.author.name} no canal '{message.channel.name}'")
        agora = datetime.datetime.now()
        hora_inicio_formatada = agora.strftime("%H:%M:%S")
        try:
            await message.channel.send(f"Ok, {message.author.mention}! Iniciando guia de telagem às **{hora_inicio_formatada}**. Siga os passos:")
            await asyncio.sleep(1.5)
            for i, passo in enumerate(PASSOS_TELAGEM, 1):
                await message.channel.send(f"**Passo {i}:** {passo}")
                await asyncio.sleep(3.0)
            await message.channel.send(f"Guia de telagem concluído, {message.author.mention}. Boa sorte!")
            print(f"Guia de telagem enviado para {message.author.name}.")
        except discord.Forbidden:
            print(f"Erro de Permissão (on_message - telagem): Não tenho permissão para enviar mensagens no canal '{message.channel.name}' ({message.channel.id}).")
        except discord.HTTPException as e:
            print(f"Erro de Rede/HTTP (on_message - telagem) ao tentar enviar guia: {e}")
        except Exception as e:
            print(f"Ocorreu um erro inesperado (on_message - telagem) ao enviar guia: {e}")

    # --- <<< NOVO >>> Lógica do Comando !clear ---
    elif message.content.lower().startswith(COMANDO_CLEAR):
        print(f"Comando '{COMANDO_CLEAR}' detectado de {message.author.name} no canal '{message.channel.name}'")

        # 1. Verificar permissão do USUÁRIO
        if not message.author.guild_permissions.manage_messages:
            try:
                await message.channel.send(f"{message.author.mention}, você não tem permissão para gerenciar mensagens neste canal.", delete_after=10)
            except discord.Forbidden:
                print(f"Erro: Bot sem permissão de enviar mensagem de erro de permissão no canal {message.channel.name}") # Log se não puder nem enviar o erro
            print(f"Usuário {message.author.name} tentou usar !clear sem permissão.")
            return # Para a execução se o usuário não tem permissão

        # 2. Extrair a quantidade de mensagens a deletar
        try:
            # Divide a mensagem em partes (ex: "!clear", "10")
            parts = message.content.split()
            if len(parts) < 2: # Verifica se o número foi fornecido
                await message.channel.send(f"Uso correto: `{COMANDO_CLEAR} <quantidade>` (ex: `{COMANDO_CLEAR} 10`)", delete_after=10)
                return

            amount_to_delete = int(parts[1]) # Tenta converter o segundo argumento para número

            if amount_to_delete <= 0: # Não permite números negativos ou zero
                 await message.channel.send(f"Por favor, insira um número positivo.", delete_after=10)
                 return

            # Limite opcional (Discord tem limites, bom colocar um teto razoável)
            limit = 100
            if amount_to_delete > limit:
                await message.channel.send(f"Só posso apagar até {limit} mensagens por vez.", delete_after=10)
                amount_to_delete = limit

        except ValueError:
            await message.channel.send(f"'{parts[1]}' não é um número válido. Use: `{COMANDO_CLEAR} <quantidade>`", delete_after=10)
            return
        except Exception as e:
            print(f"Erro ao processar argumentos do !clear: {e}")
            await message.channel.send(f"Ocorreu um erro ao processar seu comando.", delete_after=10)
            return

        # 3. Deletar as mensagens (incluindo o comando !clear)
        try:
            # Adiciona 1 para incluir a mensagem do comando !clear na contagem
            deleted_messages = await message.channel.purge(limit=amount_to_delete + 1)
            
        except discord.Forbidden:
            # Erro se o BOT não tem permissão
            print(f"Erro de Permissão (on_message - clear): **O BOT** não tem permissão 'Gerenciar Mensagens' no canal '{message.channel.name}' ({message.channel.id}).")
            try:
                await message.channel.send(f"Erro: Eu não tenho permissão para apagar mensagens neste canal.", delete_after=10)
            except discord.Forbidden:
                pass # Ignora se não puder nem enviar a mensagem de erro
        except discord.HTTPException as e:
            print(f"Erro de Rede/HTTP (on_message - clear) ao tentar apagar mensagens: {e}")
            await message.channel.send(f"Ocorreu um erro de comunicação com o Discord ao tentar apagar as mensagens.", delete_after=10)
        except Exception as e:
            print(f"Ocorreu um erro inesperado (on_message - clear): {e}")
            await message.channel.send(f"Ocorreu um erro inesperado ao tentar apagar as mensagens.", delete_after=10)


# --- Execução do Bot ---
if TOKEN is None:
    print("Erro Crítico: Token do Discord (DISCORD_TOKEN) não encontrado no arquivo .env. Verifique o arquivo.")
else:
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("Erro Crítico: Falha no login. O token fornecido no arquivo .env é inválido.")
    except discord.PrivilegedIntentsRequired as e:
        print(f"Erro Crítico: Intents privilegiadas não estão habilitadas ({e}). Verifique Portal Dev (Members e Message Content ATIVAS).")
    except Exception as e:
        print(f"Ocorreu um erro fatal ao tentar iniciar ou rodar o bot: {e}")