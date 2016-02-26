#!/usr/bin/python3
# menudesktop: Genera un menú a partir de archivos desktop entry.
# GPL v3+

import os
import unidecode
import glob
from collections import OrderedDict
import argparse

defwm = 'openbox'
editor = 'gvim'
executor = 'exo-open'
fileman = 'exo-open --launch FileManager'
wmexec = 'xfce4-appfinder --collapsed'
supported_wms = ('openbox', 'fvwm')
#default_dir = os.environ['HOME'] + '/.local/share/applications'
default_dir = os.environ['HOME'] + '/bin/apps'
dirs = (default_dir,)
#dirs = (default_dir, '/usr/share/applications')
fromcache = False
cachepath = os.path.expandvars('$HOME') + '/.cache'
allapps = False
deadicon = False

lang = os.environ['LANG']
long_lang = lang.split('.')[0]  # es_ES
short_lang = long_lang.split('_')[0]  # en

full_lang = lang.replace('UTF-8', 'utf8')  # Renaming in Thunar.
fmt_full_lang = '[' + full_lang + ']'  # Renaming in Thunar.
fmt_long_lang = '[' + long_lang + ']'  # [es_ES]...
fmt_short_lang = '[' + short_lang + ']'  # [en]...
locale = {
        'en': {
            'AudioVideo': 'Multimedia',
            'Audio': 'Audio',
            'Video': 'Video',
            'Development': 'Development',
            'Education': 'Education',
            'Game': 'Games',
            'Graphics': 'Graphics',
            'Network': 'Networks',
            'Office': 'Office',
            'Settings': 'Settings',
            'System': 'System',
            'Utility': 'Utilities',
            },
        'es': {
            'AudioVideo': 'Multimedia',
            'Audio': 'Audio',
            'Video': 'Vídeo',
            'Development': 'Programación',
            'Education': 'Educación',
            'Game': 'Juegos',
            'Graphics': 'Gráficos',
            'Network': 'Redes',
            'Office': 'Oficina',
            'Settings': 'Ajustes',
            'System': 'Sistema',
            'Utility': 'Accesorios',
            },
        }

class Item:
    fsep = '='  # Separador de campos
    esep = ';'  # Separador de elementos


    def __init__(self, dfile):
        self.fdict = {}  # Diccionario del archivo
        try:
            self.myfile = open(dfile, 'r')
        except IOError:
            print('No puedo abrir el archivo', dfile)
            exit(1)

        for line in self.myfile:
            if line.startswith('#') or line.isspace() or line.startswith('['):
                continue
            f = line.split(self.fsep)  # Separamos las líneas en campos
            self.fdict[f[0].strip()] = f[1].strip()
        self.myfile.close()

        self.execute = executor + ' ' + dfile
        self.label = getlang('Name', self.fdict, os.path.basename(dfile))
        self.icon = getlang('Icon', self.fdict, 'image_missing')
        self.menu = getlang('Categories', self.fdict, '0')  # 0 para ordenarlo

        for i in self.menu.split(';'):
            if i in locale[short_lang]:
                self.menu = self.menu.replace(i, locale[short_lang][i])

        executable = self.fdict['Exec'].strip().partition(' ')[0]
        self.avaible = which(executable)
        if not self.avaible:
            self.label = self.label + ' (No instalado)'
            self.execute = install(executable)
            if deadicon:
                self.icon = 'no_installed'


    def addto(self, d):
        if not allapps and not self.avaible:
            return 0
        for menu in self.menu.split(self.esep):
            menu = menu.strip()
            if menu in d:
                d[menu].append([self.label, self.execute, self.icon])
            else:
                d[menu] = [[self.label, self.execute, self.icon]]


def getlang(tag, dic, fallback):
    candidates = (
            tag + fmt_full_lang,
            tag + fmt_long_lang,
            tag + fmt_short_lang,
            tag
            )
    for candidate in candidates:
        if candidate in dic:
            return(dic[candidate])
    return(fallback)


