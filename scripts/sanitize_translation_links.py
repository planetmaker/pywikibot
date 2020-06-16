#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
An incomplete sample script.

This is not a complete bot; rather, it is a template from which simple
bots can be made. You can rename it to mybot.py, then edit it in
whatever way you want.

Use global -simulate option for test purposes. No changes to live wiki
will be done.


The following parameters are supported:

-always           The bot won't ask for confirmation when putting a page

-text:            Use this text to be added; otherwise 'Test' is used

-replace:         Don't add text but replace it

-top              Place additional text on top of the page

-summary:         Set the action summary message for the edit.


The following generators and filters are supported:

&params;
"""
#
# (C) Pywikibot team, 2006-2019
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import pywikibot
from pywikibot import pagegenerators

from pywikibot.bot import (
    SingleSiteBot, ExistingPageBot, NoRedirectPageBot, AutomaticTWSummaryBot)

import re

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816

name_chars = ' \'’\-_:\w\d'
name_regex = '([' + name_chars + ']*)'
trad_regex = '{{trad([' + name_chars + ',\.\s\|\=]*)?}}'


class BasicBot(
    # Refer pywikobot.bot for generic bot classes
    SingleSiteBot,  # A bot only working on one site
    # CurrentPageBot,  # Sets 'current_page'. Process it in treat_page method.
    #                  # Not needed here because we have subclasses
    ExistingPageBot,  # CurrentPageBot which only treats existing pages
    NoRedirectPageBot,  # CurrentPageBot which only treats non-redirects
    AutomaticTWSummaryBot,  # Automatically defines summary; needs summary_key
):

    """
    An incomplete sample bot.

    @ivar summary_key: Edit summary message key. The message that should be
        used is placed on /i18n subdirectory. The file containing these
        messages should have the same name as the caller script (i.e. basic.py
        in this case). Use summary_key to set a default edit summary message.

    @type summary_key: str
    """

    summary_key = 'basic-changing'

    def __init__(self, generator, **kwargs):
        """
        Initializer.

        @param generator: the page generator that determines on which pages
            to work
        @type generator: generator
        """
        # Add your own options to the bot and set their defaults
        # -always option is predefined by BaseBot class
        self.availableOptions.update({
            'replace': False,  # delete old text and write the new text
            'summary': None,  # your own bot summary
            'text': 'Test',  # add this text from option. 'Test' is default
            'top': False,  # append text on top of the page
            'write': False, # write the page
            'info': False, # print further debug output
        })

        # call initializer of the super class
        super(BasicBot, self).__init__(site=True, **kwargs)

        # assign the generator to the bot
        self.generator = generator

    def get_translation_name_wikilink(self, text, lang):
        """
        @param text: The page text to look through
        @type generator: text

        @param lang: The 2-letter lang indicator
        @type lang string (2 chars)

        """
        reg_strg = r'\[\[' + lang + ':' + name_regex + '\]\]'
        wiki_lang = re.search(reg_strg, text, re.IGNORECASE)

        try:
            strg = wiki_lang.group(1)
            strg = strg.strip()
        except:
            strg = None
        if strg == '':
            strg = None

        return strg, None

    def get_translation_name_trad(self, text, lang):
        """
        @param text: The page text to look through
        @type generator: text

        @param lang: The 2-letter lang indicator
        @type lang string (2 chars)

        """
        # Search for the {{trad template and extract that}}
        reg_strg = r'\|' + lang + ' ?=' + name_regex
        reg_quality = r'\|' + lang + 's ?= ?([0-9])'
        trad_lang = re.search(reg_strg, text, re.IGNORECASE)
        trad_quality = re.search(reg_quality, text, re.IGNORECASE)

        try:
            strg = trad_lang.group(1)
            strg = strg.strip()
            try:
                quality = trad_quality.group(1)
                quality = quality.strip()
            except:
                quality = None
        except:
            strg = None
            quality = None
        if strg == '':
            strg = None

        return strg, quality

    def get_translation_name(self, text, lang):
        """
        @param text: The page text to look through
        @type generator: text

        @param lang: The 2-letter lang indicator
        @type lang string (2 chars)

        """
        trad_name, quality = self.get_translation_name_trad(text, lang)
        wiki_name, w_quality = self.get_translation_name_wikilink(text, lang)

        #print("Translations: ", trad_name, wiki_name, quality)

        name = trad_name
        if trad_name is None:
            name = wiki_name
        elif wiki_name is None:
            name = trad_name
        elif trad_name is not None and wiki_name is not None and trad_name != wiki_name:
            print("WARNING: " + self.current_page.title()  + " different pages linked for ", lang, ":")
            print(trad_name, " <-> ", wiki_name)
            name = trad_name


        return name, quality


    def contains_translation(self, text, translations):
        """
        @param text             Text to check whether it's a translation string or quality
        @param translations     The existing translations. We use the keys.
        """
        #print("Checking for text to contain translation: ", text)
        for lang in translations.keys():
            if lang.upper() in text:
                return True
        return False

    def create_new_trad_template(self, text, translations):
        """
        text : string
            Text of the entire page
        translations: dict of translations

        returns trad_template, replacing_old
            string of new {{trad}} template and boolean whether we replace an old template

        """
        rex = re.search(trad_regex, text, re.IGNORECASE | re.MULTILINE)
        if self.getOption('info'):
            print("regex result for trad template: ", rex)

        new_trad_template = ""

        for lang,page in translations.items():
            #print("Lang: ", lang, page)
            if page['name'] is None:
                pagename = ""
            else:
                pagename = page['name']
            new_trad_template += '|' + lang.upper() + '=' + pagename
            if page['quality'] is not None:
                new_trad_template += '|' + lang.upper() + 's=' + page['quality']
            new_trad_template += '\n'
            if self.getOption('info'):
                print('pagename done:' ,lang)

        if self.getOption('info'):
            print("new_trad_template translations:\n", new_trad_template)

        try:
            strgs = rex.group(1).split('|')
            for i in range(0,len(strgs)):
                strgs[i] = strgs[i].strip()
            for s in strgs:
                #print("Checking s: ", s)
                if len(s) == 0:
                    #print("Droppling string length 0")
                    continue
                elif self.contains_translation(s, translations):
                    #print("Ignoring s in lang.upper(): ", s)
                    continue
                elif (s == '\n' or s == ' '):
                    #print("Ignoring s in \\n or ' ': ",s)
                    continue
                if self.getOption('info'):
                    print("Adding s: ", s)
                new_trad_template += '|' + s + '\n'
        except:
            print(self.current_page.title() + ": No {{trad}} template found.")
            pass

        new_trad_template = '{{Trad\n' + new_trad_template + '}}'
        replacing = (rex is not None)

        return new_trad_template, replacing

    def replace_translation_template(self, text, translations):
        """
        @param text         The page text to look through
        @param translations dictionary of translations
        """
        reg_strg = '{{trad([' + name_chars + ',\.\s\|\=]*)?}}'
        rex = re.search(reg_strg, text, re.IGNORECASE | re.MULTILINE)

        if self.getOption('info'):
            print("regex result for trad template: ", rex)

        new_trad_template,replacing = self.create_new_trad_template(text, translations)

        if self.getOption('info'):
            print("=== OLD " +self.current_page.title() + " =========================================")
            print(text, '\n')
        if replacing: # in this case, there is no translation template. Add it
            newtext = re.sub(reg_strg, new_trad_template, text, flags=(re.IGNORECASE | re.MULTILINE))
        else:
            newtext = new_trad_template + text
        if self.getOption('info'):
            print("=== NEW " +self.current_page.title() + " =========================================")
            print(newtext)
            print("=== END " +self.current_page.title() + " =========================================")

        return newtext

    def remove_wiki_language_links(self, text, translations):
        #print(lang, page)
        for lang, pagename in translations.items():
            reg_strg = r'\[\[' + lang + ':' + name_regex + '\]\](\n)?'
            text = re.sub(reg_strg, '', text, flags=re.IGNORECASE)
        return text

    def add_wiki_language_links(self, text, translations):
        for lang, page in translations.items():
            if page['name'] is not None and page['name'] != "":
                pagelink = '[[' + lang + ':' + page['name'] + ']]'
                text = text + '\n' + pagelink
                #print(pagelink)
        return text

    def get_pagename_translations(self, text):
        lang_arr = ["de", "en", "es", "fr", "ru"]
        translations = dict()

        for lang in lang_arr:
            name, quality = self.get_translation_name(text, lang)
            translations[lang] = {'name':name, 'quality':quality}

        # make sure we use the correct name for the page we edit
        translations[self.site.lang]['name'] = self.current_page.title()

        if self.getOption('info'):
            print(translations)

        return translations



    def treat_page(self):
        """Load the given page, do some changes, and save it."""
        text = self.current_page.text

        ################################################################
        # NOTE: Here you can modify the text in whatever way you want. #
        ################################################################

        # If you find out that you do not want to edit this page, just return.
        # Example: This puts Text on a page.

        translations = self.get_pagename_translations(text)

        text = self.replace_translation_template(text, translations)

        # remove old ones and add new ones at bottom of page
        text = self.remove_wiki_language_links(text, translations)
        text = self.add_wiki_language_links(text, translations)

        #print("Current page to write:")
        #print(text)

        #if self.getOption('replace'):
            ## replace the page text
            #print("replace!")
            #text = text_to_add

        #elif self.getOption('top'):
            #print("top!")
            ## put text on top
            #text = text_to_add + text

        if self.getOption('write'):
            print("saving page '" + translations['de']['name'] + "'")
            self.put_current(text, summary=self.getOption('summary'))

        else:
            # put text on bottom
            text += text_to_add

        # if summary option is None, it takes the default i18n summary from
        # i18n subdirectory with summary_key as summary key.
        # self.put_current(text, summary=self.getOption('summary'))


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: str
    """
    options = {}
    # Process global arguments to determine desired site
    local_args = pywikibot.handle_args(args)

    # This factory is responsible for processing command line arguments
    # that are also used by other scripts and that determine on which pages
    # to work on.
    gen_factory = pagegenerators.GeneratorFactory()

    # Parse command line arguments
    for arg in local_args:

        # Catch the pagegenerators options
        if gen_factory.handleArg(arg):
            continue  # nothing to do here

        # Now pick up your own options
        arg, sep, value = arg.partition(':')
        option = arg[1:]
        if option in ('summary', 'text'):
            if not value:
                pywikibot.input('Please enter a value for ' + arg)
            options[option] = value
        # take the remaining options as booleans.
        # You will get a hint if they aren't pre-defined in your bot class
        else:
            options[option] = True

    # The preloading option is responsible for downloading multiple
    # pages from the wiki simultaneously.
    gen = gen_factory.getCombinedGenerator(preload=True)
    if gen:
        # pass generator and private options to the bot
        bot = BasicBot(gen, **options)
        bot.run()  # guess what it does
    else:
        pywikibot.bot.suggest_help(missing_generator=True)


if __name__ == '__main__':
    main()
