# given:
# - sites IDs
# - indicator ID
# - campaigns
# - visualization type
# - tableau de référence
# - code indicateur

# étapes
# - préparer le contexte
# - exécuter un code python
# - retourner les infos ?

# indicateur :
# - dummy indicateur (nb d'observations)
# - I02 sans abondance
# - I02 (avec abondance si temps)

def getHE(cd_nom):
    pass

code0 = """
for site in sites:
    nbObs = 0
    for visit in site.visits:
        nbObs += len(visit.observations)
        

"""

code1 = """
observations_he = ???
Produit(observations.abondance, observations_he)
"""