def which(program):
    fpath, fname = os.path.split(program)
    if fpath:
        # Si se especifica una ruta completa.
        exe = program
    else:
        # Si no, busca el ejecutable en PATH.
            for path in os.environ["PATH"].split(os.pathsep):
                    exe = os.path.join(path, program)
                    if os.path.isfile(exe):
                        break
    if os.access(exe, os.X_OK):
        return True
    else:
        return False


def install(app):
    cmdline = 'gksu pacman -Syu ' + app
    return(cmdline)

def dfind(mydir):
    '''Find destop files in a dir'''
    try:
        os.listdir(mydir)
        dfiles = glob.glob(mydir + "/*.desktop")
    except:
        return(mydir, 'no es un directorio')
        # FIXME: Si glob está vacío devuelve []
    return(dfiles)

def gen_dbase():
    dbase = {}
    for mydir in dirs:
        alldfiles = dfind(mydir)
        for afile in alldfiles:
            app = Item(afile)
            app.addto(dbase)
            dbase = OrderedDict(sorted(dbase.items(), key=lambda t: t[0]))
    return(dbase)


def gen_format(wm):
    dbase = gen_dbase()
    if wm == 'openbox':
        fdbase = gen_openbox(dbase)
    elif wm == 'fvwm':
        fdbase = gen_fvwm(dbase)
    else:
        print('No sé cómo producir un menú para ' + wm + '.'
                + wm + 'no está soportado.')
        exit(1)
    return(fdbase)


def print_format(wm):
    data = gen_format(wm)
    for line in data:
        print(line)


def write_cache(wm):
    cache = cachepath + '/menuapps.' + wm + '.cache'
    data = gen_format(wm)

    try:
        cache_w = open(cache, 'w')
        for line in data:
            cache_w.write(line + '\n')
    except IOError:
        print('No puedo escribir en ' + cache)
        exit(1)
    cache_w.close()


def print_from_cache(wm):
    if wm in supported_wms:
        cache = cachepath + '/menuapps.' + wm + '.cache'
    else:
        print('No sé cómo leer un menú para ' + wm)
        exit(1)
    try:
        cache_r = open(cache, 'r')
        for line in cache_r:
            print(line, end='')
    except IOError:
        print('No puedo leer en ' + cache)
        exit(1)


def gen_openbox(db):
    openbox = []
    #icondir = os.environ['OPENBOX_ICONDIR']
    icondir = '/usr/local/share/icons/retrosmart/scalable'
    ext = '.svg'
    noiconfile = icondir + '/' + 'image-missing' + ext
    separator = True

    openbox.append('<openbox_pipe_menu>')
    openbox.append(
        '<item label="_Ir a las aplicaciones" '
        + 'icon="' + icondir + '/go-jump' + ext + '">'
        + '<action name="Execute"><execute>' + fileman + ' ' + default_dir
        + '</execute></action></item>')

    if fromcache:
        openbox.append(
            '<item label="_Recargar caché" '
            + 'icon="' + icondir + '/reload' + ext + '">'
            + '<action name="Execute">'
            + '<execute>menuapps -w openbox</execute></action></item>')

    openbox.append('<separator/>')
    openbox.append(
        '<item label="_Ejecutar" icon="' + icondir + '/gnome-run' + ext
        + '"><action name="Execute"><execute>' + wmexec
        + '</execute></action></item>')

    if db:
        openbox.append('<separator/>')
        for submenu in db.keys():
            if not submenu:  # Hay entradas vacías
                continue
            fmtsubmenu = unidecode.unidecode(submenu).lower().replace(' ', '_')

            if submenu != '0':
                if separator:
                    openbox.append('<separator/>')
                    separator = False

                openbox.append(
                    '<menu id="obapps-' + fmtsubmenu
                    + '" label="' + submenu
                    + '" icon="' + icondir + '/' + fmtsubmenu + ext
                    + '">')

            for item in sorted(db[submenu]): # Contenido de submenus ordenados
                label = item[0]
                execute = item[1]
                icon = item[2]

                if not '/' in icon:
                    iconfile = icondir + '/' + icon + ext
                else:
                    iconfile = icon

                if os.path.isfile(iconfile):
                    iconpath = iconfile
                else:
                    iconpath = noiconfile

                openbox.append(
                    '<item label="' + label +
                    '" icon="' + iconpath +
                    '"><action name="Execute"><execute>' + execute +
                    '</execute></action></item>')
            if submenu != '0':
                openbox.append('</menu>')
    else:
        openbox.append(
            '<item label="_No puedo abrir el archivo" icon="'
            + icondir + '/error' + ext + '">' + '</item>')
    openbox.append('</openbox_pipe_menu>')
    return(openbox)


