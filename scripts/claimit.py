#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
A script that adds claims to Wikidata items based on a list of pages.

These command line parameters can be used to specify which pages to work on:

&params;

Usage:

    python pwb.py claimit [pagegenerators] P1 Q2 P123 Q456

You can use any typical pagegenerator (like categories) to provide with a
list of pages. Then list the property-->target pairs to add.

For geographic coordinates:

    python pwb.py claimit [pagegenerators] P625 [lat-dec],[long-dec],[prec]

[lat-dec] and [long-dec] represent the latitude and longitude respectively,
and [prec] represents the precision. All values are in decimal degrees,
not DMS. If [prec] is omitted, the default precision is 0.0001 degrees.

Example:

    python pwb.py claimit [pagegenerators] P625 -23.3991,-52.0910,0.0001

By default, claimit.py does not add a claim if one with the same property
already exists on the page. To override this behavior, use the 'exists' option:

    python pwb.py claimit [pagegenerators] P246 "string example" -exists:p

Suppose the claim you want to add has the same property as an existing claim
and the "-exists:p" argument is used. Now, claimit.py will not add the claim
if it has the same target, source, and/or the existing claim has qualifiers.
To override this behavior, add 't' (target), 's' (sources), or 'q' (qualifiers)
to the 'exists' argument.

For instance, to add the claim to each page even if one with the same
property and target and some qualifiers already exists:

    python pwb.py claimit [pagegenerators] P246 "string example" -exists:ptq

Note that the ordering of the letters in the 'exists' argument does not matter,
but 'p' must be included.

"""
#
# (C) Legoktm, 2013
# (C) Pywikibot team, 2013-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import pywikibot
from pywikibot import pagegenerators, WikidataBot

# This is required for the text that is shown when you run this script
# with the parameter -help or without parameters.
docuReplacements = {
    '&params;': pagegenerators.parameterHelp,
}


class ClaimRobot(WikidataBot):

    """A bot to add Wikidata claims."""

    use_from_page = None

    def __init__(self, generator, claims, exists_arg=''):
        """
        Constructor.

        @param generator: A generator that yields Page objects.
        @type generator: iterator
        @param claims: A list of wikidata claims
        @type claims: list
        @param exists_arg: String specifying how to handle duplicate claims
        @type exists_arg: str
        """
        self.availableOptions['always'] = True
        super(ClaimRobot, self).__init__()
        self.generator = generator
        self.claims = claims
        self.exists_arg = ''.join(x for x in exists_arg.lower() if x in 'pqst')
        self.cacheSources()
        if self.exists_arg:
            pywikibot.output("'exists' argument set to '%s'" % self.exists_arg)

    def treat_page_and_item(self, page, item):
        """Treat each page."""
        # The generator might yield pages from multiple sites
        source = self.getSource(page.site)

        for claim in self.claims:
            # Existing claims on page of same property
            for existing in item.claims.get(claim.getID(), []):
                # If claim with same property already exists...
                if 'p' not in self.exists_arg:
                    pywikibot.log(
                        'Skipping %s because claim with same property already exists'
                        % (claim.getID(),))
                    pywikibot.log(
                        'Use -exists:p option to override this behavior')
                    break
                if not existing.target_equals(claim.getTarget()):
                    continue
                # If some attribute of the claim being added
                # matches some attribute in an existing claim of
                # the same property, skip the claim, unless the
                # 'exists' argument overrides it.
                if 't' not in self.exists_arg:
                    pywikibot.log(
                        'Skipping %s because claim with same target already exists'
                        % (claim.getID(),))
                    pywikibot.log(
                        "Append 't' to -exists argument to override this behavior")
                    break
                if 'q' not in self.exists_arg and not existing.qualifiers:
                    pywikibot.log(
                        'Skipping %s because claim without qualifiers already exists'
                        % (claim.getID(),))
                    pywikibot.log(
                        "Append 'q' to -exists argument to override this behavior")
                    break
                if ('s' not in self.exists_arg or not source) and not existing.sources:
                    pywikibot.log(
                        'Skipping %s because claim without source already exists'
                        % (claim.getID(),))
                    pywikibot.log(
                        "Append 's' to -exists argument to override this behavior")
                    break
                if ('s' not in self.exists_arg and source and
                        any(source.getID() in ref and
                            all(snak.target_equals(source.getTarget())
                                for snak in ref[source.getID()])
                            for ref in existing.sources)):
                    pywikibot.log(
                        'Skipping %s because claim with the same source already exists'
                        % (claim.getID(),))
                    pywikibot.log(
                        "Append 's' to -exists argument to override this behavior")
                    break
            else:
                self.user_add_claim(item, claim, page.site)


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    @rtype: bool
    """
    exists_arg = ''
    commandline_claims = []

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    gen = pagegenerators.GeneratorFactory()

    for arg in local_args:
        # Handle args specifying how to handle duplicate claims
        if arg.startswith('-exists:'):
            exists_arg = arg.split(':')[1]
            continue
        # Handle page generator args
        if gen.handleArg(arg):
            continue
        commandline_claims.append(arg)
    if len(commandline_claims) % 2:
        pywikibot.error('Incomplete command line property-value pair.')
        return False

    claims = []
    repo = pywikibot.Site().data_repository()
    for i in range(0, len(commandline_claims), 2):
        claim = pywikibot.Claim(repo, commandline_claims[i])
        if claim.type == 'wikibase-item':
            target = pywikibot.ItemPage(repo, commandline_claims[i + 1])
        elif claim.type == 'string':
            target = commandline_claims[i + 1]
        elif claim.type == 'globe-coordinate':
            coord_args = [float(c) for c in commandline_claims[i + 1].split(',')]
            if len(coord_args) >= 3:
                precision = coord_args[2]
            else:
                precision = 0.0001  # Default value (~10 m at equator)
            target = pywikibot.Coordinate(coord_args[0], coord_args[1], precision=precision)
        else:
            raise NotImplementedError(
                "%s datatype is not yet supported by claimit.py"
                % claim.type)
        claim.setTarget(target)
        claims.append(claim)

    generator = gen.getCombinedGenerator()
    if not generator:
        pywikibot.bot.suggest_help(missing_generator=True)
        return False

    bot = ClaimRobot(generator, claims, exists_arg)
    bot.run()
    return True


if __name__ == "__main__":
    main()
