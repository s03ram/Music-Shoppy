from flask import Flask, render_template, request, g, session
import sqlite3
from datetime import datetime

from recherche_patern import boyer_moore_horspool #petite fonction de recherche textuelle implémentée en cours
from config import Config
from flask_mail import Mail, Message
from random import randint

app = Flask("Mon application")
app.secret_key = "azerty" #on verra plus tard pour la sécurité



##############################################################
##############################################################
#####################/  Base de données  \####################



DATABASE = "database/chinook.db"

def get_db():
    """
    Crée la connexion vers la bdd
    Nécessaire avant chaque requête
    """
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.context_processor
def current_date():
    return {'current': datetime.now()}


@app.teardown_appcontext
def close_connection(exception):
    """
    Ferme la connexion vers la bdd
    """
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def selection(requete, args=(), one=False):
    """
    Exécute une requête auprès de la bdd (après l'avoir créée)
    """
    cur = get_db().execute(requete, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv




####################\  Base de données  /#####################
##############################################################

##############################################################
#######################/  Templates  \########################


# Les sélections des requêtes SQLite seront converties en liste
# pour faciliter l'implémentation de la fonction recherche.

# accueil
@app.route('/')
@app.route('/accueil')
def accueil():
    requete_nbArtists = 'SELECT count(*) FROM artists'
    requete_artistById = """
    SELECT * FROM artists
    WHERE artists.ArtistId = ?
    """
    nbArtistes = selection(requete_nbArtists, one=True)[0]  #nombre total d'artistes de la db pour le randint()
                                                            # en espérant qu'il n'y ait pas de trous dans les artistsId
    artistes = []
    for i in range (6):  #selectionne 6 artistes au hasard pour la section #hightlighted
        artistes.append(selection(requete_artistById, (randint(1,nbArtistes),), one=True))

    # Créé un panier vide s'il y en a pas déjà (répété sur toutes les pages au cas où le visiteur ne passe pas par l'accueil)
    if 'panier' not in session : 
            session['panier'] = []      # ensemble des articles en attente de commande
            session['panierPrice'] = 0  # prix total du panier

    return render_template('index.html', artistes = artistes)

#recherche d'un artiste
@app.route('/recherche')
def recherche():
    cherche = request.args.get('cherche')
    categorie = request.args.get('categorie')

    #modifie la requête en fonction de la catégorie
    if categorie == "Artiste":
        requete ="SELECT *, upper(Name) AS 'Upper' FROM artists"
    if categorie == "Titre":
        requete ="SELECT *, upper(Name) AS 'Upper' FROM tracks"
    else:
        requete ="SELECT *, upper(Title) AS 'Upper' FROM albums"

    select = selection(requete)

    #recherche textuelle avec algo de Boyer-Hoore et Horspool
    resultats = []
    for unit in select:
        if boyer_moore_horspool(unit["Upper"], cherche.upper()):
            resultats.append(unit)
    
    if 'panier' not in session : 
            session['panier'] = []
            session['panierPrice'] = 0

    enTete= str(len(resultats))+' résulats pour "'+cherche+'"'
    # en fonction de la catégorie, renvoyer un template différent
    if categorie == "Artiste":
        return render_template('artistes.html', artistes=resultats, titre = enTete)
    elif categorie == "Titre":
        return render_template("liste_titres.html",
                                titres = resultats,
                                title = enTete)
    else:
        return render_template('liste_albums.html', 
                                albums=resultats,
                                titre = enTete)
                                


#contact
@app.route('/contact')
def contact():
    
    if 'panier' not in session :
            session['panier'] = []
            session['panierPrice'] = 0
 
    return render_template('contact.html')


# artistes
@app.route("/artistes")
def liste_artistes():
    requete = """
    SELECT * FROM artists
    ORDER BY artists.name ASC
    """
    artistes = selection(requete)

    #pour simpifier l'implémentation de la fonction recherche, on renvoie la requête sous forme de liste
    resultats =[artiste for artiste in artistes]

    if 'panier' not in session :
            session['panier'] = []
            session['panierPrice'] = 0
 
    return render_template("artistes.html", artistes=resultats, titre = "Tous les artistes")


# albums de l'artiste sélectionné
@app.route("/liste_albums")
def liste_albums():
    artiste = request.args.get('ArtistId')
    requete_listAlbums = """
    SELECT * FROM albums
    WHERE albums.ArtistId = ?
    """
    requete_artist = """
    SELECT * FROM artists
    WHERE artists.ArtistId = ?
    """
    albums = selection(requete_listAlbums, (artiste,))
    artist = selection(requete_artist, (artiste,), one=True)

    #pour simpifier l'implémentation de la fonction recherche, on renvoie la requête sous forme de liste
    resultats = [album for album in albums]

    if 'panier' not in session :
            session['panier'] = []
            session['panierPrice'] = 0

    return render_template("liste_albums.html",
                           titre="Albums de "+artist[1],
                           albums=resultats)


# liste des titres de l'album sélectionné
@app.route("/liste_titres")
def liste_titres():

    idGet = request.args.get('id')
    parent = request.args.get('parent')

    requete_parentAlbum = """
    SELECT Title FROM albums
    WHERE albums.AlbumId = ?
    """
    requete_parentPlaylist = """
    SELECT Name FROM playlists
    WHERE playlists.PlaylistId = ?
    """
    requete_listTracksFromAlbum = """
    SELECT * FROM tracks
    WHERE tracks.AlbumId = ?
    """
    requete_listTracksFromPlaylist = """
    SELECT * FROM tracks
    INNER JOIN playlist_track ON playlist_track.TrackId = tracks.TrackId
    INNER JOIN playlists ON playlist_track.PlaylistId = playlists.PlaylistId
    WHERE playlists.PlaylistId = ?
    """
    print(idGet)
    if parent == 'album':
        title = selection(requete_parentAlbum, (idGet,), one=True)['Title']
        titres = selection(requete_listTracksFromAlbum, (idGet[0],))
    else:
        title= selection(requete_parentPlaylist, (idGet,), one=True)['Name']
        titres = selection(requete_listTracksFromPlaylist, (idGet,))

    resultats = [titre for titre in titres]

    if 'panier' not in session :
            session['panier'] = []
            session['panierPrice'] = 0
    
    return render_template("liste_titres.html",
                                title = title,
                                titres = resultats)


# playlists
@app.route('/playlists')
def playlists():
    requete_playlists = """
    SELECT * FROM playlists
    """
    requete_nbTitresPlaylists="""
    SELECT count(tracks.TrackId) FROM tracks
    INNER JOIN playlist_track ON playlist_track.TrackId = tracks.TrackId
    INNER JOIN playlists ON playlist_track.PlaylistId = playlists.PlaylistId
    WHERE playlists.PlaylistId = ?
    """
    playlists = selection(requete_playlists)

    resultats = [(playlist,selection(requete_nbTitresPlaylists,(playlist['PlaylistId'],), one=True)) for playlist in playlists]

    if 'panier' not in session :
            session['panier'] = []
            session['panierPrice'] = 0

    return render_template("playlists.html", playlists = resultats)

# récapitulatif de panier
@app.route('/panier', methods = ['post','get'])
def panier():
    # on essaie de récupérer les titres par 'POST'
    try:
        tracks = request.form
    except : # si on y arrive pas (erreur) c'est qu'on est arrivé là sans passer par liste_titres (sans ajouter au panier)
        if 'panier' not in session :
            session['panier'] = []
            session['panierPrice'] = 0
    else: # sinon c'est qu'on veut ajouter au panier
        noms = [nom for nom in tracks]
        prix = [float(tracks[n]) for n in noms]
        session['panierPrice'] += float(sum(prix))
        round(session['panierPrice'],2)
        for nom, prixUnit in zip(noms, prix):
            session['panier'].append((nom, prixUnit))

    
    return render_template("panier.html")

#suppression du panier
@app.route('/vider_panier')
def vider_panier():
    session['panier'] = []
    session['panierPrice'] = 0
    return render_template("panier.html")

# page de redirection vers une page "sécurisée"
@app.route('/paiement', methods = ['post'])
def paiement():
    return render_template("paiement.html")


### envoi d'un mail par le formulaire à mon adresse perso ###

# configuration des attributs
app.config.from_object(Config)
mail = Mail(app)

#envoi de l'email
@app.route('/message_sent', methods = ['POST'])
def envoi_email():
    name    = request.form['name']
    email   = request.form['email']
    message = request.form['message']
    msg =   Message('Formulaire site MusicShoppy',
                    recipients=['louismares03@gmail.com'])
    msg.body = "Bonjour Admin,  Nouveau message de " + str(name) + " :\n" + str(message) + "\nRecontacte-le ici :" + str(email)
    msg.html = "<p>Bonjour Admin,</p> <p>Nouveau message de " + str(name) + " :<br>" + str(message) + "</p><p>Recontacte-le ici : " + str(email)
    mail.send(msg)
    return render_template('mail_sent.html')


# 404
@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'),404



#######################\  Templates  /########################
##############################################################
##############################################################




# Le corps du programme
if __name__ == '__main__':
    # Serveur visible sur ce poste uniquement et modifiable à la volée (mode debug actif)
    app.run(debug=True)