def gen_fvwm(db):
    fvwm = []
    icondir = '/usr/local/share/icons/retrosmart/scalable'  # Para image-missing
    ext = '.svg'

    fvwm.append('+ "Aplicaciones" Title')
    fvwm.append(
        '+ "_Editar este menú%pencil.svg:22x22%" Exec ' + editor + ' ' + conf)
    fvwm.append('+ "Recargar caché%reload.svg:22x22%" Exec menuapps -w fvwm')
    fvwm.append('+ "" Nop')
    fvwm.append('+ "Ejecutar%system-run.svg:22x22%" Exec ' + wmexec)
    fvwm.append('+ "" Nop')

    if db:
        for submenu in db.keys():
            lowersubmenu = submenu.lower()
            unacclowersubmenu = unidecode.unidecode(submenu).lower()

            fvwm.append(
                '+ "' + submenu + '%' + unacclowersubmenu + ext + ':22x22%"'
                + ' Popup ' + submenu)

        for submenu in db.keys():
            fvwm.append('DestroyMenu ' + submenu)
            fvwm.append('AddToMenu ' + submenu + ' "' + submenu + '" Title')

            for item in sorted(db[submenu]):
                label = item[0].strip()
                execute = item[1].strip()
                icon = item[2].strip()

                # Podría coger el icono directamente del las opciones de fvwm
                # pero perderíamos la funcionalidad de image-missing.
                iconfile = icondir + '/' + icon + ext
                noiconfile = icondir + '/' + 'image-missing' + ext
                if os.path.isfile(iconfile):
                    iconpath = iconfile
                else:
                    iconpath = noiconfile

                fvwm.append(
                    '+ "' + label + '%' + iconpath + ':22x22%"'
                    + ' Exec ' + execute)
    else:
        fvwm.append(
            '<item label="_No puedo abrir el archivo" icon="'
            + icondir + '/error' + ext + '">' + '</item>')

    return(fvwm)


def gen_blackbox(db):
    blackbox = []
    icondir = os.environ['OPENBOX_ICONDIR']
    ext = '.png'

    blackbox.append('<blackbox_pipe_menu>')
    blackbox.append(
        '<item label="_Editar este menú" '
        + 'icon="' + icondir + '/pencil' + ext + '">'
        + '<action name="Execute"><execute>' + editor + ' ' + conf
        + '</execute></action></item>')
    blackbox.append(
        '<item label="_Recargar caché" '
        + 'icon="' + icondir + '/reload' + ext + '">'
        + '<action name="Execute">'
        + '<execute>menuapps blackbox</execute></action></item>')
    blackbox.append('<separator/>')
    blackbox.append(
        '<item label="_Ejecutar" icon="'
        + icondir + '/gnome-run' + ext + '"><action name="Execute"><execute>'
        + wmexec + '</execute></action></item>')
    blackbox.append('<separator/>')

    if db:
        for submenu in db.keys():
            lowersubmenu = submenu.lower()
            unacclowersubmenu = unidecode.unidecode(submenu).lower()

            if submenu != '0':
                blackbox.append(
                    '<menu id="obapps-' + lowersubmenu
                    + '" label="' + submenu
                    + '" icon="' + icondir + '/' + unacclowersubmenu + ext
                    + '">')

            for item in sorted(db[submenu]):
                label = item[0].strip()
                execute = item[1].strip()
                icon = item[2].strip()

                blackbox.append(
                    '<item label="' + label
                    + '" icon="' + icondir + '/' + icon + ext
                    + '"><action name="Execute"><execute>' + execute
                    + '</execute></action></item>')
            if submenu != '0':
                blackbox.append('</menu>')

    else:
        blackbox.append(
            '<item label="_No puedo abrir el archivo" icon="'
            + icondir + '/error' + ext + '">' + '</item>')
    blackbox.append('</blackbox_pipe_menu>')
    return(blackbox)


