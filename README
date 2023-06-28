# NoyerTransformer

Ce script permet de transformer un fichier tex (dont ses includes) en un fichier markdown utilisable par mkdocs.

- Fait avec **Python 3.10**

## Utilisation

```bash
python3 -m noyerTransformer <chemin fichier.tex>
```

Exemple de sortie :

```bash
$ python3 -m noyerTransformer graphes.tex
/!\ Impossible d'importer le fichier topo.tex
/!\ Impossible d'importer le fichier cfc.tex

/!\ Commande impossible à parser : \xymatrix @R=1pc { *=+<15pt>[o][F]{0}\ar[r]\ar[rd] &*=+<15pt>[o][F]{1}\ar[r] &*=+<15pt>[o][F]{3}\\ &*=+<15pt>[o][F]{2}\ar[u]& }
Conversion en image...

Conversion en image réussie

Conversion terminée !
$ ls
graphes.tex.md  images
```

Ici `graphes.tex.md` contient tout le fichier tex converti en markdown, et `images` contient un sous dossier du nom du fichier (ici `graphes`) qui lui même contient toutes les images utilisées par le `graphes` et celles qui sont générées pour contourner les problèmes de compatibilités entre le latex utilisé par l'utilisateur et celui de Mkdocs.

## Installation

Pour utiliser le script, il faut installer les dépendances suivantes :

```bash
sudo apt install netpbm poppler-utils texlive-extra-utils
```

Pour ma part, compiler le fichier graphes.tex donné en exemple necéssita l'installation de (notamment pour le package `xypic`):

```bash
sudo apt install texlive-full
```

Une fois tout cela installé, il suffit d'installer le logiciel via pip :

```bash
pip install noyerTransformer
```
