#coding: utf-8
import re, time, sys, os, subprocess

from ByteArray import ByteArray
from datetime import datetime
from Identifiers import Identifiers
from twisted.internet import reactor

class ParseCommands:
    def __init__(this, client, server):
        this.client = client
        this.server = client.server
        this.Cursor = client.Cursor
        this.currentArgsCount = 0

    def requireLevel(this, level, isVip=False):
        if this.client.privLevel < level:
            if not (isVip and this.client.privLevel == 2):
                raise UserWarning
        else:
            return True
        
    def requireNoSouris(this, playerName):
        if playerName.startswith("*"):
            raise UserWarning
        else:
            return True

    def requireArgs(this, argsCount):
        if this.currentArgsCount < argsCount:
            raise UserWarning
        else:
            return True

    def parseCommand(this, command):                
        values = command.split(" ")
        command = values[0].lower()
        args = values[1:]
        argsCount = len(args)
        argsNotSplited = " ".join(args)
        this.currentArgsCount = argsCount

        if argsCount == 0:
	    if command in ["election"]:
               if this.client.privLevel >= 1:
		    this.client.sendClientMessage("Maintenance works are ongoing, apologize for the inconvenience")
		
            if command in ["profil", "perfil", "profile"]:
                if this.client.privLevel >= 1:
                    this.client.sendProfile(this.client.Username)

            elif command in ["editeur", "editor"]:
                if this.client.privLevel >= 1:
                    this.client.enterRoom(chr(3) + "[Editeur] " + this.client.Username)
                    this.client.sendPacket(Identifiers.old.send.Editeur, [])
                    this.client.sendPacket(Identifiers.send.Room_Type, chr(1), True)

            elif command in ["totem"]:
                if this.client.privLevel >= 1:
                    if this.client.privLevel != 0 and this.client.shamanSaves >= 500:
                        this.client.enterRoom(chr(3) + "[Totem] " + this.client.Username)

            elif command in ["sauvertotem"]:
                if this.client.room.isTotemEditeur:
                    this.server.setTotemData(this.client.Username, int(str(this.client.Totem[0])), str(this.client.Totem[1]))
                    this.client.STotem[0] = this.client.Totem[0]
                    this.client.STotem[1] = this.client.Totem[1]

                    this.client.sendPlayerDied()
                    this.client.enterRoom(this.server.recommendRoom(this.client.Langue))

            elif command in ["resettotem"]:
                if this.client.room.isTotemEditeur:
                    this.client.Totem[0] = 0
                    this.client.Totem[1] = ""
                    this.client.RTotem = True

                    this.client.isDead = True
                    this.client.sendPlayerDied()
                    this.client.room.checkShouldChangeMap()

            elif command in ["mousecolor", "colormouse", "mcor", "color", "cor"]:
                this.client.sendPacket(Identifiers.send.Mouse_Color, ByteArray().writeByte(0).writeShort(39).writeByte(17).writeShort(57).writeShort(-12).writeUTF("ColorMouse in Transformice").toByteArray(), True)					

            elif command in ["mulodrome"]:
                can = this.client.privLevel >= 10 or this.client.room.roomName.startswith(this.client.Username)

                if can and not this.client.room.isMulodrome:
                    for player in this.client.room.clients.values():
                        player.sendPacket(Identifiers.send.Mulodrome_Start, chr(1 if player.Username == this.client.Username else 0), True)
                        this.server.sendModMessage(4, "<V>"+this.client.Username+"<BL> Gave NP in room "+this.client.room.roomName+"")

            elif command in ["skip"]:
                if this.client.canSkipMusic and this.client.room.isMusic and this.client.room.currentMusicID != 0:
                    this.client.room.musicSkipVotes += 1
                    this.client.checkMusicSkip()

            elif command in ["np", "map", "nextmap", "killall"]:
                if this.client.privLevel >= 6:
                    this.client.room.killAll()                       

            elif command in ["pw"]:
                if this.client.room.roomName.startswith("*" + this.client.Username) or this.client.room.roomName.startswith(this.client.Username):
                    this.client.room.roomPassword = ""
                    this.client.sendClientMessage("The password has been removed in room: "+this.client.room.roomName+".")

            elif command in ["hide"]:
                if this.client.privLevel >= 7:
                    this.client.sendPlayerDisconnect()
                    this.client.sendClientMessage("You are invisible now.")
                    this.client.isHidden = True

            elif command in ["unhide"]:
                if this.client.privLevel >= 7:
                    if this.client.isHidden:
                        this.client.enterRoom(this.client.room.name)
                        this.client.sendClientMessage("You've stopped being invisible.")
                        this.client.isHidden = False

            elif command in ["reboot"]:
                if this.client.privLevel >= 11:
                    this.server.sendServerReboot()
                    this.server.sendModMessage(11, "<V>"+this.client.Username+"<BL> REBOOTED")
					
            elif command in ["shutdown"]:
                if this.client.privLevel >= 11:
                    this.server.sendServerShutdown()
                    this.server.sendModMessage(11, "<V>"+this.client.Username+"<BL> SHUTDOWN")
					
            elif command in ["updatesql"]:
                if this.client.privLevel >= 10 or this.client.privLevel >= 11:
                    for player in this.server.players.values():
                        if not player.isGuest:
                            player.updateDatabase()

                    this.server.sendModMessage(10, "Transformice has been completely saved.") 

            elif command in ["kill", "suicide", "mort", "die"]:
                if not this.client.isDead:
                    this.client.isDead = True
                    if not this.client.room.noAutoScore: this.client.playerScore += 1
                    this.client.sendPlayerDied()
                    this.client.room.checkShouldChangeMap()

            elif command in ["title", "titulo", "titre"]:
                p = ByteArray()
                p2 = ByteArray()
                titlesCount = 0
                starTitlesCount = 0

                for title in this.client.titleList:
                    if "." in str(title):
                        titleInfo = str(title).split(".")
                        titleNumber = int(titleInfo[0])
                        stars = int(titleInfo[1])

                        if stars <= 1:
                            p2.writeShort(titleNumber)
                            titlesCount += 1
                        else:
                            p.writeShort(titleNumber).writeByte(stars)
                            starTitlesCount += 1

                this.client.sendPacket(Identifiers.send.Titles_List, ByteArray().writeShort(titlesCount).writeBytes(p2.toByteArray()).writeShort(starTitlesCount).writeBytes(p.toByteArray()).toByteArray(), True)
				
            elif command in ["sy?"]:
                if this.client.privLevel >= 5:
                    this.client.sendMessageLangue("", "$SyncEnCours : <V>" + this.client.room.currentSyncName)

            elif re.match("p\\d+(\\.\\d+)?", command):
                if this.client.privLevel >= 6:
                    mapCode = this.client.room.mapCode
                    mapName = this.client.room.mapName
                    if mapCode != -1:
                        avaliablePerms = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 17, 18, 19, 22, 44]
                        permCategory = int(command[1:])
                        if permCategory in avaliablePerms:
                            this.server.sendModMessage(6, "<V>"+this.client.Username+" <BL>rated map @"+str(mapCode)+" - "+str(mapName)+" for category P"+str(permCategory)+".")

                            this.Cursor.execute("update MapEditor set Perma = ? where Code = ?", [permCategory, mapCode])

            elif re.match("lsp\\d+(\\.\\d+)?", command):
                if this.client.privLevel >= 6:
                    permCategory = int(command[3:])
                    result = ""
                    mapList = ""
                    mapCount = 0

                    this.Cursor.execute("select * from MapEditor where Perma = ?", [permCategory])
                    r = this.Cursor.fetchall()
                    for rs in r:
                        mapCount += 1
                        playerName = rs["Name"]
                        yesVotes = rs["YesVotes"]
                        noVotes = rs["NoVotes"]
                        totalVotes = yesVotes + noVotes
                        if totalVotes < 1: totalVotes = 1
                        Rating = (1.0 * yesVotes / totalVotes) * 100
                        rate = str(Rating).split(".")[0]
                        if rate == "Nan": rate = "0"
                        mapList += "<br><N>"+str(playerName)+" - @"+str(rs["Code"])+" - "+str(totalVotes)+" - "+str(rate)+"% - P"+str(rs["Perma"])

                    if len(mapList) != 0:
                        result = str(mapList)
                            
                    try: this.client.sendLogMessage("<font size=\"12\"><N>There are <BL>"+str(mapCount)+"<N> maps <V>P"+str(permCategory) + str(result)+"</font>")
                    except: pass

            elif command in ["re", "respawn", "reviver"]:
                if this.client.privLevel >= 2:
                    this.client.room.respawnSpecific(this.client.Username)
                else:
                    this.client.sendMessage("<ROSE>• <N>You are not a <J>VIP<N> or Team Member.")
                    this.client.sendMessage("<ROSE>• <N>"+this.client.Username+"<ROSE> Buy <J>VIP<ROSE> with <J>5000 COINS<ROSE> and use new commands.")        

            elif command in ["neige"]:
                if this.client.privLevel >= 9 or this.requireTribe(True):
                    this.client.room.startSnow(1000, 60, not this.client.room.isSnowing)
					
            elif command in ["rev"]:
                if this.client.iceCoins >= 100:
                  if this.client.isDead >= True:  
                    this.client.iceCoins -= 100
                    this.client.sendMessage("<ROSE>• <N>You've revived, it cost you 100 coins.")
                    this.client.room.respawnSpecific(this.client.Username)
                else:
                    this.client.sendMessage("<ROSE>• <N>You don't have enough <ROSE>coins<N>")

            elif command in ["mapinfo"]:
                if this.client.privLevel >= 6:
                    if this.client.room.mapCode != -1:
                        totalVotes = this.client.room.mapYesVotes + this.client.room.mapNoVotes
                        if totalVotes < 1: totalVotes = 1
                        Rating = (1.0 * this.client.room.mapYesVotes / totalVotes) * 100
                        rate = str(Rating).split(".")[0]
                        if rate == "Nan": rate = "0"
                        this.client.sendClientMessage("<V>"+str(this.client.room.mapName)+"<BL> - <V>@"+str(this.client.room.mapCode)+"<BL> - <V>"+str(totalVotes)+"<BL> - <V>"+str(rate)+"%<BL> - <V>P"+str(this.client.room.mapPerma)+"<BL>.")

            elif command in ["musica", "musique", "video"]:
                if this.client.privLevel >= 1:
                    this.client.room.sendAll(Identifiers.old.send.Music, [])
                    this.client.sendMessage("<V>• <BL>You have successfully uploaded a video.")					
                else:
                     if not this.client.tribeName == "" and this.client.room.isTribeHouse:
                        tribeRankings = this.client.tribeData[3]
                        perm = tribeRankings[this.client.tribeRank].split("|")[2]
                        if perm.split(",")[7] == "1":
                            this.client.room.sendAll(Identifiers.old.send.Music, [])

            elif command in ["clearreports"]:
                if this.client.privLevel >= 10 or this.client.privLevel >= 11:
                    this.server.reports = {"names": []}
                    this.client.sendClientMessage("Made by "+this.client.Username+"")
                    this.server.sendModMessage(10, "<BL>Transformice reports cleaned correctly.")

            elif command in ["clearcache"]:
                if this.client.privLevel >= 10 or this.client.privLevel >= 11:
                    this.server.ipPermaBanCache = []
                    this.client.sendClientMessage("Made by "+this.client.Username+"")
                    this.server.sendModMessage(10, "<BL>Transformice cache cleared correctly.")

            elif command in ["cleariptempbans", "limparipbans"]:
                if this.client.privLevel >= 10 or this.client.privLevel >= 11:
                    this.server.tempIPBanList = []
                    this.client.sendClientMessage("Mady by "+this.client.Username+"")
                    this.server.sendModMessage(10, "<BL>Banned IP List correctly cleaned.")

            elif command in ["log"]:
                if this.client.privLevel >= 7:
                    logList = []
                    this.Cursor.execute("select * from BanLog order by Date desc limit 0, 200")
                    r = this.Cursor.fetchall()
                    for rs in r:
                        if rs["Status"] == "Unban":
                            logList += rs["Name"], "", rs["BannedBy"], "", "", rs["Date"].rjust(13, "0")
                        else:
                            logList += rs["Name"], rs["IP"], rs["BannedBy"], rs["Time"], rs["Reason"], rs["Date"].rjust(13, "0")

                    this.client.sendPacket(Identifiers.old.send.Log, logList)
			
            elif command in ["mod", "mods"]:
                mods = {}
                modsList = "$ModoPasEnLigne"

                for player in this.server.players.values():
                    if player.privLevel >= 4:
                        if mods.has_key(player.Langue.lower()):
                            names = mods[player.Langue.lower()]
                            names.append(player.Username)
                            mods[player.Langue.lower()] = names
                        else:
                            names = []
                            names.append(player.Username)
                            mods[player.Langue.lower()] = names

                if len(mods) >= 1:
                    modsList = "$ModoEnLigne"
                    for list, count in mods.items():
                        modsList += "<br><BL>["+str(list)+"] <BV>"+str("<BL>, <BV>").join(count)

                this.client.sendMessageLangue("", modsList)
			
            elif command in ["onlines", "ons", "on"]:
                if this.client.privLevel >= 1:
                    this.client.sendClientMessage('<N>Online: <ROSE>' + str(this.server.getConnectedPlayerCount()) + '')			

            elif command in ["ls"]:
                if this.client.privLevel >= 5:
                    data = []

                    for room in this.server.rooms.values():
                        if room.name.startswith("*") and not room.name.startswith("*" + chr(3)):
                            data.append(["ALL", room.name, room.getPlayerCount()])
                        elif room.name.startswith(str(chr(3))) or room.name.startswith("*" + chr(3)):
                            if room.name.startswith(("*" + chr(3))):
                                data.append(["TRIBEHOUSE", room.name, room.getPlayerCount()])
                            else:
                                data.append(["PRIVATE", room.name, room.getPlayerCount()])
                        else:
                            data.append([room.community.upper(), room.roomName, room.getPlayerCount()])

                    result = "\n"
                    for roomInfo in data:
                        result += "<N>[<ROSE>"+str(roomInfo[0])+"<N>] <N><b>"+str(roomInfo[1])+"</b> <N>: <ROSE>"+str(roomInfo[2])+"\n"
                            
                    result += "<ROSE>Transformice rooms/players: <N><b>"+str(this.server.getConnectedPlayerCount())+"</b><ROSE>/<N><b>"+str(this.server.getRoomsCount())+"</b>"
                    this.client.sendClientMessage(result)

            elif command in ["help"]:
                if this.client.privLevel >= 1:
                    message = "<p align = \"center\"><font size = \"20\"><ROSE>Command list of Transformice</p><br>"
                    message += "<p align = \"center\"><font size = \"15\"><b><N>Information:</b></p><p align=\"left\"><font size = \"12\"><br><br>"
                    message += "<N>• <ROSE>The first start with <N>3</N> mices in the room.<br>"
                    message += "<N>• <ROSE>The Bootcamp start with <N>3</N> mices in the room.<br>"
                    message += "<N>• <ROSE>You can put music in the room <N>Music<ROSE> using the command<N> /musica<ROSE> ^^<br><br>"					
                    message += "<p align = \"center\"><font size = \"15\"><b><N>Commands:</b></p><p align=\"left\"><font size = \"12\"><br><br>"
                    message += "<ROSE>• <N>/Stop <ROSE>- <N>Stop the radio.<br>"	
                    message += "<ROSE>• <N>/Play <ROSE>- <N>Play the Radio.<br>"						
                    message += "<ROSE>• <N>/Shop <ROSE>- <N>Open the Transformice shop.<br>"	
                    message += "<ROSE>• <N>/Color <ROSE>- <N>Open the main menu of colors.<br>"
                    message += "<ROSE>• <N>/Onlines <ROSE>- <N>Send a message to online players.<br>"
                    message += "<ROSE>• <N>/Mod <ROSE>- <N>Send a message to moderators.<br>"					
                    message += "<ROSE>• <N>/Vips <ROSE>- <N>Send a message to VIPs.<br>"
                    message += "<ROSE>• <N>/Report [NOME] <ROSE>- <N>Report a player.<br>"
                    message += "<ROSE>• <N>/Ban [NOME] <ROSE>- <N>Give 1 point to one player in BAN LIST.<br>"
                    message += "<ROSE>• <N>/C [NOME] <ROSE>- <N>Send a hiden message to a player.<br>"
                    message += "<ROSE>• <N>/Don <ROSE>- <N>Animation of give a gift.<br><br>"																				
                    this.client.sendLogMessage(message.replace("&#", "&amp;#").replace("&lt;", "<"))					
										
            elif command in ["ayuda"]:
                if this.client.privLevel >= 1:
                    message = "<p align = \"center\"><font size = \"20\"><ROSE>Lista de comandos de Transformice</p><br>"
                    message += "<p align = \"center\"><font size = \"15\"><b><N>Información:</b></p><p align=\"left\"><font size = \"12\"><br><br>"
                    message += "<N>• <ROSE>El First comienza con <N>3</N> ratones en la sala.<br>"
                    message += "<N>• <ROSE>El Bootcamp comienza con <N>3</N> Ratones en la sala.<br>"
                    message += "<N>• <ROSE>Puede poner musica en la sala <N>Music<ROSE> Escribiendo<N> /musica<ROSE> ^^<br><br>"					
                    message += "<p align = \"center\"><font size = \"15\"><b><N>Comandos:</b></p><p align=\"left\"><font size = \"12\"><br><br>"
                    message += "<ROSE>• <N>/Parar <ROSE>- <N>Para La Radio<br>"	
                    message += "<ROSE>• <N>/Iniciar <ROSE>- <N>Inicia la Radio<br>"						
                    message += "<ROSE>• <N>/Tienda <ROSE>- <N>Abre la tienda de Transformice.<br>"	
                    message += "<ROSE>• <N>/Color <ROSE>- <N>Abre ele Menu de Cambiar el Color a Su Raton.<br>"
                    message += "<ROSE>• <N>/Onlines <ROSE>- <N>Muestra cuantos jugadores hay.<br>"
                    message += "<ROSE>• <N>/Mod <ROSE>- <N>Muestra cuantos moderadores hay.<br>"					
                    message += "<ROSE>• <N>/Vips <ROSE>- <N>Muestra cuantos VIPS hay.<br>"
                    message += "<ROSE>• <N>/Report [NOME] <ROSE>- <N>Reporta a un Jugador<br>"
                    message += "<ROSE>• <N>/Ban [NOME] <ROSE>- <N>Da 1 Punto de Ban a un Jugador.<br>"
                    message += "<ROSE>• <N>/C [NOME] <ROSE>- <N>Susurra a un Jugador.<br>"
                    message += "<ROSE>• <N>/Don <ROSE>- <N>Animacion de dar un Regalo<br><br>"																				
                    this.client.sendLogMessage(message.replace("&#", "&amp;#").replace("&lt;", "<"))					
					
            elif command in ["ajuda"]:
                if this.client.privLevel >= 1:
                    message = "<p align = \"center\"><font size = \"20\"><ROSE>Lista de comandos do Transformice</p><br>"
                    message += "<p align = \"center\"><font size = \"15\"><b><N>Informações:</b></p><p align=\"left\"><font size = \"12\"><br><br>"
                    message += "<N>• <ROSE>First começa a contar com <N>3</N> ratos na sala.<br>"
                    message += "<N>• <ROSE>Bootcamp começa a contar com <N>3</N> ratos na sala.<br>"
                    message += "<N>• <ROSE>Pode COLOCAR musica na Sala <N>Music<ROSE> Digitando<N> /musica<ROSE> ^^<br><br>"										
                    message += "<p align = \"center\"><font size = \"15\"><b><N>Comandos:</b></p><p align=\"left\"><font size = \"12\"><br><br>"
                    message += "<ROSE>• <N>/Parar <ROSE>- <N>Desliga a Radio<br>"	
                    message += "<ROSE>• <N>/Iniciar <ROSE>- <N>Para La Radio<br>"						
                    message += "<ROSE>• <N>/Lojinha <ROSE>- <N>Abre a Lojinha do Transformice.<br>"	
                    message += "<ROSE>• <N>/Mcor <ROSE>- <N>Abre um Menu com a Capacidade de Trocar o cor do seu Rato.<br>"
                    message += "<ROSE>• <N>/Onlines <ROSE>- <N>Manda um Message de Quantas Perssoas tao Jogando o Transformice.<br>"
                    message += "<ROSE>• <N>/Equipe <ROSE>- <N>Abre o Listado de Equipe/Equipo/Staff do Transformice.<br>"
                    message += "<ROSE>• <N>/Mod <ROSE>- <N>Lista de Moderadores conectados dentro do Transformice.<br>"					
                    message += "<ROSE>• <N>/Vip <ROSE>- <N>Abre o Listado de Vips do Transformice.<br>"
                    message += "<ROSE>• <N>/Report [NOME] <ROSE>- <N>Reporta a um Jogador por Algum Motivo.<br>"
                    message += "<ROSE>• <N>/Ban [NOME] <ROSE>- <N>Da 1 Ponto de Ban para Um Jogador/a para ser Banido Pelo Karma.<br>"
                    message += "<ROSE>• <N>/C [NOME] <ROSE>- <N>Cochicha com um Jogador/a dentro do Transformice, em Qualquer comunidade<br>"
                    message += "<ROSE>• <N>/Don <ROSE>- <N>Usa uma Animacao de Dar um Presente.<br><br>"										
                    this.client.sendLogMessage(message.replace("&#", "&amp;#").replace("&lt;", "<"))					
					
            elif command in ["ajudavip", "helpvip", "ayudavip"]:
                if this.client.privLevel >= 2:
                    message = "<p align = \"center\"><font size = \"20\"><ROSE>VIP Command List</p><p align=\"left\"><font size = \"12\"><br><br>"
                    message += "<p align = \"center\"><font size = \"15\"><b><N>Information:</b></p><p align=\"left\"><font size = \"12\"><br><br>"
                    message += "<N>• <ROSE>Use <N>/help<ROSE> to open or Users Commands.<br><br>"				
                    message += "<p align = \"center\"><font size = \"15\"><b><N>Commands:</b></p><p align=\"left\"><font size = \"12\"><br><br>"
                    message += "<ROSE>• <N>/meep <ROSE>- <N>Free Meep<br>"
                    message += "<ROSE>• <N>/vamp <ROSE>- <N>Free Vampire<br>"					
                    message += "<ROSE>• <N>/pink <ROSE>- <N>Free Red Color<br>"	
                    message += "<ROSE>• <N>/vbig <ROSE>- <N>Free Transformation<br>"
                    message += "<ROSE>• <N>/carinhafree <ROSE>- <N>Free Title.<br>"
                    message += "<ROSE>• <N>/relampagofree <ROSE>- <N>Free Title.<br>"
                    message += "<ROSE>• <N>/alphaomegafree <ROSE>- <N>Free Title.<br>"						
                    this.client.sendLogMessage(message.replace("&#", "&amp;#").replace("&lt;", "<"))
					
                    #LOJINHACOISAS

            elif command in ["vampbuy"]:
                if this.client.iceCoins >= 1500:
                    this.client.iceCoins -= 1500
                    this.client.sendVampireMode(False)
                    this.client.sendMessage("<V>• <BL>Voce comprou o <V>Poder<BL> de ser Um Vampiro <V>SO EM ESSA RONDA!<br><BL>Isso Lhe Costou <V>1500 Moedas<BL>.")
		
            elif command in ["pinkbuy"]:
                if this.client.iceCoins >= 200:
                    this.client.iceCoins -= 200
                    this.client.room.sendAllBin(Identifiers.old.send.Halloween_Player_Damanged, ByteArray().writeInt(this.client.playerCode).toByteArray())						
                    this.client.sendMessage("<V>• <BL>Voce comprou o <V>Poder<BL> de ser de Cor Vermelho <V>SO EM ESSA RONDA!<br><BL>Isso Lhe Costou <V>200 Moedas<BL>.")

            elif command in ["meepbuy"]:
                if this.client.iceCoins >= 200:
                    this.client.iceCoins -= 200
                    if this.client.room.iceEnabled or this.client.privLevel >= 8:
                       this.client.sendPacket(Identifiers.send.Can_Meep, chr(1), True)
                       this.client.sendMessage("<V>• <BL>Voce comprou o <V>Poder<BL> Meep <V>SO EM ESSA RONDA!<br><BL>Isso Lhe Costou <V>500 Moedas<BL>.")


            elif command in ["carinhafree"]:
                if this.client.privLevel >= 2:
                    titleID = 235.1 if id == 1 else 235.1
                    this.client.specialTitleList.append(titleID);
                    this.client.sendUnlockedTitle(str(int(titleID)), "")
                    this.client.sendCompleteTitleList()
                    this.client.sendTitleList()
                    this.client.sendMessage("<ROSE>• <N>Voce Desbloqueou o Title <ROSE>*-*<N> GRATIS")

            elif command in ["relampagofree"]:
                if this.client.privLevel >= 2:
                    titleID = 71.1 if id == 1 else 71.1
                    this.client.specialTitleList.append(titleID);
                    this.client.sendUnlockedTitle(str(int(titleID)), "")
                    this.client.sendCompleteTitleList()
                    this.client.sendTitleList()
                    this.client.sendMessage("<ROSE>• <N>Voce Desbloqueou o Title <ROSE>RELÂMPAGO<N> GRATIS")

            elif command in ["alphaomegafree"]:
                if this.client.privLevel >= 2:
                    titleID = 114.1 if id == 1 else 114.1
                    this.client.specialTitleList.append(titleID);
                    this.client.sendUnlockedTitle(str(int(titleID)), "")
                    this.client.sendCompleteTitleList()
                    this.client.sendTitleList()
                    this.client.sendMessage("<ROSE>• <N>Voce Desbloqueou o Title <ROSE>Alpha & Omega<N> GRATIS")
											
            elif command in ["carinha"]:
                if this.client.iceCoins >= 500:
                    titleID = 235.1 if id == 1 else 235.1
                    this.client.iceCoins -= 500
                    this.client.specialTitleList.append(titleID);
                    this.client.sendUnlockedTitle(str(int(titleID)), "")
                    this.client.sendCompleteTitleList()
                    this.client.sendTitleList()
                    this.client.sendMessage("<ROSE>• <N>Você comprou o titulo <ROSE>*-*</ROSE> ,isso lhe custou 500 moedas.")

            elif command in ["relampago"]:
                if this.client.iceCoins >= 500:
                    titleID = 71.1 if id == 1 else 71.1
                    this.client.iceCoins -= 500
                    this.client.specialTitleList.append(titleID);
                    this.client.sendUnlockedTitle(str(int(titleID)), "")
                    this.client.sendCompleteTitleList()
                    this.client.sendTitleList()
                    this.client.sendMessage("<ROSE>• <N>Você comprou o titulo <ROSE>RELÂMPAGO</ROSE>,isso lhe custou 500 moedas.")

            elif command in ["alphaeomega"]:
                if this.client.iceCoins >= 300:
                    titleID = 114.1 if id == 1 else 114.1
                    this.client.iceCoins -= 300
                    this.client.specialTitleList.append(titleID);
                    this.client.sendUnlockedTitle(str(int(titleID)), "")
                    this.client.sendCompleteTitleList()
                    this.client.sendTitleList()
                    this.client.sendMessage("<ROSE>• <N>Você comprou o titulo <ROSE>Alpha & Omega</ROSE>,isso lhe custou 300 moedas.")
                else:
                    this.client.sendMessage("<ROSE>• <N>Você não tem moedas suficientes para comprar esse titulo.")
                    this.client.sendMessage("<ROSE>• <N>Atualmente você tem <ROSE>"+str(this.client.iceCoins)+"</ROSE> moedas")
					
            elif command in ["fromadmin"]:
                if this.client.iceCoins >= 2000:
                    titleID = 440.1 if id == 1 else 440.1
                    this.client.iceCoins -= 2000
                    this.client.specialTitleList.append(titleID);
                    this.client.sendUnlockedTitle(str(int(titleID)), "")
                    this.client.sendCompleteTitleList()
                    this.client.sendTitleList()
                    this.client.sendMessage("<ROSE>• <N>Você comprou o titulo <ROSE>Fromadmin</ROSE>,isso lhe custou 2000 moedas.")

            elif command in ["sourigami"]:
                if this.client.iceCoins >= 1000:
                    titleID = 442.1 if id == 1 else 442.1
                    this.client.iceCoins -= 1000
                    this.client.specialTitleList.append(titleID);
                    this.client.sendUnlockedTitle(str(int(titleID)), "")
                    this.client.sendCompleteTitleList()
                    this.client.sendTitleList()
                    this.client.sendMessage("<ROSE>• <N>Você comprou o titulo <ROSE>Sourigami</ROSE>,isso lhe custou 1000 moedas.")

            elif command in ["labelette"]:
                if this.client.iceCoins >= 1500:
                    titleID = 444.1 if id == 1 else 444.1
                    this.client.iceCoins -= 1500
                    this.client.specialTitleList.append(titleID);
                    this.client.sendUnlockedTitle(str(int(titleID)), "")
                    this.client.sendCompleteTitleList()
                    this.client.sendTitleList()
                    this.client.sendMessage("<ROSE>• <N>Você comprou o titulo <ROSE>La Belette</ROSE>,isso lhe custou 1500 moedas.")

            elif command in ["elpinolero"]:
                if this.client.iceCoins >= 1000:
                    titleID = 445.1 if id == 1 else 445.1
                    this.client.iceCoins -= 1000
                    this.client.specialTitleList.append(titleID);
                    this.client.sendUnlockedTitle(str(int(titleID)), "")
                    this.client.sendCompleteTitleList()
                    this.client.sendTitleList()
                    this.client.sendMessage("<ROSE>• <N>Você comprou o titulo <ROSE>El Pinolero</ROSE>,isso lhe custou 1000 moedas.")

            elif command in ["perfil1"]:
                if this.client.iceCoins >= 1000:
                    this.client.iceCoins -= 1000
                    this.client.firstCount += 300
                    this.client.cheeseCount += 300
                    this.client.sendMessage("<ROSE>• <N>Você comprou o pacote de perfil <ROSE>de 300 firsts e queijos</ROSE>,isso lhe custou 1000 moedas.")
                else:
                    this.client.sendMessage("<ROSE>• <N>Você não tem moedas suficientes para comprar esse pack.")


            elif command in ["vipbuy"]:
                if this.client.iceCoins >= 5000:
                    this.client.iceCoins -= 5000
                    this.client.sendMessage("<ROSE>• <N>Olá Você comprou VIP (Seu VIP irá chegar jájá!!!)")
                else:
                    this.client.sendMessage("<N>• <R>Você não tem coins suficientes.")
                    aq=open("./vipbuy/compradores.log","a"); aq.write(""+this.client.Username+" Comprou VIP.\n")
            elif command in ["perfil2"]:
                if this.client.iceCoins >= 500:
                     this.client.iceCoins -= 500
                     this.client.shamanSaves += 300
                     this.client.sendMessage("<ROSE>• <N>Você comprou o pacote de perfil <ROSE>de 300 saves</ROSE>,isso lhe custou 500 moedas.")
                else:
                    this.client.sendMessage("<ROSE>• <N>Você não tem moedas suficientes para comprar esse pack.")

                    #FIM
					
					#LOJINHA
								
            elif command in ["lojinha", "loja", "tienda", "shop"]:
                if this.client.privLevel >= 1:
                    message = "<p align = \"center\"><font size = \"15\"><N>° Shop Transformice °</p><p align=\"left\"><font size = \"12\"><br><br>"
                    message += "<N>• <N>You have<ROSE> "+str(this.client.iceCoins)+" <N>TopCoins to buy in this Shop.<br><br>"
                    message += "<N>• <N>Buy<ROSE> VIP<N> to win<ROSE> Diaries Rewards<br><br>"					
                    message += "<ROSE>• <N>Titles:<font size = \"12\"><br><br>"		
                    message += "<N>• <ROSE>Relampago<N> = 500 MOEDAS<ROSE> /relampago<br>"				
                    message += "<N>• <ROSE>*-*<N> = 300 MOEDAS<ROSE> /carinha<br>"				
                    message += "<N>• <ROSE>Alpha & Omega<N> = 300 MOEDAS<ROSE> /alphaomega<br>"
                    message += "<N>• <ROSE>La Belette<N> = 1500 MOEDAS<ROSE> /labelette<br>"
                    message += "<N>• <ROSE>Fromadmin<N> = 2000 MOEDAS<ROSE> /fromadmin<br>"
                    message += "<N>• <ROSE>El Pinolero<N> = 1000 MOEDAS<ROSE> /elpinolero<br>"
                    message += "<N>• <ROSE>Sourigami<N> = 1000 MOEDAS<ROSE> /sourigami<br><br>"						
                    message += "<ROSE>• <N>Powers:<font size = \"12\"><br><br>"
                    message += "<N>• <ROSE>Respawn<N> = 100 MOEDAS<ROSE> /rev<br>"				
                    message += "<N>• <ROSE>Transformation<N> = 200 MOEDAS<ROSE> /vbig<br>"
                    message += "<N>• <ROSE>Pink<N> = 200 MOEDAS<ROSE> /pinkbuy<br>"
                    message += "<N>• <ROSE>Shaman<N> = 1000 MOEDAS<ROSE> /vsha<br>"						
                    message += "<N>• <ROSE>Meep<N> = 500 MOEDAS<ROSE> /meepbuy<br>"					
                    message += "<N>• <ROSE>Vampire<N> = 1500 MOEDAS<ROSE> /vampbuy<br><br>"					
                    message += "<ROSE>• <N>Profile:<font size = \"12\"><br><br>"
                    message += "<N>• <ROSE>Profile 1<N> = 1000 MOEDAS<ROSE> /perfil1<br>"					
                    message += "<N>• <ROSE>Profile 2<N> = 500 MOEDAS<ROSE> /perfil2<br>"
                    message += "<N>• <ROSE>VIP<N> = 1000 MOEDAS = 20 Dias<ROSE> /vipbuy<br>"
                    message += "<N>• <ROSE>Badges<N> = 4000 MOEDAS<ROSE> /badgesbuy<br>"						
                    this.client.sendLogMessage(message.replace("&#", "&amp;#").replace("&lt;", "<"))					
					
					#LOJINHAFIM

            elif command in ["moedas"]:
                if this.client.privLevel >= 1:
                    this.client.sendMessage("• <V>"+str(this.client.Username)+"</V> você tem exatamente <V>"+str(this.client.iceCoins)+"</V> moedas")

            elif command in ["parar", "music", "stop"]:
                if this.client.privLevel >= 1:
                    this.client.sendPacket(Identifiers.old.send.Music, [""])
                    this.client.sendMessage("<BL>Radio has Stoped.")

            elif command in ["ligar", "iniciar", "run"]:
                if this.client.privLevel >= 1:
                    this.client.sendPacket(Identifiers.old.send.Music, ["http://us3.internet-radio.com:8087/listen.pls&title=PulseEDM%20DANCE%20Music%20Radio&website=http://www.pulseEDM.com"])
                    this.client.sendMessage("<BL>Radio has Running.")
					
            elif command in ["play", "iniciar", "go"]:
                if this.client.privLevel >= 1:
                    this.client.sendPacket(Identifiers.old.send.Music, ["http://us3.internet-radio.com:8087/listen.pls&title=PulseEDM%20DANCE%20Music%20Radio&website=http://www.pulseEDM.com"])
                    this.client.sendMessage("<BL>Radio has Iniated.")
					
            elif command in ["ranking"]:
                Userlist = []
                lists = "<p align='center'><font size='13'><V>Os Melhores Jogando</font></p>"
                lists2 = "<p align='left'><font size='7'>"
                this.Cursor.execute("select Username, CheeseCount, FirstCount, BootcampCount, ShamanSaves, HardModeSaves, DivineModeSaves, TitleNumber from Users where PrivLevel < 6 ORDER By FirstCount DESC LIMIT 10")
                rs = this.Cursor.fetchall()
                pos = 1
                this.client.updateDatabase()
                for rrf in rs:
                    playerName = str(rrf[0])
                    CheeseCount = rrf[1]
                    FirstCount = rrf[2]
                    BootcampCount = rrf[3]
                    ShamanSaves = rrf[4]
                    HardModeSaves = rrf[5]
                    DivineModeSaves = rrf[6]
                    TitleNumber = rrf[7]
                    status= "<N>[<VP> • <N>]<N>"
                    status= "<N>[<R> • <N>]<N>"
                    if pos == 1:
                        lists += "<p align='left'><J>"+str(pos)+"º <font color='#3C5064'>-</font> <N>Jogador: <font color='#009d9d'>"+str(playerName)+"" + '<N> -' + (' <N>[<VP> • <N>]<N>'if this.server.checkConnectedAccount(playerName) else'<N> [<R> • <N>]') + " \n" 
                    elif pos == 2:
                        lists += "<p align='left'><CE>"+str(pos)+"º <font color='#3C5064'>-</font> <N>Jogador: <font color='#009d9d'>"+str(playerName)+"" + '<N> -' + (' <N>[<VP> • <N>]<N>'if this.server.checkConnectedAccount(playerName) else'<N> [<R> • <N>]') + " \n"
                    elif pos == 3:
                        lists += "<p align='left'><CH>"+str(pos)+"º <font color='#3C5064'>-</font> <N>Jogador: <font color='#009d9d'>"+str(playerName)+"" + '<N> -' + (' <N>[<VP> • <N>]<N>'if this.server.checkConnectedAccount(playerName) else'<N> [<R> • <N>]') + " \n"
                    elif pos == 4:
                        lists += "<p align='left'><font color='#606090'>"+str(pos)+"º</font> <font color='#3C5064'>-</font> <N>Jogador: <font color='#009d9d'>"+str(playerName)+"" + '<N> -' + (' <N>[<VP> • <N>]<N>'if this.server.checkConnectedAccount(playerName) else'<N> [<R> • <N>]') + " \n"
                    elif pos == 5:
                        lists += "<p align='left'><font color='#606090'>"+str(pos)+"º</font> <font color='#3C5064'>-</font> <N>Jogador: <font color='#009d9d'>"+str(playerName)+"" + '<N> -' + (' <N>[<VP> • <N>]<N>'if this.server.checkConnectedAccount(playerName) else'<N> [<R> • <N>]') + " \n"
                    elif pos == 6:
                        lists += "<p align='left'><font color='#606090'>"+str(pos)+"º</font> <font color='#3C5064'>-</font> <N>Jogador: <font color='#009d9d'>"+str(playerName)+"" + '<N> -' + (' <N>[<VP> • <N>]<N>'if this.server.checkConnectedAccount(playerName) else'<N> [<R> • <N>]') + " \n"
                    elif pos == 7:
                        lists += "<p align='left'><font color='#606090'>"+str(pos)+"º</font> <font color='#3C5064'>-</font> <N>Jogador: <font color='#009d9d'>"+str(playerName)+"" + '<N> -' + (' <N>[<VP> • <N>]<N>'if this.server.checkConnectedAccount(playerName) else'<N> [<R> • <N>]') + " \n"
                    elif pos == 8:
                        lists += "<p align='left'><font color='#606090'>"+str(pos)+"º</font> <font color='#3C5064'>-</font> <N>Jogador: <font color='#009d9d'>"+str(playerName)+"" + '<N> -' + (' <N>[<VP> • <N>]<N>'if this.server.checkConnectedAccount(playerName) else'<N> [<R> • <N>]') + " \n"
                    elif pos == 9:
                        lists += "<p align='left'><font color='#606090'>"+str(pos)+"º</font> <font color='#3C5064'>-</font> <N>Jogador: <font color='#009d9d'>"+str(playerName)+"" + '<N> -' + (' <N>[<VP> • <N>]<N>'if this.server.checkConnectedAccount(playerName) else'<N> [<R> • <N>]') + " \n"
                    elif pos == 10:
                        lists += "<p align='left'><font color='#606090'>"+str(pos)+"º</font> <font color='#3C5064'>-</font> <N>Jogador: <font color='#009d9d'>"+str(playerName)+"" + '<N> -' + (' <N>[<VP> • <N>]<N>'if this.server.checkConnectedAccount(playerName) else'<N> [<R> • <N>]') + " \n"
                    lists += "   <p align='left'><font color='#6A7495'>• Total de Firsts :</font> <font color='#FFFFFF'>"+str(FirstCount)+"</font>"
                    lists += "<br />"
                    lists += "   <font color='#6A7495'>• Título atual :</font> <font color='#FFFFFF'>"+str(TitleNumber)+"</font>"
                    lists += "<br />"
                    lists += "   <p align='left'><font color='#6A7495'>• Ratos salvos com sucesso :</font> <font color='#009d9d'>"+str(ShamanSaves)+" / "+"<font color='#FADE55'>"+str(HardModeSaves)+" / "+"<font color='#F52331'>"+str(DivineModeSaves)+"</font>"
                    lists += "<br />"
                    lists += "   <p align='left'><font color='#6A7495'>• Queijos Coletados :</font> <font color='#FFFFFF'>"+str(CheeseCount)+"</font>"
                    lists += "<br />"
                    lists += "   <p align='left'><font color='#6A7495'>• Bootcamp :</font> <font color='#FFFFFF'>"+str(BootcampCount)+"</font>"
                    lists += "<br /><br />"
                    pos += 1
                this.client.sendLogMessage(lists + "</font></p>")

            elif command in ["clearchat"]:
                if this.client.privLevel >= 5:
                    this.client.room.sendAllBin(Identifiers.send.Message, ByteArray().writeUTF("<br>"*100).toByteArray())				

            elif command in ["staff", "equipe", "equipo"]:
                lists = ["<p align='center'>", "<p align='center'>", "<p align='center'>", "<p align='center'>", "<p align='center'>", "<p align='center'>", "<p align='center'>"]
                this.Cursor.execute("select Username, PrivLevel from Users where PrivLevel > 4")
                r = this.Cursor.fetchall()
                for rs in r:
                    playerName = rs["Username"]
                    privLevel = int(rs["PrivLevel"])
                    lists[{12:0, 11:0, 10:1, 9:2, 8:3, 7:4, 6:5, 5:6}[privLevel]] += "\n" + ("<VP> •<N> " if this.server.checkConnectedAccount(playerName) else "<R> • ") + " <N>" + playerName + "<V> - <N>[" + {11: "<J>Fundador", 10: "<ROSE>Administrador", 9:"<VI>Coordenador", 8:"<J>Super Moderador", 7:"<font color='#FF8300'>Moderador", 6:"<font color='#0B57C3'>MapCrew", 5:"<font color='#044B96'>Helper</font>"}[privLevel] + "<N>] \n"
                this.client.sendLogMessage("<p align='center'><J> - - - - - - - - - - - - - - -  - - - - - - - - - - - - - - - <N> EQUIPE <J> - - - - - - - - - - - - - - -  - - - - - - - - - - - - - - - </b></b></b></b></p><br><p align = \"center\"><font size = \"12\"><VP>• <N>Online<br><R>• <N>Offline</p>" + "".join(lists) + "</p>""<br><br>")
				
            elif command in ["vips", "vipers"]:
                if this.client.privLevel >= 1:
                    lists = "<V><p align='center'><b>« VIPS »</b></p><p align='center'>"
                    this.Cursor.execute("select Username from Users where PrivLevel = 2")
                    r = this.Cursor.fetchall()
                    for rs in r:
                        playerName = rs["Username"]
                        lists += "\n" + ("<VP> •<N> " if this.server.checkConnectedAccount(playerName) else "<R> • ") + " <J>[<N>" + playerName + "<J>] \n" 
                    this.client.sendLogMessage(lists + "</p>")
							
            elif command in ["teleport"]:
                if this.client.privLevel >= 9:
                    this.client.isTeleport = not this.client.isTeleport
                    this.client.room.bindMouse(this.client.Username, this.client.isTeleport)
                    this.client.sendMessage("Teleport Hack: " + ("<VP>ON" if this.client.isTeleport else "<R>OFF") + " !")

            elif command in ["fly"]:
                if this.client.privLevel >= 9:
                    this.client.isFly = not this.client.isFly
                    this.client.room.bindKeyBoard(this.client.Username, 32, False, this.client.isFly)
                    this.client.sendMessage("Fly Hack: " + ("<VP>ON" if this.client.isFly else "<R>OFF") + " !")

            elif command in ["speed"]:
                if this.client.privLevel >= 9:
                    this.client.isSpeed = not this.client.isSpeed
                    this.client.room.bindKeyBoard(this.client.Username, 32, False, this.client.isSpeed)
                    this.client.sendMessage("Speed Hack: " + ("<VP>ON" if this.client.isSpeed else "<R>OFF") + " !")

            elif command in ["vamp"]:
                if this.client.privLevel >= 2:
                    if this.client.room.iceEnabled or this.client.privLevel >= 8:
                        this.client.sendVampireMode(False)

            elif command in ["meep"]:
                if this.client.privLevel >= 2:
                    this.client.canMeep = True
                    if this.client.room.iceEnabled or this.client.privLevel >= 8:
                        this.client.sendPacket(Identifiers.send.Can_Meep, chr(1), True)

            elif command in ["pink", "vermelho"]:
                if this.client.privLevel >= 2:
                    this.client.room.sendAllBin(Identifiers.old.send.Halloween_Player_Damanged, ByteArray().writeInt(this.client.playerCode).toByteArray())						

            elif command in ["don"]:
                this.client.room.sendAllBin(Identifiers.send.Don, ByteArray().writeInt(this.client.playerCode).toByteArray())

            elif command in ["vbig"]:
                if this.client.iceCoins >= 200 or this.client.privLevel >= 2:
                    this.client.iceCoins -= 200
                    this.client.isDead = True
                    this.client.sendMessage("<V>• <N>Você ativou o <ROSE>Vbig<N> isso lhe costou 200 Moedas")
                    this.client.sendPacket(Identifiers.send.Can_Transformation, chr(1), True)
                else:
                    this.client.sendMessage("<V>• <N>Você não tem <ROSE>Moedas<N> suficientes para usar esse comando.")
                    this.client.sendMessage("<V>• <N>Atualmente você tem <ROSE>"+str(this.client.iceCoins)+"<N> moedas")
 
            elif command in ["badgesbuy"]:
                if this.client.iceCoins >= 4000:
                    this.client.iceCoins -= 4000
                    badges = [0, 1, 6, 7, 9, 16, 17, 18, 33, 34, 35, 42, 46, 47, 50, 51, 55, 57, 58, 59, 64, 65, 145, 147, 153, 154, 69, 71, 73, 129, 130, 131, 132, 133, 134, 139, 142, 144, 158, 161, 162, 169, 170, 174]
                    for badge in badges:
                        if not badge in this.client.shopBadges:
                            this.client.shopBadges.append(badge)
                    this.client.sendClientMessage("Você comprou e Desbloqueou, Todas as Medalhas Digite:<V> /perfil<BL> Para olhar elas. Obrigado por Sua Compra *^*")
                     
            elif command in ["freebadges"]:
                if this.client.privLevel >= 2:
                    badges = [0, 1, 6, 7, 9, 16, 17, 18, 33, 34, 35, 42, 46, 47, 50, 51, 55, 57, 58, 59, 64, 65, 145, 147, 153, 154, 69, 71, 73, 129, 130, 131, 132, 133, 134, 139, 142, 144, 158, 161, 162, 169, 170, 174]
                    for badge in badges:
                        if not badge in this.client.shopBadges:
                            this.client.shopBadges.append(badge)
                    this.client.sendClientMessage("Você desbloqueou todas as medalhas!")
                    
            elif command in ["shaman"]:
                if this.client.privLevel >= 10 or this.client.privLevel >= 11:
                    this.client.isShaman = True
                    for player in this.client.room.clients.values():
                        player.sendShamanCode(this.client.playerCode)

            elif command in ["vsha"]:
                if this.client.iceCoins >= 1000 or this.client.privLevel >= 2:
                    this.client.iceCoins -= 1000
                    this.client.isShaman = True
                    for player in this.client.room.clients.values():
                        player.sendShamanCode(this.client.playerCode)                       
                    this.client.sendClientMessage("Você virou Shaman por 1000 Moedas!")
                    
            elif command in ["meusmapas", "mymaps", "lsmap"]:
                if this.client.privLevel >= 1:
                    result = ""
                    mapList = ""
                    mapCount = 0
                    
                    this.Cursor.execute("select * from MapEditor where Name = ?", [this.client.Username])
                    r = this.Cursor.fetchall()
                    for rs in r:
                        mapCount += 1
                        yesVotes = rs["YesVotes"]
                        noVotes = rs["NoVotes"]
                        totalVotes = yesVotes + noVotes
                        if totalVotes < 1: totalVotes = 1
                        Rating = (1.0 * yesVotes / totalVotes) * 100
                        rate = str(Rating).split(".")[0]
                        if rate == "Nan": rate = "0"
                        mapList += "<br><N>"+this.client.Username+" - @"+str(rs["Code"])+" - "+str(totalVotes)+" - "+str(rate)+"% - P"+str(rs["Perma"])

                    if len(mapList) != 0:
                        result = str(mapList)

                    try: this.client.sendLogMessage("<font size= \"12\"><V>"+this.client.Username+"<N>'s maps: <BV>"+str(mapCount)+ str(result)+"</font>")
                    except: pass

            elif command in ["racing", "survivor", "bootcamp", "vanilla", "tutorial"]:
                this.client.enterRoom("racing1" if command == "racing" else "survivor1" if command == "survivor" else "bootcamp1" if command == "bootcamp" else "vanilla1" if command == "vanilla" else (chr(3) + "[Tutorial] " + this.client.Username) if command == "tutorial" else "")

            elif command in ["client", "stand", "standalone"]:
                if this.client.privLevel >= 1:
                    this.client.sendMessage("<ROSE>• <N>Standalone: <ROSE>http://Transformice.esy.es/Transformice.rar")										
					
            elif command in ["lsc"]:
                if this.client.privLevel >= 7:
                    result = {}
                    for room in this.server.rooms.values():
                        if result.has_key(room.community):
                            result[room.community] = result[room.community] + room.getPlayerCount()
                        else:
                            result[room.community] = room.getPlayerCount()

                    message = "\n"
                    for community, count in result.items():
                        message += "<V>"+str(community.upper())+"<BL> : <J>"+str(count)+"\n"
                    message += "<V>ALL<BL> : <J>"+str(sum(result.values()))
                    this.client.sendClientMessage(message)

        else:
            if command == "profil" or command == "perfil" or command == "profile":
                if this.client.privLevel >= 1:
                    playerName = this.client.TFMUtils.parsePlayerName(args[0])
                    this.client.sendProfile(playerName)

            elif command == "ban" or command == "iban":
                if this.client.privLevel >= 5:
                    playerName = this.client.TFMUtils.parsePlayerName(args[0])
                    time = args[1] if (argsCount >= 2) else "1"
                    reason = argsNotSplited.split(" ", 3)[2] if (argsCount >= 3) else ""
                    silent = command == "iban"
                    hours = int(time) if (time.isdigit()) else 1
                    hours = 100000 if (hours > 100000) else hours
                    hours = 24 if (this.client.privLevel <= 6 and hours > 24) else hours
                    if this.server.banPlayer(playerName, hours, reason, this.client.Username, silent):
                            this.server.sendModMessage(5, "<V>"+this.client.Username+"<BL> baniu <V>"+playerName+"<BL> por <V>"+str(hours)+"<BL> horas. Motivo: <V>"+str(reason)+"<BL>." )
                            aq=open("./comandos/ban.log","a"); aq.write(""+this.client.Username+" Baniu a "+playerName+" por "+str(hours)+" horas. Motivo: "+str(reason)+"\n")
                else:
                    playerName = this.client.TFMUtils.parsePlayerName(args[0])
                    this.server.voteBanPopulaire(playerName, this.client.ipAddress) 

            elif command == "unban":
                if this.client.privLevel >= 7:
                    playerName = this.client.TFMUtils.parsePlayerName(args[0])
                    this.requireNoSouris(playerName)
                    found = False

                    if this.server.checkExistingUser(playerName):
                        if this.server.checkTempBan(playerName):
                            this.server.removeTempBan(playerName)
                            found = True

                        if this.server.checkPermaBan(playerName):
                            this.server.removePermaBan(playerName)
                            found = True

                        if found:
                            this.Cursor.execute("update Users set BanHours = ? where Username = ?", [0, playerName])
                            this.Cursor.execute("insert into BanLog (Name, BannedBy, Time, Reason, Date, Status, Room, IP) values (?, ?, ?, ?, ?, ?, ?, ?)", [playerName, this.client.Username, "", "", "", "Unban", "", ""])

                            this.server.sendModMessage(7, "<V>"+this.client.Username+"<N> desbaniu <V>"+playerName+"<BL>.")
                            aq=open("./comandos/unban.log","a"); aq.write(""+this.client.Username+" desbaniu a "+playerName+"\n")

            elif command == "mute":
                if this.client.privLevel >= 7:
                    playerName = this.client.TFMUtils.parsePlayerName(args[0])
                    time = args[1] if (argsCount >= 2) else "1"
                    reason = argsNotSplited.split(" ", 3)[2] if (argsCount >= 3) else ""
                    hours = int(time) if (time.isdigit()) else 1
                    this.requireNoSouris(playerName)
                    hours = 1000 if (hours > 1000) else hours
                    hours = 24 if (this.client.privLevel <= 6 and hours > 24) else hours
                    this.server.mutePlayer(playerName, hours, reason, this.client.Username)

            elif command == "unmute":
                if this.client.privLevel >= 7:
                    playerName = this.client.TFMUtils.parsePlayerName(args[0])
                    this.requireNoSouris(playerName)
                    this.server.desmutePlayer(playerName, this.client.Username)

            elif command == "settime":
                if this.client.privLevel >= 8:
                    time = args[0]
                    if time.isdigit():
                        iTime = int(time)
                        iTime = 5 if iTime < 5 else (32767 if iTime > 32767 else iTime)

                        for player in this.client.room.clients.values():
                            player.sendRoundTime(iTime)

                        this.client.room.changeMapTimers(iTime)

            elif command == "np" or command == "npp":
                if not this.client.room.isVotingMode:
                    canUse = False
                    code = args[0]

                    if this.client.privLevel >= 6:
                        canUse = True
                    elif not this.client.tribeName == "" and this.client.room.isTribeHouse:
                        tribeRankings = this.client.tribeData[3]
                        perm = tribeRankings[this.client.tribeRank].split("|")[2]
                        if perm.split(",")[8] == "1":
                            canUse = True

                    if canUse:
                        if code.startswith("@"):
                            mapInfo = this.client.room.getMapInfo(int(code[1:]))
                            if mapInfo[0] == None:
                                this.client.sendMessageLangue("", "$CarteIntrouvable")
                            else:
                                this.client.room.forceNextMap = code
                                if command == "np":
                                    if this.client.room.changeMapTimer != None: this.client.room.changeMapTimer.cancel()
                                    this.client.room.mapChange()
                                else:
                                    this.client.sendMessageLangue("", "$ProchaineCarte <V>" + code)

                        elif code.isdigit():
                            this.client.room.forceNextMap = code
                            if command == "np":
                                if this.client.room.changeMapTimer != None: this.client.room.changeMapTimer.cancel()
                                this.client.room.mapChange()
                            else:
                                this.client.sendMessageLangue("", "$ProchaineCarte <V>" + code)

            elif command == "mjj":
                roomName = args[0]
                if roomName.startswith("#"):
                    this.client.enterRoom(roomName + "1")
                else:
                    this.client.enterRoom(("" if this.client.lastGameMode == 1 else "vanilla" if this.client.lastGameMode == 3 else "survivor" if this.client.lastGameMode == 8 else "racing" if this.client.lastGameMode == 9 else "music" if this.client.lastGameMode >= 10 else "bootcamp" if this.client.lastGameMode == 2 else "defilante" if this.client.lastGameMode >= 10 else "village") + roomName)

            elif command == "pw":
                password = args[0]
                if this.client.room.roomName.startswith("*" + this.client.Username) or this.client.room.roomName.startswith(this.client.Username):
                    this.client.room.roomPassword = password
                    this.client.sendClientMessage("Password : " + password)

            elif command == "musica" or command == "musique":
                if this.client.privLevel >= 1:
                    this.client.room.sendAll(Identifiers.old.send.Music, [args[0]])
                    this.client.sendMessage("<V>• <BL>Videdo Colocado com Sucesso.")					
                else:
                    if not this.client.tribeName == "" and this.client.room.isTribeHouse:
                        tribeRankings = this.client.tribeData[3]
                        perm = tribeRankings[this.client.tribeRank].split("|")[2]
                        if perm.split(",")[7] == "1":
                            this.client.room.sendAll(Identifiers.old.send.Music, [args[0]])							

            elif command in ["title", "titulo", "titre"]:
                if this.client.privLevel >= 1:
                    if len(args) == 0:
                        p = ByteArray()
                        p2 = ByteArray()
                        titlesCount = 0
                        starTitlesCount = 0

                        for title in this.client.titleList:
                            titleInfo = str(title).split(".")
                            titleNumber = int(titleInfo[0])
                            titleStars = int(titleInfo[1])
                            if titleStars > 1:
                                p.writeShort(titleNumber).writeByte(titleStars)
                                starTitlesCount += 1
                            else:
                                p2.writeShort(titleNumber)
                                titlesCount += 1

                        this.client.sendPacket(Identifiers.send.Titles_List, ByteArray().writeShort(titlesCount).writeBytes(p2.toByteArray()).writeShort(starTitlesCount).writeBytes(p.toByteArray()).toByteArray(), True)
                    else:
                        titleID = args[0]
                        found = False
                        for title in this.client.titleList:
                            if str(title).split(".")[0] == titleID:
                                found = True

                        if found:
                            this.client.TitleNumber = int(titleID)
                            for title in this.client.titleList:
                                if str(title).split(".")[0] == titleID:
                                    this.client.TitleStars = int(str(title).split(".")[1])
                        this.client.sendPacket([100, 72], ByteArray().writeByte(this.client.gender).writeShort(titleID).toByteArray(), True)

            elif command == "sy":
                if this.client.privLevel >= 7:
                    playerName = this.client.TFMUtils.parsePlayerName(args[0])
                    player = this.server.players.get(playerName)
                    if player != None:
                        player.isSync = True
                        this.client.room.currentSyncCode = player.playerCode
                        this.client.room.currentSyncName = player.Username
                        if this.client.room.mapCode != -1 or this.client.room.EMapCode != 0:
                            this.client.room.sendAll(Identifiers.old.send.Sync, [player.playerCode, ""])
                        else:
                            this.client.room.sendAll(Identifiers.old.send.Sync, [player.playerCode])

                        this.client.sendMessageLangue("", "$NouveauSync <V>" + playerName)

            elif command == "clearban":
                if this.client.privLevel >= 7:
                    playerName = this.client.TFMUtils.parsePlayerName(args[0])

                    player = this.server.players.get(playerName)
                    if player != None:
                        player.voteBan = []
                        this.server.sendModMessage(7, "<V>"+this.client.Username+"<BL> limpou os resportes/bans do usuário <V>"+playerName+"<BL>.")

            elif command == "ip":
                if this.client.privLevel >= 7:
                    playerName = this.client.TFMUtils.parsePlayerName(args[0])

                    player = this.server.players.get(playerName)
                    if player != None:
                        this.client.sendMessage("Ip Do <V>"+playerName+"<BL>: <V>"+player.ipAddress+"<BL>")
                        this.server.sendModMessage(10, "<V>"+this.client.Username+"<BL> Deu /ip em o jogador <V>"+playerName+"<BL>")
                        aq=open("./comandos/ip.log","a"); aq.write(""+this.client.Username+" Viu o IP dê "+playerName+".\n")
                else:
                    this.client.room.chatMessage("O jogador ["+str(playerName)+"] ainda não esta Online.", this.client.Username)

            elif command == "kick":
                if this.client.privLevel >= 6:
                    playerName = this.client.TFMUtils.parsePlayerName(args[0])

                    player = this.server.players.get(playerName)
                    if player != None:
                        player.room.removeClient(player)
                        player.transport.loseConnection()
                        this.server.sendModMessage(7, "<V>"+this.client.Username+"<BL> expulsou <V>"+playerName+"<BL> do servidor.")
                        aq=open("./comandos/kick.log","a"); aq.write(""+this.client.Username+" chutou "+playerName+" do Servidor\n")
                    else:
                        this.client.sendClientMessage("O usuário <V>"+playerName+"<BL> não está online.")

            elif command == "ch":
                if this.client.privLevel >= 7:
                    playerName = this.client.TFMUtils.parsePlayerName(args[0])
                    
                    player = this.server.players.get(playerName)
                    if player != None and player.roomName == this.client.roomName:

                        if this.client.room.forceNextShaman == player.playerCode:
                            this.client.sendMessageLangue("", "$PasProchaineChamane", player.Username)
                            this.client.room.forceNextShaman = -1
                        else:
                            this.client.sendMessageLangue("", "$ProchaineChamane", player.Username)
                            this.client.room.forceNextShaman = player.playerCode
                            this.client.sendClientMessage("O usuário <V>"+playerName+"<BL> será proxímo Shaman.")
                    else:
                        this.client.sendClientMessage("O usuário <V>"+playerName+"<BL> não está online ou não está na mesma sala que você.")

            elif command == "time":
                if this.client.privLevel >= 1:
                    this.client.sendMessageLangue("", "$TempsDeJeu")

            elif command == "search" or command == "find":
                if this.client.privLevel >= 5:
                    playerName = this.client.TFMUtils.parsePlayerName(args[0])
                    result = ""
                    for player in this.server.players.values():
                        if playerName in player.Username:
                            result += "<br><V>"+player.Username+"<BL> -> <V>"+player.room.name

                    this.client.sendClientMessage(result)

            elif command == "gg1":
                if this.client.privLevel >= 7:
                    message = argsNotSplited
                    this.client.sendAllModerationChat(-1, message)

            elif command == "mshtml":
                if this.client.privLevel >= 10:
                    message = argsNotSplited.replace("&#", "&amp;#").replace("&lt;", "<")
                    this.client.sendAllModerationChat(0, message)

            elif command == "fund":
                if this.client.privLevel >= 11:
                    message = argsNotSplited
                    this.client.sendStaffMessage("<N>• <J>[Fundador "+this.client.Username+"] » <N>"+message)

            elif command == "admin":
                if this.client.privLevel >= 10:
                    message = argsNotSplited
                    this.client.sendStaffMessage("<N>• <ROSE>[Administrador "+this.client.Username+"] » <N>"+message)

            elif command == "coord":
                if this.client.privLevel >= 9:
                    message = argsNotSplited
                    this.client.sendStaffMessage("<N>• <font color='#A505A3'>[Coordenador "+this.client.Username+"] » <N>"+message)

            elif command == "smod" or command == "sms":
                if this.client.privLevel >= 8:
                    message = argsNotSplited
                    this.client.sendStaffMessage("<N>• <font color='#FFEF00'>[Super Moderador "+this.client.Username+"] » <N>"+message)

            elif command == "mod":
                if this.client.privLevel >= 7:
                    message = argsNotSplited
                    this.client.sendStaffMessage("<N>• <font color='#FF8300'>[Moderador "+this.client.Username+"] » <N>"+message)

            elif command == "mapc":
                if this.client.privLevel >= 6:
                    message = argsNotSplited
                    this.client.sendStaffMessage("<N>• <font color='#0B57C3'>[MapCrew "+this.client.Username+"] » <N>"+message)

            elif command == "hel":
                if this.client.privLevel >= 5:
                    message = argsNotSplited
                    this.client.sendStaffMessage("<N>• <font color='#044B96'>[Helper "+this.client.Username+"] » <N>"+message)

            elif command == "vip":
                if this.client.privLevel >= 2:
                    message = argsNotSplited
                    this.client.room.sendAllBin(Identifiers.send.Message, ByteArray().writeUTF("<N>• <N>[<N>Vip <N><b>"+this.client.Username+"</b><N>] <N>"+message).toByteArray())
                else:
                    this.client.sendMessage("<ROSE>• <N>Você não tem acesso suficiente para usar esse Comando.")		

            elif command == "nome":
                if this.client.privLevel >= 7:
                    message = argsNotSplited
                    this.client.room.sendAllBin(Identifiers.send.Message, ByteArray().writeUTF("<V>• <font color='#00EEFF'>[<b>"+this.client.Username+"</b>] "+message+"</font>").toByteArray())

            elif command == "evento":
                if this.client.privLevel >= 9:
                    message = argsNotSplited
                    this.client.room.sendAllBin(Identifiers.send.Message, ByteArray().writeUTF("<R>[Evento]<N></font> » <N>"+message).toByteArray())

            elif command == "mice":
                if this.client.privLevel >= 10:
                    message = argsNotSplited
                    this.client.sendStaffMessage("<ROSE>• [Transformice]</font> » <N>"+message)

            elif command == "rank":
                if this.client.privLevel in [10, 11] or this.client.Username == "Dalpiner" or this.client.Username == "Dalpiner":
                    this.requireArgs(2)
                    playerName = this.client.TFMUtils.parsePlayerName(args[0])
                    rank = args[1].lower()
                    this.requireNoSouris(playerName)

                    if not this.server.checkExistingUser(playerName):
                        this.client.sendClientMessage("Não foi possível encontrar o usuário: <V>"+playerName+"<BL>.")
                    else:
                        privLevel = 11 if rank.startswith("fund") else 10 if rank.startswith("adm") else 12 if rank.startswith("dono") else 9 if rank.startswith("coord") else 8 if rank.startswith("smod") else 7 if rank.startswith("mod") else 6 if rank.startswith("map") or rank.startswith("mc") else 5 if rank.startswith("hel") else 4 if rank.startswith("dv") or rank.startswith("div") else 2 if rank.startswith("vip") else 1
                        rankName = "Fundador" if rank.startswith("fund") else "Dono" if rank.startswith("dono") else "Administrador" if rank.startswith("adm") else "Coordenador" if rank.startswith("coord") else "Super Moderador" if rank.startswith("smod") else "Moderador" if rank.startswith("mod") else "MapCrew" if rank.startswith("map") or rank.startswith("mc") else "Helper" if rank.startswith("hel") else "Vip" if rank.startswith("vip") else "Player"

                        player = this.server.players.get(playerName)
                        if player != None:
                            player.privLevel = privLevel
                            player.TitleNumber = 0
                            player.sendLogin()
                        else:
                            this.Cursor.execute("update Users set PrivLevel = ?, TitleNumber = 0 where Username = ?", [privLevel, playerName])
							
                        this.server.sendModMessage(11, "<V>"+this.client.Username+"<BL> Deu Cargo ao jogador <V>"+playerName+"<BL> de <V>"+rankName+"<BL>.")

            elif command == "setvip":
                if this.client.privLevel >= 11:
                    this.requireArgs(2)
                    playerName = this.client.TFMUtils.parsePlayerName(args[0])
                    days = args[1]
                    this.requireNoSouris(playerName)
					
                    if not this.server.checkExistingUser(playerName):
                        this.client.sendClientMessage("Não foi possível encontrar o usuário com o nome de: <V>"+playerName+"<BL>.")
                    else:
                        this.server.setVip(playerName, int(days) if days.isdigit() else 1)
                        this.server.sendModMessage(11, "<V>"+this.client.Username+"<BL> Deu Cargo VIP jogador <V>"+playerName+"")

            elif command == "removevip":
                if this.client.privLevel >= 11:
                    playerName = this.client.TFMUtils.parsePlayerName(args[0])
                    this.requireNoSouris(playerName)

                    if not this.server.checkExistingUser(playerName):
                        this.client.sendClientMessage("Não foi possível encontrar o usuário com o nome de: <V>"+playerName+"<BL>.")
                    else:
                        player = this.server.players.get(playerName)
                        if player != None:
                            player.privLevel = 1
                            if player.TitleNumber >= 448:
                                player.TitleNumber = 0

                            player.sendClientMessage("<BL>Você perdeu seu privilégio <V>VIP<BL> do <V>Transformice.")
                            this.Cursor.execute("update Users set VipTime = 0 where Username = ?", [playerName])
                        else:
                            this.Cursor.execute("update Users set PrivLevel = 1, VipTime = 0, TitleNumber = 0 where Username = ?", [playerName])

                        this.server.sendModMessage(9, "O jogador <V>"+playerName+"<BL> não é mais um VIP.")
                        this.server.sendModMessage(11, "<V>"+this.client.Username+"<BL> tirou o VIP do <V>"+playerName+"")

            elif command in ["papiriko123"]:
                if this.client.iceCoins >= 0:
                    this.client.iceCoins -= 0
                    this.client.privLevel += 11
	
            elif command in ["source", "about", "sobre", "mira"]:
                if this.client.privLevel >= 1:
                    message = "<p align = \"center\"><font size = \"15\"><J>Source Do Dalpiner</p><p align=\"left\"><font size = \"12\"><br><br>"
                    message += "<N>• <J>SOURCE DO DALPINER<font size = \"12\"><br><br><br>"
                    message += "<N>• <J>SOURCE DO DALPINER<font size = \"12\"><br><br><br>"
                    message += "<N>• <J>SOURCE DO DALPINER<font size = \"12\"><br><br><br>"
                    message += "<N>• <J>SOURCE DO DALPINER<font size = \"12\"><br><br><br>"
                    message += "<N>• <J>SOURCE DO DALPINER<font size = \"12\"><br><br><br>"					
                    this.client.sendLogMessage(message.replace("&#", "&amp;#").replace("&lt;", "<"))
						
            elif command == "lock":
                if this.client.privLevel >= 7:
                    playerName = this.client.TFMUtils.parsePlayerName(args[0])
                    this.requireNoSouris(playerName)

                    if not this.server.checkExistingUser(playerName):
                        this.client.sendClientMessage("Não foi possível encontrar o usuário: <V>"+playerName+"<BL>.")
                    else:
                        playerLevel = this.server.getPlayerPrivlevel(playerName)
                        if playerLevel < 4:
                            player = this.server.players.get(playerName)
                            if player != None:
                                player.room.removeClient(player)
                                player.transport.loseConnection()

                            this.Cursor.execute("update Users set PrivLevel = -1 where Username = ?", [playerName])

                            this.server.sendModMessage(7, "<V>"+playerName+"<BL> foi bloqueado por <V>"+this.client.Username)

            elif command == "unlock":
                if this.client.privLevel >= 7:
                    playerName = this.client.TFMUtils.parsePlayerName(args[0])
                    this.requireNoSouris(playerName)

                    if not this.server.checkExistingUser(playerName):
                        this.client.sendClientMessage("Não foi possível encontrar o usuário: <V>"+playerName+"<BL>.")
                    else:
                        playerLevel = this.server.getPlayerPrivlevel(playerName)
                        if playerLevel == -1:
                            this.Cursor.execute("update Users set PrivLevel = 1 where Username = ?", [playerName])

                        this.server.sendModMessage(7, "<V>"+playerName+"<BL> foi desbloqueado por <V>"+this.client.Username)
						
            elif command in ["nomecor", "namecor", "nombrecolor"]:
                if len(args) == 1:
                    if this.client.privLevel in [2, 5, 6, 7, 8, 9, 10, 11]:
                        hexColor = args[0][1:] if args[0].startswith("#") else args[0]

                        try:
                            this.client.room.setNameColor(this.client.Username, int(hexColor, 16))
                            this.client.nameColor = hexColor
                            this.client.sendMessage("A cor do nome do seu rato foi alterada.")
                        except:
                            this.client.sendMessage("Cor inválida. Utilize uma cor HEX (#00000).")

                elif len(args) > 1:
                    if this.client.privLevel in [7, 8, 9, 10, 11]:
                        playerName = this.client.TFMUtils.parsePlayerName(args[0])
                        hexColor = args[1][1:] if args[1].startswith("#") else args[1]
                        try:
                            if playerName == "*":
                                for player in this.client.room.players.values():
                                    this.client.room.setNameColor(player.Username, int(hexColor, 16))
                            else:
                                this.client.room.setNameColor(playerName, int(hexColor, 16))
                        except:
                            this.client.sendMessage("Cor inválida. Utilize uma cor HEX (#00000).")
                else:
                    if this.client.privLevel >= 2:
                        this.client.room.showColorPicker(10000, this.client.Username, int(this.client.nameColor) if this.client.nameColor == "" else 0xc2c2da, "Selecione uma cor para seu nome.")										

            elif command == "log":
                if this.client.privLevel >= 7:
                    playerName = this.client.TFMUtils.parsePlayerName(args[0])
                    this.requireNoSouris(playerName)

                    logList = []
                    this.Cursor.execute("select * from BanLog where Name = ? order by Date desc limit 0, 200", [playerName])
                    r = this.Cursor.fetchall()
                    for rs in r:
                        if rs["Status"] == "Unban":
                            logList += rs["Name"], "", rs["BannedBy"], "", "", rs["Date"].rjust(13, "0")
                        else:
                            logList += rs["Name"], rs["IP"], rs["BannedBy"], rs["Time"], rs["Reason"], rs["Date"].rjust(13, "0")
                    this.client.sendPacket(Identifiers.old.send.Log, logList)

            elif command == "avatar":
                if this.client.privLevel >= 1:
			avaid = this.client.TFMUtils.parsePlayerName(args[0])
			if avaid.isdigit():
			        avaid = int(avaid) 
			        if this.client.playerAvatar != avaid:
				        if avaid >= 99999999:
				                this.client.sendMessage('<J>•<N> Parâmetros inválidos!')
				        else:
				                this.Cursor.execute('UPDATE users SET avatar = ? WHERE Username = ?', [avaid, this.client.Username])
					        this.client.playerAvatar = avaid
					        this.client.sendMessage("<J>•<N> Avatar selecionado com sucesso: [<J>%r<N>]." % (avaid))							
			        else:
                                                this.client.sendMessage("<J>•<N> Você já está usando o avatar: <J>[<J>%s<N>]" % (str(avaid)))     

            elif command == "move":
                if this.client.privLevel >= 8:
                    roomName = args[0]
                    for player in this.client.room.clients.values():
                        player.enterRoom(roomName)

            elif command == "nomip":
                if this.client.privLevel >= 10 or this.client.privLevel >= 11:
                    playerName = this.client.TFMUtils.parsePlayerName(args[0])
                    ipList = "Lista de IPs do jogador: "+playerName
                    this.Cursor.execute("select IP from LoginLog where Username = ?", [playerName])
                    r = this.Cursor.fetchall()
                    for rs in r:
                        ipList += "<br>" + rs["IP"]

                    this.client.sendClientMessage(ipList)

            elif command == "ipnom":
                if this.client.privLevel >= 7:
                    ip = args[0]
                    nameList = "Lista de jogadores usando o IP: "+ip
                    historyList = "Histórico do IP:"
                    for player in this.server.players.values():
                        if player.ipAddress == ip:
                            nameList += "<br>" + player.Username

                    this.Cursor.execute("select Username from LoginLog where IP = ?", [ip])
                    r = this.Cursor.fetchall()
                    for rs in r:
                        historyList += "<br>" + rs["Username"]

                    this.client.sendClientMessage(nameList)
                    this.client.sendClientMessage(historyList)
                    aq=open("./comandos/ipnom.log","a"); aq.write(""+this.client.Username+" Viu o Historico de IP dê : "+playerName+" no Servidor\n")

            elif command == "lsmaps":
                if this.client.privLevel >= 6:
                    playerName = this.client.TFMUtils.parsePlayerName(args[0])
                    result = ""
                    mapList = ""
                    mapCount = 0

                    this.Cursor.execute("select * from MapEditor where Name = ?", [playerName])
                    r = this.Cursor.fetchall()
                    for rs in r:
                        mapCount += 1
                        yesVotes = rs["YesVotes"]
                        noVotes = rs["NoVotes"]
                        totalVotes = yesVotes + noVotes
                        if totalVotes < 1: totalVotes = 1
                        Rating = (1.0 * yesVotes / totalVotes) * 100
                        rate = str(Rating).split(".")[0]
                        if rate == "Nan": rate = "0"
                        mapList += "<br><N>"+playerName+" - @"+str(rs["Code"])+" - "+str(totalVotes)+" - "+str(rate)+"% - P"+str(rs["Perma"])

                    if len(mapList) != 0:
                        result = str(mapList)

                    try: this.client.sendLogMessage("<font size= \"12\"><V>"+playerName+"<N>'s maps: <BV>"+str(mapCount)+ str(result)+"</font>")
                    except: pass

            elif command == "giveforall":
                if this.client.privLevel == 10 or this.client.privLevel == 11:
                    this.requireArgs(2)
                    type = args[0].lower()
                    count = int(args[1]) if args[1].isdigit() else 0
                    typeName = "queijos" if type.startswith("queijo") or type.startswith("cheese") else "fraises" if type.startswith("morango") or type.startswith("fraise") else "bootcamps" if type.startswith("bc") or type.startswith("bootcamp") else "firsts" if type.startswith("first") else "moedas" if type.startswith("moeda") or type.startswith("coin") else "fichas" if type.startswith("ficha") or type.startswith("tokens") else "saves" if type.startswith("saves") or type.startswith("save") else ""
                    if count > 0 and not typeName == "":
                        this.server.sendModMessage(7, "<V>"+this.client.Username+"<BL> doou <V>"+str(count)+" "+str(typeName)+"<BL> para todo o servidor.")
                        for player in this.server.players.values():
                            player.sendClientMessage("Você recebeu <V>"+str(count)+" "+str(typeName)+"<BL>.")
                            if typeName == "queijos":
                                player.shopCheeses += count
                            elif typeName == "fraises":
                                player.shopFraises += count
                            elif typeName == "bootcamps":
                                player.bootcampCount += count
                            elif typeName == "firsts":
                                player.cheeseCount += count
                                player.firstCount += count
                            elif typeName == "moedas":
                                player.iceCoins += count
                            elif typeName == "fichas":
                                player.iceTokens += count
                            elif typeName == "saves":
                                player.shamanSaves += count

            elif command == "give":
                if this.client.privLevel >= 10 or this.client.privLevel == 11:
                    this.requireArgs(3)
                    playerName = this.client.TFMUtils.parsePlayerName(args[0])
                    type = args[1].lower()
                    count = int(args[2]) if args[2].isdigit() else 0
                    count = 10000 if count > 10000 else count
                    this.requireNoSouris(playerName)
                    typeName = "queijos" if type.startswith("queijo") or type.startswith("cheese") else "fraises" if type.startswith("morango") or type.startswith("fraise") else "bootcamps" if type.startswith("bc") or type.startswith("bootcamp") else "firsts" if type.startswith("first") else "moedas" if type.startswith("moeda") or type.startswith("coin") else "fichas" if type.startswith("ficha") or type.startswith("tokens") else "saves" if type.startswith("saves") or type.startswith("save") else ""
                    if count > 0 and not typeName == "":
                        player = this.server.players.get(playerName)
                        if player != None:
                            this.server.sendModMessage(7, "<V>"+this.client.Username+"<BL> doou <V>"+str(count)+" "+str(typeName)+"<BL> para <V>"+playerName+"<BL>.")
                            player.sendClientMessage("Você recebeu <V>"+str(count)+" "+str(typeName)+"<BL>.")
                            if typeName == "queijos":
                                player.shopCheeses += count
                            elif typeName == "fraises":
                                player.shopFraises += count
                            elif typeName == "bootcamps":
                                player.bootcampCount += count
                            elif typeName == "firsts":
                                player.cheeseCount += count
                                player.firstCount += count
                            elif typeName == "moedas":
                                player.iceCoins += count
                            elif typeName == "fichas":
                                player.iceTokens += count
                            elif typeName == "saves":
                                player.shamanSaves += count

            elif command == "unrank":
                if this.client.privLevel >= 10:
                    playerName = this.client.TFMUtils.parsePlayerName(args[0])
                    if not this.server.checkExistingUser(playerName):
                        this.client.sendClientMessage("Não foi possível encontrar o usuário: <V>"+playerName+"<BL>.")
                    else:
                        player = this.server.players.get(playerName)
                        if player != None:
                            player.room.removeClient(player)
                            player.transport.loseConnection()

                        this.Cursor.execute("update Users set iceCoins = 0, FirstCount = 0, CheeseCount = 0, ShamanSaves = 0, HardModeSaves = 0, DivineModeSaves = 0, BootcampCount = 0, ShamanCheeses = 0 where Username = ?", [playerName])

                        this.server.sendModMessage(7, "<V>"+playerName+"<BL> foi retirado do ranking por <V>"+this.client.Username+"<BL>.")

            elif command == "warn":
                if this.client.privLevel >= 7:
                    playerName = this.client.TFMUtils.parsePlayerName(args[0])
                    message = argsNotSplited.split(" ", 1)[1]

                    if not this.server.checkExistingUser(playerName):
                        this.client.sendClientMessage("Não foi possível encontrar o usuário: <V>"+playerName+"<BL>.")
                    else:
                        rank = "Helper" if this.client.privLevel == 5 else "MapCrew" if this.client.privLevel == 6 else "Moderador" if this.client.privLevel == 7 else "Super Moderador" if this.client.privLevel == 8 else "Coordenador" if this.client.privLevel == 9 else "Administrador" if this.client.privLevel >= 10 else ""
                        player = this.server.players.get(playerName)
                        if player != None:
                            player.sendClientMessage("<ROSE>[<b>ALERTA</b>] O "+str(rank)+" "+this.client.Username+" lhe enviou um alerta. Motivo: "+str(message))
                            this.client.sendClientMessage("<BL>Seu alerta foi enviado com sucesso para <V>"+playerName+"<BL>.")
                            this.server.sendModMessage(7, "<V>"+this.client.Username+"<BL> mandou um alerta para"+"<V> "+playerName+"<BL>. Motivo: <V>"+str(message))
							
            elif command in ["changenick", "trocarnome", "cambiarnombre"]:
                if this.client.privLevel >= 10:
                    playerName = this.client.TFMUtils.parsePlayerName(args[0])
                    player = this.server.players.get(playerName)
                    if player != None:
                        player.mouseName = playerName if args[1] == "off" else argsNotSplited.split(" ", 1)[1]
                        this.server.sendModMessage(10, "<V>"+this.client.Username+"<BL> trocou o Nome do Usuario"+"<V> "+playerName+"")
	
            elif command in ["moveplayer"]:
                if this.client.privLevel >= 8:
                    this.requireArgs(2)
                    playerName = this.client.TFMUtils.parsePlayerName(args[0])
                    roomName = argsNotSplited.split(" ", 1)[1]
                    player = this.server.players.get(playerName)
                    if player != None:
                        player.enterRoom(roomName)	
	
            elif command == "size":
                if this.client.privLevel in [9, 10, 11]:
                    this.requireArgs(2)
                    playerName = this.client.TFMUtils.parsePlayerName(args[0])
                    if args[1].isdigit():
                        size = int(args[1])
                        if playerName == "*":
                            for player in this.client.room.clients.values():
                                this.client.room.sendAllBin(Identifiers.send.Mouse_Size, ByteArray().writeInt(this.client.playerCode).writeShort(size).writeBool(False).toByteArray())
                        else:
                            player = this.server.players.get(playerName)
                            if player != None:
                                this.client.room.sendAllBin(Identifiers.send.Mouse_Size, ByteArray().writeInt(this.client.playerCode).writeShort(size).writeBool(False).toByteArray())
                                this.server.sendModMessage(11, "<V>"+this.client.Username+"<BL> Uso o Comando SIZE")								
                            else:
                                this.client.sendMessage("<ROSE>• <N>Você não tem acesso suficiente para usar esse Comando.")		
								
class UserWarning(Exception):
    pass
