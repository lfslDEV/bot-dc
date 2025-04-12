import discord
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Carrega o TOKEN do bot a partir do .env
TOKEN = os.getenv("DISCORD_TOKEN")

# Carrega o ID do CARGO a ser adicionado a partir do .env
ID_CARGO_PADRAO_STR = os.getenv('ID_DO_CARGO_PARA_ADICIONAR') # Usa a chave definida no .env

# Valida e converte o ID do Cargo para inteiro
ID_CARGO_PADRAO = None
if ID_CARGO_PADRAO_STR:
    try:
        ID_CARGO_PADRAO = int(ID_CARGO_PADRAO_STR) # Tenta converter para número
    except ValueError:
        # Se não for um número válido no .env, imprime erro e sai
        print(f"Erro Crítico: O valor '{ID_CARGO_PADRAO_STR}' para 'ID_DO_CARGO_PARA_ADICIONAR' no arquivo .env não é um ID numérico válido.")
        exit() # Encerra o script
else:
    # Se a chave não for encontrada no .env, imprime erro e sai
    print("Erro Crítico: A chave 'ID_DO_CARGO_PARA_ADICIONAR' não foi encontrada no arquivo .env.")
    exit() # Encerra o script

# --- Configuração das Intents ---
# Habilita as intents necessárias (membros é essencial para on_member_join)
intents = discord.Intents.default()
intents.members = True

bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    """Evento chamado quando o bot está conectado e pronto."""
    print(f'Bot conectado como {bot.user.name}#{bot.user.discriminator}')
    print(f'ID do Bot: {bot.user.id}')
    # --- CORRIGIDO ---
    # Imprime o ID do cargo que foi carregado da variável
    print(f'Pronto para adicionar cargo com ID: {ID_CARGO_PADRAO}')
    print('-------')

@bot.event
async def on_member_join(member: discord.Member):
    """Evento chamado quando um novo membro entra no servidor."""
    print(f'{member.name}#{member.discriminator} (ID: {member.id}) entrou no servidor {member.guild.name}.')

    # Pega o objeto do servidor (guild) onde o membro entrou
    guild = member.guild

    # --- CORRIGIDO ---
    # Busca o objeto do cargo usando o ID carregado da variável ID_CARGO_PADRAO
    cargo_para_adicionar = guild.get_role(ID_CARGO_PADRAO)

    if cargo_para_adicionar:
        try:
            # Adiciona o cargo ao novo membro
            await member.add_roles(cargo_para_adicionar, reason="Cargo automático de entrada") # Adiciona um motivo opcional
            print(f'Cargo "{cargo_para_adicionar.name}" (ID: {ID_CARGO_PADRAO}) adicionado a {member.name}#{member.discriminator}.')
        except discord.Forbidden:
            print(f'Erro de Permissão: Não foi possível adicionar o cargo "{cargo_para_adicionar.name}" a {member.name}. '
                  f'Verifique se o cargo do bot (ID: {bot.user.id}) está posicionado ACIMA do cargo "{cargo_para_adicionar.name}" (ID: {ID_CARGO_PADRAO}) na lista de cargos do servidor '
                  f'e se o bot tem a permissão "Gerenciar Cargos".')
        except discord.HTTPException as e:
            print(f'Erro de Rede/HTTP ao tentar adicionar o cargo a {member.name}: {e}')
        except Exception as e:
            print(f'Ocorreu um erro inesperado ao processar {member.name}: {e}')
    else:
        # --- CORRIGIDO ---
        # Usa a variável ID_CARGO_PADRAO na mensagem de erro
        print(f'Erro de Configuração: Cargo com ID {ID_CARGO_PADRAO} (definido em .env) não foi encontrado no servidor "{guild.name}". '
              f'Verifique se o ID no arquivo .env está correto e se o cargo ainda existe neste servidor.')

# --- Verificações antes de iniciar ---
if TOKEN is None:
    print("Erro Crítico: Token do Discord (DISCORD_TOKEN) não encontrado no arquivo .env. Verifique o arquivo.")
# A verificação do ID_CARGO_PADRAO já causa 'exit()' se houver erro,
# então não precisamos de um 'elif' específico aqui, mas garantimos que o TOKEN existe.
else:
    try:
        # Inicia o bot usando o TOKEN carregado do .env
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("Erro Crítico: Falha no login. O token fornecido no arquivo .env é inválido. Verifique se copiou o NOVO token corretamente.")
    except discord.PrivilegedIntentsRequired:
        print("Erro Crítico: Intents privilegiadas (Server Members Intent) não estão habilitadas para este bot no Portal de Desenvolvedores do Discord. Vá até a página do seu bot e ative-a na seção 'Privileged Gateway Intents'.")
    except Exception as e:
        print(f"Ocorreu um erro fatal ao tentar iniciar ou rodar o bot: {e}")