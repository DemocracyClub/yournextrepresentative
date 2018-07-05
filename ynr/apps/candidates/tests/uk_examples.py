# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.contenttypes.models import ContentType

from datetime import date

from . import factories

class UK2015ExamplesMixin(object):

    def setUp(self):
        ContentType.objects.clear_cache()

    @classmethod
    def setUpTestData(cls):
        super(UK2015ExamplesMixin, cls).setUpTestData()
        cls.gb_parties = factories.PartySetFactory.create(
            slug='gb', name='Great Britain'
        )
        cls.ni_parties = factories.PartySetFactory.create(
            slug='ni', name='Northern Ireland'
        )
        commons_extra = factories.ParliamentaryChamberExtraFactory.create()
        cls.commons = commons_extra.base
        # Create the 2010 and 2015 general elections:
        cls.election = factories.ElectionFactory.create(
            slug='2015',
            name='2015 General Election',
            for_post_role='Member of Parliament',
        )
        cls.earlier_election = factories.EarlierElectionFactory.create(
            slug='2010',
            name='2010 General Election',
            for_post_role='Member of Parliament',
            current=False,
        )
        # Create some example parties:
        factories.PartyFactory.reset_sequence()
        factories.PartyExtraFactory.reset_sequence()
        EXAMPLE_PARTIES = [
            {
                'id': 'party:53',
                'name': 'Labour Party',
                'attr': 'labour_party_extra',
                'party_set': cls.gb_parties,
            },
            {
                'id': 'party:90',
                'name': 'Liberal Democrats',
                'attr': 'ld_party_extra',
                'party_set': cls.gb_parties,
            },
            {
                'id': 'party:63',
                'name': 'Green Party',
                'attr': 'green_party_extra',
                'party_set': cls.gb_parties,
            },
            {
                'id': 'party:52',
                'name': 'Conservative Party',
                'attr': 'conservative_party_extra',
                'party_set': cls.gb_parties,
            },
            {
                'id': 'party:39',
                'name': 'Sinn Féin',
                'attr': 'sinn_fein_extra',
                'party_set': cls.ni_parties,
            },
        ]
        for party in EXAMPLE_PARTIES:
            p = factories.PartyExtraFactory(
                slug=party['id'],
                base__name=party['name'],
            )
            p.base.identifiers.update_or_create(
                scheme='electoral-commission',
                defaults={
                    'identifier': "PP{}".format(party['id'].split(':')[1]),
                }
            )
            setattr(cls, party['attr'], p)
            party['party_set'].parties.add(p.base)
        # Create some example posts as well:
        EXAMPLE_CONSTITUENCIES = [
            {
                'id': '14419',
                'name': 'Edinburgh East',
                'country': 'Scotland',
                'attr': 'edinburgh_east_post_extra',
            },
            {
                'id': '14420',
                'name': 'Edinburgh North and Leith',
                'country': 'Scotland',
                'attr': 'edinburgh_north_post_extra',
            },
            {
                'id': '65808',
                'name': 'Dulwich and West Norwood',
                'country': 'England',
                'attr': 'dulwich_post_extra',
            },
            {
                'id': '65913',
                'name': 'Camberwell and Peckham',
                'country': 'England',
                'attr': 'camberwell_post_extra',
            },
        ]
        for cons in EXAMPLE_CONSTITUENCIES:
            label = 'Member of Parliament for {}'.format(cons['name'])
            pe = factories.PostExtraFactory.create(
                elections=(cls.election, cls.earlier_election),
                base__organization=cls.commons,
                slug=cons['id'],
                base__label=label,
                party_set=cls.gb_parties,
                group=cons['country'],
            )

            setattr(cls, cons['attr'], pe)

            pee_attr_name = "{}_pee".format(cons['attr'])
            pee = pe.postextraelection_set.get(election=cls.election)
            setattr(cls, pee_attr_name, pee)

            pee_attr_name = "{}_pee_earlier".format(cons['attr'])
            pee = pe.postextraelection_set.get(election=cls.earlier_election)
            setattr(cls, pee_attr_name, pee)


        # Also create a local election and post:
        cls.local_council = factories.OrganizationExtraFactory.create(
            base__name='Maidstone',
            slug='local-authority:maidstone',
        ).base
        cls.local_election = factories.ElectionFactory.create(
            slug='local.maidstone.2016-05-05',
            organization=cls.local_council,
            name='Maidstone local election',
            for_post_role='Local Councillor',
            election_date=date(2016, 5, 5),
        )
        cls.local_post = factories.PostExtraFactory.create(
            elections=(cls.local_election,),
            slug='DIW:E05005004',
            base__label='Shepway South Ward',
            party_set=cls.gb_parties,
            base__organization=cls.local_council,
        )
