import pytest

from tasa_website.helpers import POSITIONS, officer_sections, position_section, position_title

EXPECTED_SECTIONS = {
    'President': 'Executive Board',
    'Internal Vice President': 'Executive Board',
    'External Vice President': 'Executive Board',
    'Treasurer': 'Officers',
    'Webmaster': 'Officers',
    'Outreach': 'Officers',
    'Design': 'Officers',
    'Marketing': 'Officers',
    'Public Relations': 'Officers',
    'Family Head': 'Officers',
    'Historian': 'Officers',
    'Senior Advisor': 'Senior Advisors',
    'Treasurer Intern': 'Interns',
    'Webmaster Intern': 'Interns',
    'Outreach Intern': 'Interns',
    'Design Intern': 'Interns',
    'Marketing Intern': 'Interns',
    'Public Relations Intern': 'Interns',
    'Family Head Intern': 'Interns',
    'Historian Intern': 'Interns',
}


def test_every_position_is_mapped():
    assert len(POSITIONS) == len(EXPECTED_SECTIONS)


@pytest.mark.parametrize('index,title', list(enumerate(POSITIONS)))
def test_position_section(index, title):
    assert position_section(index) == EXPECTED_SECTIONS[title]


def test_out_of_range_positions_are_safe():
    assert position_section(-1) == 'Officers'
    assert position_section(99) == 'Officers'
    assert position_title(99) == 'Officer'


class FakeOfficer:
    def __init__(self, name, position):
        self.name = name
        self.position = position


def test_officer_sections_order_and_grouping():
    officers = [
        FakeOfficer('Zoe', 12),   # Treasurer Intern
        FakeOfficer('Amy', 0),    # President
        FakeOfficer('Ben', 11),   # Senior Advisor
        FakeOfficer('Cat', 4),    # Webmaster
        FakeOfficer('Ann', 4),    # Webmaster (same position, sorts by name)
    ]
    sections = officer_sections(officers)
    assert [name for name, _ in sections] == ['Executive Board', 'Officers', 'Interns', 'Senior Advisors']
    officers_bucket = dict(sections)['Officers']
    assert [o.name for o in officers_bucket] == ['Ann', 'Cat']


def test_empty_sections_omitted():
    sections = officer_sections([FakeOfficer('Amy', 0)])
    assert len(sections) == 1
    assert sections[0][0] == 'Executive Board'
