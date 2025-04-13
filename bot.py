import discord
import os
import asyncio
import datetime
from dotenv import load_dotenv
from discord.ui import Button, View # <<< NOVO >>> Importações para UI (Botões)
from discord import PermissionOverwrite # <<< NOVO >>> Importação para Permissões de Canal

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# --- Configurações Globais ---
TOKEN = os.getenv("DISCORD_TOKEN")
ID_CARGO_PADRAO_STR = os.getenv('ID_DO_CARGO_PARA_ADICIONAR')
COMANDO_TELAGEM = "!telagem"        # Comando para iniciar o guia
CANAL_TELAGEM_NOME = "chat-woo"     # Nome EXATO do canal onde o comando de telagem funciona
COMANDO_CLEAR = "!clear"            # Comando para limpar mensagens
# <<< NOVO OPCIONAL >>> Adicione esta linha ao seu .env se quiser que mods/admins vejam os canais
ID_CARGO_MODERADOR_STR = os.getenv('ID_CARGO_MODERADOR', None)

# --- Lista de Passos da Telagem (Personalize!) ---
PASSOS_TELAGEM = [
    # Passo 1: Gerenciador de Tarefas
    "🔍 **Gerenciador de Tarefas** (`Ctrl+Shift+Esc`):\n   Verifique os *processos em execução*. Procure por nomes suspeitos ou uso excessivo de CPU/Memória/Disco.",
    "\n" 
    # Passo 2: Prefetch
    "⏱️ **Histórico de Execução (Prefetch)**:\n   Acesse `C:\\Windows\\Prefetch`. Ordene por 'Data de modificação' para ver programas executados recentemente. Analise nomes suspeitos.",
    "\n"
    # Passo 3: Pastas Comuns
    "📁 **Pastas Comuns para Cheats**:\n   Verifique cuidadosamente: `%appdata%`, `%localappdata%`, `Documentos`. Procure por pastas/arquivos com nomes sugestivos.",
    "\n"
    # Passo 4: Análise Avançada de Processos
    "🛠️ **Análise Avançada (Process Hacker / System Informer)**:\n   Use uma dessas ferramentas para inspecionar *processos a fundo*. Verifique módulos carregados, strings internas e conexões de rede suspeitas.",
    "\n"
    # Passo 5: Navegador e Downloads
    "🌐 **Histórico do Navegador e Downloads**:\n   Cheque o *histórico de navegação* e a pasta de *downloads*. Procure por sites ou arquivos relacionados a cheats/mods.",
    "\n"
    # Passo 6: Lixeira
    "🗑️ **Lixeira**:\n   Examine a lixeira. Arquivos suspeitos podem ter sido deletados recentemente.",
    "\n"
    # Passo 7: Busca por Strings
    "💬 **Busca por Strings Conhecidas**:\n   Utilize ferramentas de busca (como **Everything**) ou o próprio **Process Hacker/System Informer** para procurar *textos específicos* (strings) conhecidos de cheats nos arquivos ou na memória dos processos.",
    "\n"
    # Passo 8: Logs de Jogos/Launchers
    "📜 **Logs Específicos (se aplicável)**:\n   Analise logs do *jogo* ou de *launchers* (Steam, EA App, etc.) que possam conter informações relevantes sobre modificações ou erros.",
    "\n"
    # Passo 9: Overlays (Sobreposições)
    "⚙️ **Overlays / Sobreposições**:\n   Verifique as configurações de overlay de aplicativos como Discord, MSI Afterburner, GeForce Experience, Xbox Game Bar, etc. Veja se há algo incomum ativo.",
    "\n"
    # Passo 10: Conclusão
    "✅ **Conclusão da Análise**:\n   Revise todas as evidências encontradas. Finalize a verificação e comunique seu veredito de forma clara."
]

# --- Validação do ID do Cargo Padrão ---
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

ID_CARGO_MODERADOR = None
if ID_CARGO_MODERADOR_STR:
    try:
        ID_CARGO_MODERADOR = int(ID_CARGO_MODERADOR_STR)
        print(f"ID do Cargo Moderador/Admin carregado: {ID_CARGO_MODERADOR}")
    except ValueError:
        print(f"Aviso: ID_CARGO_MODERADOR '{ID_CARGO_MODERADOR_STR}' no .env não é um número válido. Moderadores não terão acesso automático aos canais de telagem.")
