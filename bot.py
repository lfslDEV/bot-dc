import discord
import discord.ui
import os
import asyncio
import datetime
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()

# --- Configurações Globais ---
TOKEN = os.getenv("DISCORD_TOKEN")
ID_CARGO_PADRAO_STR = os.getenv('ID_DO_CARGO_PARA_ADICIONAR')
COMANDO_CLEAR = "!clear"
# Comando para Administradores postarem/atualizarem o menu de navegação
COMANDO_SETUP_NAVEGACAO = "!setup_navegacao"

# <<< IDs dos Canais (SUBSTITUA PELOS SEUS IDs REAIS!) >>>
ID_CANAL_PRINCIPAL = 111111111111111111  # ID do canal onde o menu ficará (ex: #bem-vindo ou #regras)
ID_CANAL_GUIA_TELAGEM = 222222222222222222 # ID do canal onde estão os passos/comandos da telagem

# --- Validação do ID do Cargo ---
ID_CARGO_PADRAO = None
if ID_CARGO_PADRAO_STR:
    try:
        ID_CARGO_PADRAO = int(ID_CARGO_PADRAO_STR)
    except ValueError:
        print(f"Erro Crítico: O valor '{ID_CARGO_PADRAO_STR}' para 'ID_DO_CARGO_PARA_ADICIONAR' no .env não é um número válido.")
        exit()
else:
    # Se ID_DO_CARGO_PARA_ADICIONAR não for essencial, pode só avisar:
    # print("Aviso: A chave 'ID_DO_CARGO_PARA_ADICIONAR' não foi encontrada no .env. Função de auto-role desativada.")
    # Ou manter como erro crítico se for essencial:
    print("Erro Crítico: A chave 'ID_DO_CARGO_PARA_ADICIONAR' não foi encontrada no .env.")
    exit()


# --- Configuração das Intents ---
intents = discord.Intents.default()
intents.members = True          # Necessária para on_member_join
intents.message_content = True  # Necessária para ler comandos (!setup_navegacao, !clear)

# --- Inicialização do Bot ---
bot = discord.Client(intents=intents)

# --- Mapeamento Simplificado de Opções para Canais ---
MAPA_NAVEGACAO = {
    "nav_telagem": ID_CANAL_GUIA_TELAGEM,
}

# --- View Persistente Simplificada para Navegação ---
class NavigationSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # View não expira

    @discord.ui.select(
        custom_id="navigation_select_menu_v1", # ID Fixo (mudei para v1 para evitar conflito se a antiga ainda estiver registrada)
        placeholder="Selecione um tópico para ser direcionado...",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(
                label="Guia de Telagem",
                value="nav_telagem", # Valor interno para mapeamento
                description="Precisa verificar algum usuário? Vá para o canal de telagem.",
                emoji="🔍" # Emoji opcional
            ),
            # Removido: Opção de Regex
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        """Callback chamado quando uma opção é selecionada."""
        selected_value = select.values[0]
        user = interaction.user

        target_channel_id = MAPA_NAVEGACAO.get(selected_value)

        if target_channel_id:
            target_channel = bot.get_channel(target_channel_id)
            if target_channel:
                # Resposta EFÊMERA direcionando o usuário
                await interaction.response.send_message(
                    f"Olá {user.mention}! Para encontrar informações e procedimentos sobre **Telagem**, por favor, vá para o canal {target_channel.mention}.",
                    ephemeral=True # Mensagem visível apenas para quem clicou
                )
                print(f"Usuário {user.name} direcionado para o canal '{target_channel.name}' via menu de navegação (Telagem).")
            else:
                await interaction.response.send_message(
                    "Desculpe, não consegui encontrar o canal de destino configurado para a telagem.",
                    ephemeral=True
                )
                print(f"Erro: Canal de Telagem com ID {target_channel_id} não encontrado (opção '{selected_value}').")
        else:
            await interaction.response.send_message(
                "Desculpe, ocorreu um erro ao processar sua seleção (opção desconhecida).",
                ephemeral=True
            )
            print(f"Erro: Valor '{selected_value}' do menu não encontrado no MAPA_NAVEGACAO.")

# --- Eventos do Bot ---

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user.name}#{bot.user.discriminator}')
    # Adiciona a View persistente ao bot
    bot.add_view(NavigationSelectView())
    print("View de Navegação Persistente (simplificada) adicionada.")
    print(f'ID do Bot: {bot.user.id}')
    if ID_CARGO_PADRAO:
        print(f'Pronto para adicionar cargo com ID: {ID_CARGO_PADRAO}')
    else:
        print("Função de adicionar cargo automático DESATIVADA (ID não configurado).")
    print(f'Pronto para limpar mensagens com o comando "{COMANDO_CLEAR}"')
    print(f'Pronto para configurar menu de navegação com "{COMANDO_SETUP_NAVEGACAO}" no canal ID {ID_CANAL_PRINCIPAL}')
    print('-------')

