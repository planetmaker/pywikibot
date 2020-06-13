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
        })

        # call initializer of the super class
        super(BasicBot, self).__init__(site=True, **kwargs)

        # assign the generator to the bot
        self.generator = generator

    def get_translation_name(self, text, lang):
        """
        @param text: The page text to look through
        @type generator: text

        @param lang: The 2-letter lang indicator
        @type lang string (2 chars)
        """
        reg_strg = r'\|' + lang + ' ?=([ \w]*)'
        #print(reg_strg)
        rex = re.search(reg_strg, text, re.IGNORECASE)
        #print(rex)
        try:
            strg = rex.group(1)
        except:
            strg = None

        #if strg is not None:
            #print(lang + ': ' + strg)

        ret = dict()
        ret[lang] = strg
        return ret

    def replace_translation_template(self, text, translations):
        """
        @param text The page text to look through
        @param translations dictionary of translations
        """
        reg_strg = '{{trad([\w\s\|\=]*)}}'
        rex = re.search(reg_strg, text, re.IGNORECASE | re.MULTILINE)

        print("Replacing:")
        try:
            print(rex.group(1))
            strgs = rex.group(1).split('|')
            print(strgs)
            new_strg = ""
            for lang,pagename in translations.items():
                if pagename is None:
                    pagename = ""
                new_strg += '|' + lang.upper() + '=' + pagename + '\n'

            #print("New_strg: ", new_strg)

            for lang in translations.keys():
                for (n,str) in enumerate(strgs):
                    if lang.upper() in str:
                        strgs.pop(n)

            for s in strgs:
                if len(s) > 2:
                    new_strg += '|' + s + '\n'

            new_strg = '{{Trad\n' + new_strg + '}}'
            #print(new_strg, '\n')
            #print('\n with \n \n')
            newtext = re.sub(reg_strg, new_strg, text, flags=re.IGNORECASE | re.MULTILINE)
            #print(newtext)

        except:
            print("no text matched:", rex)

        return newtext



    def treat_page(self):
        """Load the given page, do some changes, and save it."""
        text = self.current_page.text

        ################################################################
        # NOTE: Here you can modify the text in whatever way you want. #
        ################################################################

        # If you find out that you do not want to edit this page, just return.
        # Example: This puts Text on a page.

        # Retrieve your private option
        # Use your own text or use the default 'Test'
        text_to_add = self.getOption('text')

        lang_arr = ["de", "en", "es", "fr", "ru"]

        translations = dict()
        for lang in lang_arr:
            translations = {**translations, **self.get_translation_name(text, lang)}
        print(translations)

        for lang, pagename in translations.items():
            print(lang, pagename)
            if pagename is not None:
                pagelink = '[[' + lang + ':' + pagename + ']]'
                if pagelink not in text:
                    text = text + '\n' + pagelink
                    print(pagelink)

        text = self.replace_translation_template(text, translations)

        print("Current page to write:")
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
            print("saving" + translations['de'])
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
