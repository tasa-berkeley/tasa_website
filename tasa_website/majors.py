"""Canonical UC Berkeley undergraduate majors, grouped by college/division (the "category").

Compiled from the UC Berkeley Office of Undergraduate Admissions majors list + the Academic Guide
(reflects majors through the 2024–25 catalog, including newer ones like Neuroscience, Marine Science,
Energy Engineering, and Education Sciences). Within-major concentrations/emphases (e.g. the MCB tracks,
individual Scandinavian/Slavic languages) and "Undeclared" placeholders are folded into their parent
major to keep the picker usable. The admin major dropdown offers these as optgroups so majors are
entered consistently ("Data Science", not "DS"), and /alumni can organize by Major or Major *field*.
To add a major, drop its exact catalog name under the right category below.
"""

# Ordered so the admin dropdown reads naturally. Category name -> majors offered under it.
MAJOR_CATEGORIES = {
    'Engineering': [
        'Aerospace Engineering',
        'Bioengineering',
        'Civil Engineering',
        'Electrical Engineering and Computer Sciences',
        'Energy Engineering',
        'Engineering Mathematics and Statistics',
        'Engineering Physics',
        'Environmental Engineering Science',
        'Industrial Engineering and Operations Research',
        'Management, Entrepreneurship, and Technology (MET)',
        'Materials Science and Engineering',
        'Mechanical Engineering',
        'Nuclear Engineering',
    ],
    'Computing & Data Science': [
        'Computer Science',
        'Data Science',
        'Statistics',
    ],
    'Chemistry': [
        'Chemical Biology',
        'Chemical Engineering',
        'Chemistry',
    ],
    'Mathematical & Physical Sciences': [
        'Applied Mathematics',
        'Astrophysics',
        'Earth and Planetary Science',
        'Geophysics',
        'Marine Science',
        'Mathematics',
        'Physics',
    ],
    'Biological Sciences': [
        'Integrative Biology',
        'Molecular and Cell Biology',
        'Neuroscience',
        'Public Health',
    ],
    'Natural Resources': [
        'Conservation and Resource Studies',
        'Ecosystem Management and Forestry',
        'Environmental Economics and Policy',
        'Environmental Sciences',
        'Genetics and Plant Biology',
        'Microbial Biology',
        'Molecular Environmental Biology',
        'Nutritional Sciences',
        'Society and Environment',
    ],
    'Social Sciences': [
        'African American Studies',
        'American Studies',
        'Anthropology',
        'Asian American and Asian Diaspora Studies',
        'Chicanx and Latinx Studies',
        'Cognitive Science',
        'Development Studies',
        'Economics',
        'Education Sciences',
        'Ethnic Studies',
        "Gender and Women's Studies",
        'Geography',
        'Global Studies',
        'History',
        'Interdisciplinary Studies',
        'Latin American Studies',
        'Legal Studies',
        'Linguistics',
        'Media Studies',
        'Middle Eastern Studies',
        'Native American Studies',
        'Peace and Conflict Studies',
        'Political Economy',
        'Political Science',
        'Psychology',
        'Social Welfare',
        'Sociology',
    ],
    'Arts & Humanities': [
        'Ancient Greek and Roman Studies',
        'Art History',
        'Celtic Studies',
        'Comparative Literature',
        'Dance and Performance Studies',
        'Dutch Studies',
        'East Asian Languages and Cultures',
        'East Asian Religion, Thought, and Culture',
        'English',
        'Film and Media',
        'French',
        'German',
        'Italian Studies',
        'Middle Eastern Languages and Cultures',
        'Music',
        'Near Eastern Civilizations',
        'Philosophy',
        'Practice of Art',
        'Rhetoric',
        'Scandinavian',
        'Slavic Languages and Literatures',
        'South and Southeast Asian Studies',
        'Spanish and Portuguese',
        'Theater and Performance Studies',
    ],
    'Environmental Design': [
        'Architecture',
        'Landscape Architecture',
        'Sustainable Environmental Design',
        'Urban Studies',
    ],
    'Business': [
        'Business Administration',
        'Global Management Program',
    ],
}

MAJOR_NAMES = [m for majors in MAJOR_CATEGORIES.values() for m in majors]
_MAJOR_TO_CATEGORY = {m: cat for cat, majors in MAJOR_CATEGORIES.items() for m in majors}


def major_category(name):
    """Category (college/division) for a canonical major name, or '' if unknown."""
    return _MAJOR_TO_CATEGORY.get((name or '').strip(), '')


def is_known_major(name):
    return (name or '').strip() in _MAJOR_TO_CATEGORY