@bot.event
async def on_member_join(member: discord.Member):
    """Evento chamado quando um novo membro entra no servidor."""
    if not ID_CARGO_PADRAO: # Se o cargo não foi configurado, não faz nada
        return

    print(f'{member.name}#{member.discriminator} (ID: {member.id}) entrou no servidor {member.guild.name}.')
    guild = member.guild
    cargo_para_adicionar = guild.get_role(ID_CARGO_PADRAO)

    if cargo_para_adicionar:
        try:
            await member.add_roles(cargo_para_adicionar, reason="Cargo automático de entrada")
            print(f'Cargo "{cargo_para_adicionar.name}" (ID: {ID_CARGO_PADRAO}) adicionado a {member.name}#{member.discriminator}.')
        except discord.Forbidden:
            print(f'Erro de Permissão (on_member_join): Não foi possível adicionar o cargo "{cargo_para_adicionar.name}" a {member.name}. Verifique hierarquia/permissões do BOT.')
        except discord.HTTPException as e:
            print(f'Erro de Rede/HTTP (on_member_join) ao tentar adicionar o cargo a {member.name}: {e}')
        except Exception as e:
            print(f'Ocorreu um erro inesperado (on_member_join) ao processar {member.name}: {e}')
    else:
        print(f'Erro de Configuração (on_member_join): Cargo com ID {ID_CARGO_PADRAO} não encontrado no servidor "{guild.name}". Verifique o ID no .env.')


