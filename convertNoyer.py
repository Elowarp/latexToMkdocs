'''
 Name : Elowan
 Creation : 24-06-2023 20:53:52
 Last modified : 26-06-2023 15:54:43
'''
from TexSoup import TexSoup, utils, data
import re
import os

from CONST import disponible_environments, skip_envs
from latex2png import pnglatex

# Soup = l'intérieur d'une balise

def frameAnalyse(soup):
    """
    Analyse le contenu d'un frame et le transforme en markdown

    (Prend en compte les frames fragiles et les titres pas dans des 
    frametitle)

    :param soup: le contenu du frame
    :type soup: TexSoup.TexNode
    :return: le contenu du frame en markdown
    """
    # Si la frame est sans paramètres
    if len(soup.args) == 0:
        return transformSoupToMarkdown(list(soup.contents))
    
    # Si la frame est fragile
    if soup.args[0] == '[fragile]':
        string = ''

        # Si la frame a un titre
        if len(soup.args) >= 2:
            string += "\n#### " + removeWeirdSpacing(str(soup.args[1])) \
                    .replace('{', '').replace('}', '') + "\n\n"
            return string + transformSoupToMarkdown(list(soup.contents)[2:])
        
        else:
            return "\n" + transformSoupToMarkdown(list(soup.contents)[1:])
    else:
        # Si la frame a un titre mais pas de mention fragile
        string = "\n#### " + removeWeirdSpacing(str(soup.args[0])).replace('{', '').replace('}', '') + "\n\n"
        return string + transformSoupToMarkdown(list(soup.contents)[1:])
    
def getEnvironment(string):
    """
    Récupère le contenu d'un environnement dans un string

    Trouve le premier '{' et renvoie tout ce qu'il y a dedans 

    :param string: le string à analyser
    :type string: str
    :return: le contenu de l'environnement
    """
    count = None
    ignoreLine = False
    for i in range(len(string)):
        if ignoreLine:
            continue

        if string[i] == '%':
            ignoreLine = True
            continue

        if string[i] == '{':
            if count == None: count = 0
            count += 1
        elif string[i] == '}':
            count -= 1
        if count == 0:
            return string[string.find('{')+1:i]

def getWeirdEnvironment(string):
    """
    Récupère le contenu d'une commande de la forme "\env ... {}" 
    dans un string avec ... les options de la commande

    :param string: le string à analyser
    :type string: str
    :return: (
        la commande, 
        le contenu de l'environnement, 
        la commande complète
    )
    """
    command = ""

    # Récupère la commande latex
    for i in range(len(string)):
        if string[i] == '\\':
            command += string[i:string.find('{')]
            break

    # Récupère le contenu de l'environnement
    envContent = getEnvironment(string[len(command):])
    
    return string[string.find('\\'):len(command)+len(envContent)+3]

def renderImage(name, string):
    """
    Rend une image latex en png

    :param name: le nom de l'image
    :type name: str
    :param string: le contenu de l'image
    :type string: str
    :return: le nom de l'image
    :rtype: str
    """
    print("/!\ Commande impossible à parser : {}".format(
                removeWeirdSpacing(string)))
    print("Conversion en image...\n")
    
    DIR = "images/{}/".format(soup.title.string)

    imageNumber = len([name for name in os.listdir(DIR) if os.path.isfile(os.path.join(DIR, name))])

    # Convertit le latex en image
    try:
        filename = "{}_{}.png".format(name, imageNumber)
        pnglatex(string, DIR + "{}".format(filename), packages=packages)

    except ValueError:
        print("/!\ Erreur lors de la conversion en image\n")
        return "\n!!!danger \"Erreur de convertion : {}\"\n".format(
                removeWeirdSpacing(filename))
    

    else:
        print("Conversion en image réussie\n")
        return "\n\n![{}]({})\n\n".format(name, DIR + "{}".format(filename))