else:
     print("Aviso: Chave 'ID_CARGO_MODERADOR' não encontrada no .env. Apenas o usuário e o bot terão acesso aos canais de telagem.")


# --- Configuração das Intents ---
intents = discord.Intents.default()
intents.members = True          # Necessária para on_member_join
intents.message_content = True  # Necessária para ler comandos (!telagem, !clear)

# --- Inicialização do Bot ---
bot = discord.Client(intents=intents)

class CloseChannelView(View):
    def __init__(self, author_id: int, timeout=3600*6): # <<< MODIFICADO >>> Adicionado timeout de 6 horas por padrão
        super().__init__(timeout=timeout)
        self.author_id = author_id # Armazena o ID do usuário que iniciou

    @discord.ui.button(label="Fechar Canal", style=discord.ButtonStyle.danger, custom_id="close_telagem_channel")
    async def close_button(self, interaction: discord.Interaction, button: Button):
        channel_to_delete = interaction.channel
        user_who_clicked = interaction.user
        guild = interaction.guild

        # <<< MODIFICADO >>> Verificação mais robusta: permite fechar quem iniciou OU quem tem permissão de Gerenciar Canais no servidor
        is_original_author = user_who_clicked.id == self.author_id
        has_manage_channels_perm = user_who_clicked.guild_permissions.manage_channels

        if not (is_original_author or has_manage_channels_perm):
             await interaction.response.send_message("Você não tem permissão para fechar este canal.", ephemeral=True)
             print(f"Usuário {user_who_clicked.name} (não autorizado) tentou fechar o canal {channel_to_delete.name}.")
             return

        # Verifica se o BOT tem permissão para DELETAR este canal
        bot_member = guild.me
        if not channel_to_delete.permissions_for(bot_member).manage_channels:
            print(f"Erro: Bot não tem permissão 'Gerenciar Canais' para deletar {channel_to_delete.name}")
            await interaction.response.send_message("Erro: Não tenho permissão para deletar este canal. Contate um administrador.", ephemeral=True)
            return

        try:
            await interaction.response.defer(ephemeral=True, thinking=False) # Confirma recebimento do clique
            print(f"Tentando deletar canal {channel_to_delete.name} a pedido de {user_who_clicked.name}...")
            await channel_to_delete.delete(reason=f"Telagem concluída e canal fechado por {user_who_clicked.name}")
            print(f"Canal de telagem {channel_to_delete.name} fechado com sucesso.")
        except discord.NotFound:
             print(f"Erro: Canal {channel_to_delete.name} já foi deletado ou não encontrado ao tentar fechar.")
             # Não precisa enviar mensagem ao usuário, o canal já sumiu.
        except discord.Forbidden:
            print(f"Erro de Permissão ao tentar deletar o canal {channel_to_delete.name} por {user_who_clicked.name}.")
            if not interaction.is_done():
                 await interaction.followup.send("Erro Crítico: Falha ao deletar o canal por falta de permissões do BOT.", ephemeral=True)
        except discord.HTTPException as e:
            print(f"Erro HTTP ao tentar deletar o canal {channel_to_delete.name}: {e}")
            if not interaction.is_done():
                await interaction.followup.send("Erro: Falha na comunicação com o Discord ao tentar fechar o canal.", ephemeral=True)
        except Exception as e:
            print(f"Erro inesperado ao tentar deletar o canal {channel_to_delete.name}: {e}")
            if not interaction.is_done():
                await interaction.followup.send("Ocorreu um erro inesperado ao fechar o canal.", ephemeral=True)

# --- Eventos do Bot ---