@bot.event
async def on_message(message: discord.Message):
    """Evento chamado quando uma mensagem é enviada."""
    # Ignorar mensagens do próprio bot ou de outros bots
    if message.author.bot:
        return

    # --- Comando de Setup para Administradores ---
    if message.content.lower() == COMANDO_SETUP_NAVEGACAO:
        # 1. Verificar permissão (Administrador)
        if not message.author.guild_permissions.administrator:
            await message.reply("Apenas administradores podem usar este comando.", delete_after=10)
            try: await message.delete(delay=10)
            except: pass
            return

        # 2. Encontrar o canal principal
        canal_principal = bot.get_channel(ID_CANAL_PRINCIPAL)
        if not canal_principal:
            print(f"Erro Crítico: Canal principal com ID {ID_CANAL_PRINCIPAL} não encontrado.")
            await message.reply(f"Erro: Não encontrei o canal configurado com ID {ID_CANAL_PRINCIPAL}.")
            return

        # 3. (Opcional) Deletar mensagens antigas do menu do bot neste canal
        try:
            async for msg in canal_principal.history(limit=50):
                if msg.author.id == bot.user.id and msg.components:
                     # Verifica se a view é a nossa pelo custom_id (mais seguro)
                     if msg.components and isinstance(msg.components[0], discord.ActionRow):
                         first_component = msg.components[0].children[0]
                         if isinstance(first_component, discord.ui.Select) and first_component.custom_id == "navigation_select_menu_v1":
                             print(f"Deletando mensagem antiga do menu (ID: {msg.id})")
                             await msg.delete()
                             # break # Descomente para deletar só a mais recente
        except discord.Forbidden:
            print(f"Aviso: Sem permissão para ler histórico ou deletar mensagens no canal '{canal_principal.name}'.")
        except Exception as e:
            print(f"Erro ao tentar limpar mensagens antigas do menu: {e}")


        # 4. Criar e enviar a nova mensagem com a view simplificada
        print(f"Comando '{COMANDO_SETUP_NAVEGACAO}' executado por {message.author.name}.")
        view_navegacao = NavigationSelectView()
        try:
            await canal_principal.send(
                "**Bem-vindo(a)!** 👋\n\n"
                "Precisa de ajuda com a **verificação de usuários (Telagem)**? Selecione abaixo para ser direcionado ao canal correto:",
                view=view_navegacao
            )
            await message.reply("✅ Menu de navegação para Telagem configurado/atualizado!", delete_after=10)
            print(f"Menu de navegação (Telagem) postado no canal '{canal_principal.name}'.")
        except discord.Forbidden:
             print(f"Erro Crítico: Bot sem permissão para enviar mensagens no canal principal '{canal_principal.name}'.")
             await message.reply(f"Erro: Não tenho permissão para enviar mensagens no canal {canal_principal.mention}.")
        except Exception as e:
             print(f"Erro inesperado ao enviar menu de navegação: {e}")
             await message.reply("Ocorreu um erro ao tentar configurar o menu.")

        # 5. Deletar a mensagem de comando do admin
        try:
            await message.delete()
        except discord.Forbidden:
            print(f"Aviso: Sem permissão para deletar a mensagem do comando '{COMANDO_SETUP_NAVEGACAO}'.")
        except Exception as e:
            print(f"Erro ao deletar mensagem do comando '{COMANDO_SETUP_NAVEGACAO}': {e}")


    # --- Lógica do Comando !clear (sem alterações, funciona em qualquer canal) ---
    elif message.content.lower().startswith(COMANDO_CLEAR):
        print(f"Comando '{COMANDO_CLEAR}' detectado de {message.author.name} no canal '{message.channel.name}'")

        # 1. Verificar permissão do USUÁRIO para gerenciar mensagens *neste canal*
        if not message.author.guild_permissions.manage_messages:
            try:
                await message.channel.send(f"{message.author.mention}, você não tem permissão para gerenciar mensagens neste canal.", delete_after=10)
            except discord.Forbidden:
                print(f"Erro: Bot sem permissão de enviar msg de erro de permissão no canal {message.channel.name}")
            print(f"Usuário {message.author.name} tentou usar !clear sem permissão no canal {message.channel.name}.")
            return

        # 2. Extrair a quantidade
        try:
            parts = message.content.split()
            if len(parts) < 2:
                await message.channel.send(f"Uso correto: `{COMANDO_CLEAR} <quantidade>` (ex: `{COMANDO_CLEAR} 10`)", delete_after=10)
                return
            amount_to_delete = int(parts[1])
            if amount_to_delete <= 0:
                 await message.channel.send(f"Por favor, insira um número positivo.", delete_after=10)
                 return
            limit = 100 # Limite seguro padrão do Discord por vez
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

        # 3. Deletar as mensagens (verificando permissão do BOT)
        try:
            # Verifica permissão do BOT *antes* de tentar deletar
            bot_perms = message.channel.permissions_for(message.guild.me)
            if not bot_perms.manage_messages:
                 print(f"Erro de Permissão (on_message - clear): **O BOT** não tem permissão 'Gerenciar Mensagens' no canal '{message.channel.name}' ({message.channel.id}).")
                 await message.channel.send(f"Erro: Eu não tenho a permissão 'Gerenciar Mensagens' neste canal para apagar mensagens.", delete_after=10)
                 return

            # Adiciona 1 para incluir a mensagem do comando !clear na contagem
            deleted_messages = await message.channel.purge(limit=amount_to_delete + 1, check=lambda m: not m.pinned) # Não apaga mensagens fixadas
            # Mensagem de confirmação que some (opcional)
            confirm_msg = await message.channel.send(f"{len(deleted_messages) - 1} mensagens apagadas por {message.author.mention}.", delete_after=5)
            print(f"{len(deleted_messages) - 1} mensagens apagadas por {message.author.name} no canal {message.channel.name}")

        except discord.Forbidden:
            # Este erro geralmente indica que o bot não tem permissão, mas a verificação acima deve pegá-lo.
            # Pode ocorrer em casos raros ou se a permissão for revogada entre a verificação e a ação.
            print(f"Erro de Permissão Inesperado (on_message - clear): Falha ao apagar mensagens no canal '{message.channel.name}'.")
            try: await message.channel.send(f"Erro: Falha ao apagar mensagens. Verifique minhas permissões.", delete_after=10)
            except discord.Forbidden: pass
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