# Fonctions de transformation de balise en markdown
functions_for_envs = {
    # MetaBalises
    "input": lambda x, indent: "\n\n!!!danger \"Include\"\n", # TODO: include the file
    "frame": lambda x, indent: frameAnalyse(x),
    "title": lambda x, indent: "# " + removeWeirdSpacing(str(x.string)) + "\n\n",
    "section": lambda x, indent: "\n## " + removeWeirdSpacing(str(x.string)) + "\n\n",
    "subsection": lambda x, indent: "\n### " + removeWeirdSpacing(str(x.string)) + "\n\n",
    "frametitle": lambda x, indent: "\n\n#### " + removeWeirdSpacing(str(x.string)) + "\n\n",
    "framesubtitle": lambda x, indent: "\n##### " + removeWeirdSpacing(str(x.string)) + "\n\n",

    
    # Blocs à part entière
    "label": lambda x, indent: "", # On dégage les labels
    "tiny": lambda x, indent: str(transformSoupToMarkdown(list(x.contents))),
    "small": lambda x, indent: str(transformSoupToMarkdown(list(x.contents))),
    "ref": lambda x, indent: "[" + removeWeirdSpacing(str(x.string)) + "](#"
                            + str(x.string) + ")",
    "tabular": lambda x, indent: renderImage(str(x.name), str(x)),

    "figure": lambda x, indent: "\n" + renderImage(x.name, str(x)),
    
    "itemize": lambda x, indent: "\n\n" + "\n".join([indent + "- " + str(
                                    transformSoupToMarkdown(list(elmt))
                                    ).rstrip().lstrip() 
                                    for elmt in list(x.children)]) + "\n\n",

    "enumerate": lambda x, indent: "\n\n" + "\n".join([indent + "1. " + str(
                                    transformSoupToMarkdown(list(elmt), indent)
                                    ).rstrip().lstrip()
                                    for elmt in list(x.children)]) + "\n\n",

    "lstlisting": lambda x, indent: "\n```{} linenums=\"1\"\n".format(str(x.contents[0])
                                    .replace("style=", "")) + 
                                    str(x.contents[1]).replace('    ', ' ') + 
                                    "\n```\n",

    "columns": lambda x, indent: str(transformSoupToMarkdown(list(x.contents[2:]), indent)),
    "column": lambda x, indent: str(transformSoupToMarkdown(list(x.contents[1:]), indent)),

    "defn": lambda x, indent: '\n\n!!!quote "Définition"\n' + "     " + 
                                    str(transformSoupToMarkdown(list(x.contents), 
                                    indent + "     ")) + "\n\n",

    "rem": lambda x, indent: '\n\n!!!tip ""\n    **Remarque**\n\n' + "     " +
                                    str(transformSoupToMarkdown(list(x.contents), 
                                    indent + "     ")) + "\n\n",

    "prop": lambda x, indent: '\n\n!!!warning ""\n    **Propriété**\n\n' + "     " +
                                    str(transformSoupToMarkdown(list(x.contents), 
                                    indent + "     ")) + "\n\n",
    "block": lambda x, indent: "\n\n" + str(transformSoupToMarkdown(list(x.contents),
                                    indent)) + "\n\n",
    "cod": lambda x, indent: "\n`" + str(transformSoupToMarkdown(list(x.contents),
                                    indent)) + "`\n",
    

    # Inline elements
    "href": lambda x, indent: "[" + removeWeirdSpacing(str(x.args[1].string)) + 
                                    "](" + str(x.args[0].string) + ")",

    "emph": lambda x, indent: " *" + str(transformSoupToMarkdown(list(x.contents)
                                    )) + "*",
    "enquote": lambda x, indent: "\"" + str(transformSoupToMarkdown(list(x.contents)
                                    )) + "\"",
    "textcolor": lambda x, indent: "<span style='color:{}'>".format(
                                    str(x.args[0].string)
                                    ) + str(transformSoupToMarkdown(
                                        list(x.contents[1:]))
                                    ) + "</span>",

    "displaymath": lambda x, indent: "\n\n$$\n" + " ".join(
                                    [ str(x).rstrip().lstrip() for x in x.contents]
                                    ) + "$$\n\n",
    "BraceGroup": lambda x, indent: str(transformSoupToMarkdown(
                                    list(x.contents), indent)),

    # "alert": lambda x, indent: str(transformSoupToMarkdown(
    #                                 list(TexSoup(getEnvironment(stringSoup[x.position:]), 
    #                                 skip_envs=skip_envs)), indent)),

    "textbf": lambda x, indent: "**" + str(transformSoupToMarkdown(
                                    list(x.contents))
                                    ) + "**",
    
    "gbox": lambda x, indent: " `" + str(transformSoupToMarkdown(
                                    list(x.contents))
                                    ) + "`",
    "textwidth": lambda x, indent: str(transformSoupToMarkdown(
                                    list(x.contents))
                                    ),

    # Abréviations (TODO: à vérifier)
    "node": lambda x, indent: "noeud",
    "ie": lambda x, indent: "ie",
    "ssi": lambda x, indent: "si et seulement si",
    "": lambda x, indent: transformSoupToMarkdown(list(x.contents), indent),
}


