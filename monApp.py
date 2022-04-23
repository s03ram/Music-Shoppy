from crypt import methods
from multiprocessing import AuthenticationError
from flask import Flask, appcontext_pushed, render_template, request, g
import sqlite3
from datetime import datetime
from config import Config
from flask_mail import Mail, Message

app = Flask("Mon application")




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




# accueil
@app.route('/')
@app.route('/accueil')
def accueil():
    return render_template('index.html')


#contact
@app.route('/contact')
def contact():
    return render_template('contact.html')


# artistes
@app.route("/artistes")
def liste_artistes():
    requete = """
    SELECT * FROM artists
    ORDER BY artists.name ASC
    """
    artistes = selection(requete)
    return render_template("artistes.html", artistes=artistes)


# albums de l'artiste sélectionné
@app.route("/liste_albums")
def liste_albums():
    # à améliorer -> simplifiable niveau requêtes
    idArtist = request.args.get('ArtistId')
    requete_listAlbums = """
    SELECT * FROM albums
    WHERE albums.ArtistId = ?
    """
    albums = selection(requete_listAlbums, (idArtist,))
    requete_artist = """
    SELECT * FROM artists
    WHERE artists.ArtistId = ?
    """
    artist = selection(requete_artist, (idArtist,), one=True)
    requete_UnitPrice = """
    SELECT tracks.AlbumId, tracks.UnitPrice FROM tracks
    INNER JOIN albums ON tracks.AlbumId = albums.AlbumId
    INNER JOIN artists ON albums.ArtistId = artists.ArtistId
    WHERE artists.ArtistId = ?
    """
    unitPrice = selection(requete_UnitPrice, (idArtist,))
    prix_albums = []
    no_album = 1
    current_album = unitPrice[0][0]
    sum_prix = 0
    for i in range(len(unitPrice)-1):
        if unitPrice[i][0] == current_album:
            sum_prix += unitPrice[i][1]
        else:
            prix_albums.append((no_album, round(sum_prix,2)))
            current_album = unitPrice[i][0]
            sum_prix = 0
            no_album += 1
    prix_albums.append((no_album, sum_prix))
    return render_template("liste_albums.html",
                           artist=artist,
                           albums=albums,
                           prix_albums=prix_albums
                           )


# liste des titres de l'album sélectionné
@app.route("/liste_titres")
def liste_titres():
    idAlbum = request.args.get('AlbumId')
    requete_album = """
    SELECT Title FROM albums
    WHERE albums.AlbumId = ?
    """
    album = selection(requete_album, (idAlbum,), one=True)
    requete_listTitles = """
    SELECT * FROM tracks
    WHERE tracks.AlbumId = ?
    """
    titres = selection(requete_listTitles, (idAlbum,))
    return render_template("liste_titres.html",
                            album = album,
                            titres = titres)


# récapitulatif de commande
@app.route('/commande', methods = ['post'])
def recap_commande():
    titres = request.form
    print(titres)
    requete_track = """
    SELECT Name, unitPrice FROM tracks
    WHERE tracks.trackId = ?
    """
    return render_template("commande.html")


# page de redirection vers une page "sécurisée"
@app.route('/achat', methods = ['post'])
def achat():
    return render_template("achat.html")


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
