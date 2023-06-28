#!/usr/bin/env python3
'''
 Name : Elowan
 Creation : 24-06-2023 20:53:52
 Last modified : 28-06-2023 16:44:30
'''
from .TexSoup import TexSoup, utils, data
import re
import os

from .CONST import disponible_environments, skip_envs
from .latex2png import pnglatex

# Soup = l'intérieur d'une balise

class Converter:
    """
    Classe de conversion d'un fichier latex en markdown
    """

    def __init__(self, filename):
        """
        Initialise le convertisseur

        :param filename: le nom du fichier à convertir
        :type filename: str
        """
        self.filename = filename.split("/")[-1]
        self.sourcedir = "/".join(filename.split("/")[:-1]) + "/"
        self.workingdir = os.getcwd() + "/"
        self.imgdir = self.workingdir + "images/{}/".format(
            filename.split("/")[-1].split('.')[0].replace(' ', '_'))
        self.stringSoup = ""
        self.packages = []

    def frameAnalyse(self, soup):
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
            return self.transformSoupToMarkdown(list(soup.contents))
        
        # Si la frame est fragile
        if soup.args[0] == '[fragile]':
            string = ''

            # Si la frame a un titre
            if len(soup.args) >= 2:
                string += "\n#### " + Converter.removeWeirdSpacing(str(soup.args[1])) \
                        .replace('{', '').replace('}', '') + "\n\n"
                return string + self.transformSoupToMarkdown(list(soup.contents)[2:])
            
            else:
                return "\n" + self.transformSoupToMarkdown(list(soup.contents)[1:])
        else:
            # Si la frame a un titre mais pas de mention fragile
            string = "\n#### " + Converter.removeWeirdSpacing(str(soup.args[0])).replace('{', '').replace('}', '') + "\n\n"
            return string + self.transformSoupToMarkdown(list(soup.contents)[1:])
        
    @staticmethod
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

    @staticmethod
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
        envContent = Converter.getEnvironment(string[len(command):])
        
        return string[string.find('\\'):len(command)+len(envContent)+3]

    def renderImage(self, name, string):
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
                    Converter.removeWeirdSpacing(string)))
        print("Conversion en image...\n")
        
        imageNumber = len([name for name in os.listdir(self.imgdir) if os.path.isfile(os.path.join(self.imgdir, name))])

        # Convertit le latex en image
        try:
            filename = "{}_{}.png".format(name, imageNumber)
            pnglatex(string, self.imgdir + "{}".format(filename), packages=self.packages)

        except ValueError:
            print("/!\ Erreur lors de la conversion en image\n")
            return "\n!!!danger \"Erreur de convertion : {}\"\n".format(
                    Converter.removeWeirdSpacing(filename))
        

        else:
            print("Conversion en image réussie\n")
            return "\n\n![{}]({})\n\n".format(name, self.imgdir + "{}".format(filename))

    # Fonctions de transformation de balise en markdown
    def get_functions_for_envs(self, fun):
        functions_for_envs = {
            # MetaBalises
            "input": lambda x, indent: "\n\n!!!danger \"Include\"\n", # TODO: include the file
            "frame": lambda x, indent: self.frameAnalyse(x),
            "title": lambda x, indent: "# " + Converter.removeWeirdSpacing(str(x.string)) + "\n\n",
            "section": lambda x, indent: "\n## " + Converter.removeWeirdSpacing(str(x.string)) + "\n\n",
            "subsection": lambda x, indent: "\n### " + Converter.removeWeirdSpacing(str(x.string)) + "\n\n",
            "frametitle": lambda x, indent: "\n\n#### " + Converter.removeWeirdSpacing(str(x.string)) + "\n\n",
            "framesubtitle": lambda x, indent: "\n##### " + Converter.removeWeirdSpacing(str(x.string)) + "\n\n",

            
            # Blocs à part entière
            "label": lambda x, indent: "", # On dégage les labels
            "tiny": lambda x, indent: str(self.transformSoupToMarkdown(list(x.contents))),
            "small": lambda x, indent: str(self.transformSoupToMarkdown(list(x.contents))),
            "ref": lambda x, indent: "[" + Converter.removeWeirdSpacing(str(x.string)) + "](#"
                                    + str(x.string) + ")",
            "tabular": lambda x, indent: self.renderImage(str(x.name), str(x)),

            "figure": lambda x, indent: "\n" + self.renderImage(x.name, str(x)),
            
            "itemize": lambda x, indent: "\n\n" + "\n".join([indent + "- " + str(
                                            self.transformSoupToMarkdown(list(elmt))
                                            ).rstrip().lstrip() 
                                            for elmt in list(x.children)]) + "\n\n",

            "enumerate": lambda x, indent: "\n\n" + "\n".join([indent + "1. " + str(
                                            self.transformSoupToMarkdown(list(elmt), indent)
                                            ).rstrip().lstrip()
                                            for elmt in list(x.children)]) + "\n\n",

            "lstlisting": lambda x, indent: "\n```{} linenums=\"1\"\n".format(str(x.contents[0])
                                            .replace("style=", "")) + 
                                            str(x.contents[1]).replace('    ', ' ') + 
                                            "\n```\n",

            "columns": lambda x, indent: str(self.transformSoupToMarkdown(list(x.contents[2:]), indent)),
            "column": lambda x, indent: str(self.transformSoupToMarkdown(list(x.contents[1:]), indent)),

            "defn": lambda x, indent: '\n\n!!!quote "Définition"\n' + "     " + 
                                            str(self.transformSoupToMarkdown(list(x.contents), 
                                            indent + "     ")) + "\n\n",

            "rem": lambda x, indent: '\n\n!!!tip ""\n    **Remarque**\n\n' + "     " +
                                            str(self.transformSoupToMarkdown(list(x.contents), 
                                            indent + "     ")) + "\n\n",

            "prop": lambda x, indent: '\n\n!!!warning ""\n    **Propriété**\n\n' + "     " +
                                            str(self.transformSoupToMarkdown(list(x.contents), 
                                            indent + "     ")) + "\n\n",
            "block": lambda x, indent: "\n\n" + str(self.transformSoupToMarkdown(list(x.contents),
                                            indent)) + "\n\n",
            "cod": lambda x, indent: "\n`" + str(self.transformSoupToMarkdown(list(x.contents),
                                            indent)) + "`\n",
            

            # Inline elements
            "href": lambda x, indent: "[" + Converter.removeWeirdSpacing(str(x.args[1].string)) + 
                                            "](" + str(x.args[0].string) + ")",

            "emph": lambda x, indent: " *" + str(self.transformSoupToMarkdown(list(x.contents)
                                            )) + "*",
            "enquote": lambda x, indent: "\"" + str(self.transformSoupToMarkdown(list(x.contents)
                                            )) + "\"",
            "textcolor": lambda x, indent: "<span style='color:{}'>".format(
                                            str(x.args[0].string)
                                            ) + str(self.transformSoupToMarkdown(
                                                list(x.contents[1:]))
                                            ) + "</span>",

            "displaymath": lambda x, indent: "\n\n$$\n" + " ".join(
                                            [ str(x).rstrip().lstrip() for x in x.contents]
                                            ) + "$$\n\n",
            "BraceGroup": lambda x, indent: str(self.transformSoupToMarkdown(
                                            list(x.contents), indent)),

            # "alert": lambda x, indent: str(self.transformSoupToMarkdown(
            #                                 list(TexSoup(getEnvironment(self.stringSoup[x.position:]), 
            #                                 skip_envs=skip_envs)), indent)),

            "textbf": lambda x, indent: "**" + str(self.transformSoupToMarkdown(
                                            list(x.contents))
                                            ) + "**",
            
            "gbox": lambda x, indent: " `" + str(self.transformSoupToMarkdown(
                                            list(x.contents))
                                            ) + "`",
            "textwidth": lambda x, indent: str(self.transformSoupToMarkdown(
                                            list(x.contents))
                                            ),

            # Abréviations (TODO: à vérifier)
            "node": lambda x, indent: "noeud",
            "ie": lambda x, indent: "ie",
            "ssi": lambda x, indent: "si et seulement si",
            "": lambda x, indent: self.transformSoupToMarkdown(list(x.contents), indent),
        }

        if fun in functions_for_envs:
            return functions_for_envs[fun]
        
        else:
            return None

    def transformSoupToMarkdown(self, soupList, indent=""):
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
                resultString += ' ' + Converter.removeWeirdSpacing(str(soup))

                if type(soup) != data.TexNode:
                    resultString = resultString.rstrip().lstrip()
                    
                continue

            # Si on a prévu une fonction pour cette balise, on l'applique
            func = self.get_functions_for_envs(soup.name)
            if func is not None:
                resultString += str(func(soup, indent))
                continue
            
            # Si la balise n'est pas prise en charge par le script
            # qui se chargera de l'afficher sur le site, on affiche un warning
            if soup.name not in disponible_environments:
                string = Converter.getWeirdEnvironment(self.stringSoup[soup.position-1:])

                # Transforme la balise en image             
                string = self.renderImage(soup.name, string)

                toSkip = soup.position + len(string) + 1
                
                resultString += string

                # resultString += "\n\n$$\n" + Converter.removeWeirdSpacing(str(soup)).rstrip().lstrip() + "\n$$\n\n"
                continue

            # Sinon on applique la fonction sur tous les enfants de la balise
            resultString += self.transformSoupToMarkdown(list(soup.contents), indent)

            resultString += "\n"
            
        return resultString

    @staticmethod
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

    def includeFiles(self, soup):
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
                with open(self.sourcedir + str(input_soup.args[0].string), 'r') as f:
                    stringSoup = f.read()

                # Ajoute le contenu du fichier au fichier principal
                input_soup.replace_with(TexSoup(stringSoup, skip_envs=skip_envs))
            
            except FileNotFoundError:
                print("/!\ Impossible d'importer le fichier " + 
                    str(input_soup.args[0].string))
                
        return TexSoup(str(soup), skip_envs=skip_envs)

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def removeOldImages(imgdir):
        """
        Supprime les images précédentes
        """
        if os.path.exists(imgdir):
            for file in os.listdir(imgdir):
                os.remove(imgdir + file)

    def run(self):
        """
        Fonction principale du script, transforme un fichier .tex en markdown
        """
        # Ouverture du fichier
        with open(self.sourcedir + self.filename, 'r') as f:
            stringSoup = f.read()
            
        soup = TexSoup(stringSoup, skip_envs=skip_envs)
        soup = self.includeFiles(soup)
        soup = Converter.removeComments(soup)

        # Récupération des informations importantes
        self.stringSoup = str(soup)
        self.packages = Converter.getAllImportedPackages(soup)

        # Supprime les images précédentes
        Converter.removeOldImages(self.imgdir)
        os.makedirs(self.imgdir, exist_ok=True)

        # Récupération de la partie importante du fichier
        document = soup.find('document')
        documentList = list(document.contents)

        # Transformation en markdown
        outputString = ""

        # Ajout du titre, author et date
        outputString += "# " + Converter.removeWeirdSpacing(str(soup.find("title").string)) + "\n\n"
        outputString += "## " + Converter.removeWeirdSpacing(str(soup.find("author").string)) + "\n\n"

        outputString += self.transformSoupToMarkdown(documentList)

        # Supprime les faux espaces utilisés pour l'indentation
        outputString = outputString.replace(' ', '')

        # Ecriture dans le fichier
        with open(self.workingdir + self.filename +'.md', 'w') as f:
            f.write(outputString)

        print("Conversion terminée !")
        
if __name__ == '__main__':
    filename = "graphes (copia).tex"
    converter = Converter(filename)
    converter.run()
