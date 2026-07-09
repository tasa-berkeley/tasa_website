from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

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
