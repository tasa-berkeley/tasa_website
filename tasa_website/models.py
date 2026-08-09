from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .extensions import db


class Officer(db.Model):
    __tablename__ = 'officers'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(100))
    year: Mapped[str] = mapped_column(db.String(20))  # class standing, e.g. "Junior" (legacy data)
    major: Mapped[str] = mapped_column(db.String(100))
    position: Mapped[int]  # index into helpers.POSITIONS
    image_url: Mapped[str] = mapped_column(db.String(255))
    quote: Mapped[Optional[str]] = mapped_column(db.Text)
    description: Mapped[Optional[str]] = mapped_column(db.Text)
    display_order: Mapped[int] = mapped_column(default=0)  # content.yaml list order, for tie-break within a position
    # Vestigial column from the legacy schema (unused by the site). The old DB declares it
    # NOT NULL with no default, so we keep it on the model with a '' default so inserts succeed.
    href: Mapped[Optional[str]] = mapped_column(db.String(255), default='')


class Family(db.Model):
    __tablename__ = 'families'

    id: Mapped[int] = mapped_column(primary_key=True)
    family_name: Mapped[str] = mapped_column(db.String(100))
    family_head1: Mapped[str] = mapped_column(db.String(100))
    family_head2: Mapped[str] = mapped_column(db.String(100))
    family_head_intern: Mapped[Optional[str]] = mapped_column(db.String(100))
    description: Mapped[str] = mapped_column(db.Text)
    image_url: Mapped[str] = mapped_column(db.String(255))

    def heads(self):
        names = [self.family_head1, self.family_head2]
        if self.family_head_intern:
            names.append(self.family_head_intern)
        return ' & '.join(n for n in names if n)


class Testimonial(db.Model):
    __tablename__ = 'testimonials'
    __test__ = False  # keep pytest from collecting this as a test class

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(100))
    position: Mapped[str] = mapped_column(db.String(200))  # free text, e.g. "Historian Officer, President"
    question: Mapped[str] = mapped_column(db.Text)
    response: Mapped[str] = mapped_column(db.Text)
    image_url: Mapped[Optional[str]] = mapped_column(db.String(255))


class CabinetMember(db.Model):
    """A cabinet member (current, alumni, or future) in the big/little lineage.

    Self-referential: `big_id` points at this member's big (mentor); `littles` are the
    members whose big is this one. Each member has at most one big, so the whole set forms
    a forest of trees — that is what the public /alumni page draws as a lineage map.
    This is a separate concept from the `officers` roster: officers are only the *current*
    cabinet shown on the Officers page, whereas this table spans every cabinet year.
    """
    __tablename__ = 'cabinet_members'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(100))
    grad_year: Mapped[Optional[int]]                                  # real graduation year (filter facet)
    role: Mapped[Optional[str]] = mapped_column(db.String(200))      # free text, e.g. "President, Treasurer"
    major: Mapped[Optional[str]] = mapped_column(db.String(100))
    instagram: Mapped[Optional[str]] = mapped_column(db.String(100))  # handle, stored without a leading '@'
    email: Mapped[Optional[str]] = mapped_column(db.String(255))
    linkedin: Mapped[Optional[str]] = mapped_column(db.String(255))   # canonical profile URL
    bio: Mapped[Optional[str]] = mapped_column(db.Text)
    image_url: Mapped[Optional[str]] = mapped_column(db.String(255))
    big_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey('cabinet_members.id'))
    # Intern class = the semester this member joined cabinet (their first, intern semester).
    intern_season: Mapped[Optional[str]] = mapped_column(db.String(10))
    intern_year: Mapped[Optional[int]]

    big: Mapped[Optional['CabinetMember']] = relationship(
        'CabinetMember', remote_side='CabinetMember.id', back_populates='littles')
    littles: Mapped[list['CabinetMember']] = relationship(
        'CabinetMember', back_populates='big')
    # Positions this member held, one row per (position, semester). Deleting a member
    # deletes its terms; clearing the collection deletes the removed rows.
    terms: Mapped[list['CabinetTerm']] = relationship(
        'CabinetTerm', back_populates='member', cascade='all, delete-orphan')


class CabinetTerm(db.Model):
    """One position a cabinet member held in one semester.

    A member has many terms, which is what powers the 'Position' lineage on /alumni: members are
    grouped by position and chained in semester order. A person who held several positions shows up
    in each of those position lineages.
    """
    __tablename__ = 'cabinet_terms'

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(db.ForeignKey('cabinet_members.id'))
    position: Mapped[int]                                # index into helpers.POSITIONS
    season: Mapped[str] = mapped_column(db.String(10))  # 'Fall' | 'Spring' | 'Summer'
    year: Mapped[int]

    member: Mapped['CabinetMember'] = relationship('CabinetMember', back_populates='terms')