def gen_fluxbox(db):
    fluxbox = []
    icondir = os.environ['OPENBOX_ICONDIR']
    ext = '.png'

    fluxbox.append('<fluxbox_pipe_menu>')
    fluxbox.append(
        '<item label="_Editar este menú" '
        + 'icon="' + icondir + '/pencil' + ext + '">'
        + '<action name="Execute"><execute>' + editor + ' ' + conf
        + '</execute></action></item>')
    fluxbox.append(
        '<item label="_Recargar caché" '
        + 'icon="' + icondir + '/reload' + ext + '">'
        + '<action name="Execute">'
        + '<execute>menuapps fluxbox</execute></action></item>')
    fluxbox.append('<separator/>')
    fluxbox.append(
        '<item label="_Ejecutar" icon="' + icondir + '/gnome-run' + ext
        + '"><action name="Execute"><execute>'
        + wmexec + '</execute></action></item>')
    fluxbox.append('<separator/>')

    if db:
        for submenu in db.keys():
            lowersubmenu = submenu.lower()
            unacclowersubmenu = unidecode.unidecode(submenu).lower()

            if submenu != '0':
                fluxbox.append(
                    '<menu id="obapps-' + lowersubmenu
                    + '" label="' + submenu
                    + '" icon="' + icondir + '/' + unacclowersubmenu + ext
                    + '">')

            for item in sorted(db[submenu]):
                label = item[0].strip()
                execute = item[1].strip()
                icon = item[2].strip()

                fluxbox.append(
                    '<item label="' + label
                    + '" icon="' + icondir + '/' + icon + ext
                    + '"><action name="Execute"><execute>'
                    + execute + '</execute></action></item>')
            if submenu != '0':
                fluxbox.append('</menu>')

    else:
        fluxbox.append(
            '<item label="_No puedo abrir el archivo" icon="'
            + icondir + '/error' + ext + '">' + '</item>')
    fluxbox.append('</fluxbox_pipe_menu>')
    return(fluxbox)


parser = argparse.ArgumentParser()
parser.add_argument(
    'wm', help='El tipo de WM para el que se producirá el menú.')
parser.add_argument(
    '-c', '--cache', action='store_true',
    help='Imprime el menú desde la caché.')
parser.add_argument(
    '-w', '--write', action='store_true',
    help='Escribe la caché.')
parser.add_argument(
    '-a', '--allapps', action='store_true',
    help='Muestra la aplicación aunque no esté instalada.')
parser.add_argument(
    '-i', '--icons', action='store_true',
    help='Muestra el icono de la aplicación no instalada. No una lápida.')

args = parser.parse_args()

if args.allapps:
    # Muestra todas las aplicaciones, aunque no estén instaladas.
    allapps = args.allapps
    if args.icons:
        # Muestra el icono de la aplicación no instalada en lugar de una lápida
        # No se tiene en cuenta si no se emplea -a
        deadicon = args.icons

if args.cache:
    # Imprime desde archivo caché.
    print_from_cache(args.wm)
elif args.write:
    # Escribe archivo caché desde conf.
    # FIXME: Añadir mensaje de error para wm
    write_cache(args.wm)
else:
    # Imprime desde archivo conf.
    # FIXME: Añadir mensaje de error para wm
    print_format(args.wm)
