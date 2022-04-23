from crypt import methods
from multiprocessing import AuthenticationError
from flask import Flask, render_template, request, g, session
import sqlite3
from datetime import datetime
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




# accueil
@app.route('/')
@app.route('/accueil')
def accueil():
    requete_nbArtists = 'SELECT count(*) FROM artists'
    requete_artistById = """
    SELECT * FROM artists
    WHERE artists.ArtistId = ?
    """
    nbArtistes = selection(requete_nbArtists, one=True)[0]
    artistes = []
    for i in range (6):
        artistes.append(selection(requete_artistById, (randint(1,nbArtistes),), one=True))
    print(artistes[0]['Name'])
    if 'panier' not in session :
            session['panier'] = []
            session['panierPrice'] = 0

    return render_template('index.html', artistes = artistes)


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
    
    if 'panier' not in session :
            session['panier'] = []
            session['panierPrice'] = 0
 
    return render_template("artistes.html", artistes=artistes)


# albums de l'artiste sélectionné
@app.route("/liste_albums")
def liste_albums():
    # à améliorer -> simplifiable niveau requêtes
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

    if 'panier' not in session :
            session['panier'] = []
            session['panierPrice'] = 0

    return render_template("liste_albums.html",
                           artist=artist,
                           albums=albums,)


# liste des titres de l'album sélectionné
@app.route("/liste_titres")
def liste_titres():
    idAlbum = request.args.get('AlbumId')
    requete_album = """
    SELECT Title FROM albums
    WHERE albums.AlbumId = ?
    """
    requete_listTitles = """
    SELECT * FROM tracks
    WHERE tracks.AlbumId = ?
    """
    album = selection(requete_album, (idAlbum,), one=True)
    titres = selection(requete_listTitles, (idAlbum,))

    if 'panier' not in session :
            session['panier'] = []
            session['panierPrice'] = 0

    return render_template("liste_titres.html",
                            album = album,
                            titres = titres)


# récapitulatif de panier
@app.route('/panier', methods = ['post','get'])
def panier():
    try:
        tracks = request.form
    except :
        if 'panier' not in session :
            session['panier'] = []
            session['panierPrice'] = 0
    else:
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