def transformSoupToMarkdown(soupList, indent=""):
    """
    Transforme une liste de soup en markdown, si un % est placé au début de la ligne,
    alors la ligne n'est pas gardée. La fonction est récursive.

    :param list: une liste de soup
    :type list: List

    :return: string
    """
    resultString = ''
    toSkip = -1

    # Parcours de la liste de soup
    for i in range(len(soupList)):
        soup = soupList[i]

        if soup.position < toSkip:
            continue

        # Si c'est un commentaire, on passe à la ligne suivante
        if str(soup).startswith('%'):
            continue

        # Si c'est un simple texte ou des maths, on le retourne
        if type(soup) == utils.Token or soup.name == "$":
            resultString += ' ' + removeWeirdSpacing(str(soup))

            if type(soup) != data.TexNode:
                resultString = resultString.rstrip().lstrip()
                
            continue

        # Si on a prévu une fonction pour cette balise, on l'applique
        if soup.name in functions_for_envs:
            resultString += str(functions_for_envs[soup.name](soup, indent))
            continue
        
        # Si la balise n'est pas prise en charge par le script
        # qui se chargera de l'afficher sur le site, on affiche un warning
        if soup.name not in disponible_environments:
            string = getWeirdEnvironment(stringSoup[soup.position-1:])

            # Transforme la balise en image             
            string = renderImage(soup.name, string)

            toSkip = soup.position + len(string) + 1
            
            resultString += string

            # resultString += "\n\n$$\n" + removeWeirdSpacing(str(soup)).rstrip().lstrip() + "\n$$\n\n"
            continue

        # Sinon on applique la fonction sur tous les enfants de la balise
        resultString += transformSoupToMarkdown(list(soup.contents), indent)

        resultString += "\n"
        
    return resultString

def removeWeirdSpacing(string):
    """
    Enlève les espaces/saut à la ligne en trop dans une string

    :param string: la string à modifier
    :type string: string

    :return: string
    """
    # On enlève les sauts à la ligne, les espaces et les % en trop
    reg1 = re.compile(r'\s+')
    reg2 = re.compile(r'[\n\r%]')
    string = re.sub(reg1, ' ', string)
    return re.sub(reg2, '', string)

def includeFiles(soup):
    """
    Include les fichiers .tex dans le fichier principal

    :param soup: le fichier principal
    :type soup: TexSoup

    :return: string
    """
    # Récupère les fichiers à inclure
    inputs = soup.find_all('input')
    for input_soup in inputs:
        # Ouvre le fichier
        try:
            with open(str(input_soup.args[0].string), 'r') as f:
                stringSoup = f.read()

            # Ajoute le contenu du fichier au fichier principal
            input_soup.replace_with(TexSoup(stringSoup, skip_envs=skip_envs))
        
        except FileNotFoundError:
            print("/!\ Impossible d'importer le fichier " + 
                  str(input_soup.args[0].string))
            
    return TexSoup(str(soup), skip_envs=skip_envs)

def getAllImportedPackages(soup):
    """
    Récupère tous les packages importés dans le fichier

    :param soup: le fichier principal
    :type soup: TexSoup

    :return: List
    """
    packages = []
    for package in soup.find_all('usepackage'):
        packages.append(str(package))
    return packages

def removeComments(soup):
    """
    Enlève les commentaires du fichier

    :param soup: le fichier principal
    :type soup: TexSoup

    :return: string
    """
    # Récupère tous les commentaires
    ignoreLine = False
    soupstr = str(soup)
    outstring = ""
    for i in range(len(soupstr)):
        if soupstr[i] == '%':
            ignoreLine = True
            continue

        if soupstr[i] == '\n':
            ignoreLine = False
            
        if not ignoreLine:
            outstring += soupstr[i]

    return TexSoup(outstring)

if __name__ == '__main__':
    # Ouverture du fichier
    with open('graphes (copia).tex', 'r') as f:
        stringSoup = f.read()
        
    soup = TexSoup(stringSoup, skip_envs=skip_envs)
    soup = includeFiles(soup)
    soup = removeComments(soup)

    stringSoup = str(soup)

    # Supprime les images précédentes
    folder = 'images/{}/'.format((soup.title.string).replace(' ', '_'))
    if os.path.exists(folder):
        for file in os.listdir(folder):
            os.remove(folder + file)

    os.makedirs(folder, exist_ok=True)


    # Récupère tous les packages importés
    packages = getAllImportedPackages(soup)

    # Récupération de la partie importante du fichier
    document = soup.find('document')
    documentList = list(document.contents)

    # Transformation en markdown
    outputString = ""

    # Ajout du titre, author et date
    outputString += "# " + removeWeirdSpacing(str(soup.find("title").string)) + "\n\n"
    outputString += "## " + removeWeirdSpacing(str(soup.find("author").string)) + "\n\n"

    outputString += transformSoupToMarkdown(documentList)

    # Supprime les faux espaces utilisés pour l'indentation
    outputString = outputString.replace(' ', '')

    # Ecriture dans le fichier
    with open('output.md', 'w') as f:
        f.write(outputString)

