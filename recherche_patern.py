def derniere_apparition(motif : str) -> dict:
    """_summary_

    Args:
        motif (str): _description_

    Returns:
        dict: _description_
    """
    dico = {}
    for i in range(len(motif)-1,-1,-1):
        if motif [i] not in dico:
            dico[motif[i]] = i
    return dico

def boyer_moore_horspool(texte:str, motif:str)->bool:
    """Recherche un motif dans un texte.
    Algorithmes de Boyer-Moore et Horspool.

    Args:
        texte (str): chaine de caractères dans laquelle chercher "motif"
        motif (str): chaine de caractères à chercher dans "texte"

    Returns:
        bool: oui ou non le motif est présent dans le texte
    """
    if motif =='':
        return False

    occurences = []

    apparitions = derniere_apparition(motif)

    N = len(texte)
    P = len(motif)
    n = 0
    j = P-1

    while n < N-P+1:
        if texte[n+j] == motif[j]:
            j = j-1
            if j == -1:
                occurences.append(n)
                n = n+1
                j = P-1
        else:
            if texte[n+j] not in apparitions:
                n = n+j+1
                j = P-1
            else:
                n = n + max(1, j-apparitions[texte[n+j]])
                j = P-1
    return False if len(occurences)==0 else True