@bot.event
async def on_ready():
    """Evento chamado quando o bot está conectado e pronto."""
    print(f'Bot conectado como {bot.user.name}#{bot.user.discriminator}')
    print(f'ID do Bot: {bot.user.id}')
    print(f'Pronto para adicionar cargo com ID: {ID_CARGO_PADRAO}')
    print(f'>>> Pronto para criar canais de telagem via comando "{COMANDO_TELAGEM}" no canal "{CANAL_TELAGEM_NOME}" <<<') # <<< MODIFICADO >>>
    print(f'Pronto para limpar mensagens com o comando "{COMANDO_CLEAR}"')
    print('-------')
    # <<< NOVO >>> Registrar a view persistentemente se quiser que os botões funcionem após reiniciar o bot
    # Isso é mais avançado, por enquanto a view será criada a cada comando
    # bot.add_view(CloseChannelView(author_id=0)) # Exemplo - requer ajustes para funcionar corretamente com persistência

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

    if message.author.bot:
        return

    # --- <<< MODIFICADO >>> Lógica do Comando !telagem com Criação de Canal ---
    if message.channel.name == CANAL_TELAGEM_NOME and message.content.lower().startswith(COMANDO_TELAGEM):
        print(f"Comando '{COMANDO_TELAGEM}' detectado de {message.author.name} no canal '{message.channel.name}'")
        member = message.author
        guild = message.guild

        # 1. Verifica permissão do BOT para GERENCIAR CANAIS
        if not guild.me.guild_permissions.manage_channels:
            print(f"Erro Crítico de Permissão: O bot não tem a permissão 'Gerenciar Canais' no servidor '{guild.name}'.")
            try:
                await message.channel.send(f"{member.mention}, não tenho permissão para criar canais neste servidor. Por favor, peça a um administrador para me conceder a permissão **'Gerenciar Canais'**.", delete_after=20)
            except discord.Forbidden:
                print(f"Erro: Bot sem permissão para enviar mensagem de erro no canal {message.channel.name}")
            return

        agora = datetime.datetime.now()
        hora_inicio_formatada = agora.strftime("%H:%M:%S")

        # 2. Define permissões para o novo canal
        overwrites = {
            guild.default_role: PermissionOverwrite(read_messages=False, send_messages=False, view_channel=False), # Nega para @everyone
            member: PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True),             # Permite para o usuário
            guild.me: PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True, manage_channels=True, view_channel=True) # Permite para o bot
        }

        # Opcional: Adiciona permissão para cargo de moderador/admin
        if ID_CARGO_MODERADOR:
            mod_role = guild.get_role(ID_CARGO_MODERADOR)
            if mod_role:
                overwrites[mod_role] = PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True, view_channel=True) # Permite para Mods
                print(f"Cargo de moderador '{mod_role.name}' terá acesso ao canal de telagem.")
            else:
                print(f"Aviso: Cargo de moderador com ID {ID_CARGO_MODERADOR} não encontrado no .env ou no servidor.")

        # 3. Define nome e tenta criar o canal
        # Remove caracteres inválidos para nomes de canal e limita tamanho
        safe_user_name = ''.join(c for c in member.name if c.isalnum() or c in ('-', '_')).lower()
        channel_name = f"telagem-{safe_user_name[:50]}-{member.id % 10000}" # Nome único e mais curto
        # Opcional: Criar dentro de uma categoria específica
        # category = discord.utils.get(guild.categories, name="Telagens")
        # if not category: print("Aviso: Categoria 'Telagens' não encontrada.")

        try:
            # Tenta criar o canal
            # new_channel = await guild.create_text_channel(channel_name, overwrites=overwrites, category=category, reason=f"Canal de telagem para {member.name}") # Com categoria
            new_channel = await guild.create_text_channel(channel_name, overwrites=overwrites, reason=f"Canal de telagem para {member.name}") # Sem categoria
            print(f"Canal privado '{new_channel.name}' (ID: {new_channel.id}) criado para {member.name}.")

            # 4. Avisa no canal original e menciona o novo canal
            try:
                await message.delete() # <<< NOVO >>> Apaga o comando !telagem original
                await message.channel.send(f"Ok, {member.mention}! Criei um canal exclusivo para você: {new_channel.mention}. Siga os passos lá.", delete_after=25) # Mensagem some
            except discord.Forbidden:
                 print(f"Aviso: Não foi possível deletar o comando original ou enviar a confirmação em {message.channel.name}")
            except discord.HTTPException as e:
                 print(f"Aviso: Erro HTTP ao interagir com {message.channel.name}: {e}")


            # 5. Envia os passos no NOVO canal
            await new_channel.send(f"Olá {member.mention}! Iniciando guia de telagem às **{hora_inicio_formatada}**. Siga os passos:")
            await asyncio.sleep(1.0) # Reduzi um pouco o sleep inicial
            for i, passo in enumerate(PASSOS_TELAGEM, 1):
                await new_channel.send(f"**Passo {i}:** {passo}")
                await asyncio.sleep(2.5) # Reduzi um pouco o sleep entre passos

            # 6. Envia a mensagem final com o botão de fechar
            view = CloseChannelView(author_id=member.id)
            await new_channel.send(
                f"Guia concluído. Assim que terminar a SS, clique no botão abaixo para **fechar o canal**.",
                view=view
            )
            print(f"\nGuia de telagem e botão de fechar enviados para {member.name} no canal {new_channel.name}.")

        except discord.Forbidden as e:
            print(f"Erro Crítico de Permissão (on_message - telagem): **O BOT** não tem permissão para 'Criar Canais' ou configurar permissões.")
            print(f"Detalhe do erro: {e}")
            try:
                await message.channel.send(f"{member.mention}, falha ao criar seu canal de telagem. **Verifique se tenho as permissões necessárias (Gerenciar Canais)!**", delete_after=20)
            except discord.Forbidden: pass # Ignora se não puder nem avisar
        except discord.HTTPException as e:
            print(f"Erro de Rede/HTTP (on_message - telagem) ao tentar criar canal ou enviar guia: {e}")
            try:
                await message.channel.send(f"{member.mention}, ocorreu um erro de comunicação com o Discord ao criar seu canal.", delete_after=15)
            except discord.Forbidden: pass
        except Exception as e:
            print(f"Ocorreu um erro inesperado (on_message - telagem): {e}")
            # Tenta deletar o canal se ele chegou a ser criado mas deu erro depois
            if 'new_channel' in locals() and new_channel:
                 try: await new_channel.delete(reason="Erro durante a configuração")
                 except: pass
            try:
                await message.channel.send(f"{member.mention}, ocorreu um erro inesperado ao iniciar a telagem.", delete_after=15)
            except discord.Forbidden: pass


    # --- Lógica do Comando !clear
    elif message.content.lower().startswith(COMANDO_CLEAR):
        print(f"Comando '{COMANDO_CLEAR}' detectado de {message.author.name} no canal '{message.channel.name}'")

        # 1. Verificar permissão do USUÁRIO
        if not message.author.guild_permissions.manage_messages:
            try:
                await message.channel.send(f"{message.author.mention}, você não tem permissão para gerenciar mensagens neste canal.", delete_after=10)
            except discord.Forbidden:
                print(f"Erro: Bot sem permissão de enviar mensagem de erro de permissão no canal {message.channel.name}")
            print(f"Usuário {message.author.name} tentou usar !clear sem permissão.")
            return

        # 2. Extrair a quantidade de mensagens a deletar
        try:
            parts = message.content.split()
            if len(parts) < 2:
                await message.channel.send(f"Uso correto: `{COMANDO_CLEAR} <quantidade>` (ex: `{COMANDO_CLEAR} 10`)", delete_after=10)
                return

            amount_to_delete = int(parts[1])

            if amount_to_delete <= 0:
                 await message.channel.send(f"Por favor, insira um número positivo.", delete_after=10)
                 return

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

        # 3. Deletar as mensagens
        try:
            deleted_messages = await message.channel.purge(limit=amount_to_delete + 1)
            # Opcional: enviar confirmação que some rápido
            # await message.channel.send(f"{len(deleted_messages)-1} mensagens apagadas por {message.author.mention}.", delete_after=5)
            print(f"{len(deleted_messages)-1} mensagens apagadas em '{message.channel.name}' por {message.author.name}.")

        except discord.Forbidden:
            print(f"Erro de Permissão (on_message - clear): **O BOT** não tem permissão 'Gerenciar Mensagens' no canal '{message.channel.name}' ({message.channel.id}).")
            try:
                await message.channel.send(f"Erro: Eu não tenho permissão para apagar mensagens neste canal.", delete_after=10)
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
    except ImportError as e:
        print(f"Erro Crítico: Falha ao importar módulo necessário: {e}")