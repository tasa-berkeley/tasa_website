"""Canonical UC Berkeley undergraduate majors, grouped by college/division (the "category").

Reflects the Berkeley Academic Guide undergraduate catalog. The admin major picker offers these as
optgroups so majors are entered consistently (e.g. "Applied Mathematics", not "Applied Math"; "Data
Science", not "DS"), and the /alumni page can organize the graph by major or by major *field*
(category). To add a major, drop its exact catalog name under the right category below.
"""

# Ordered so the admin dropdown reads naturally. Category name -> majors offered under it.
MAJOR_CATEGORIES = {
    'Engineering': [
        'Aerospace Engineering',
        'Bioengineering',
        'Civil Engineering',
        'Electrical Engineering and Computer Sciences',
        'Engineering Mathematics and Statistics',
        'Engineering Physics',
        'Environmental Engineering Science',
        'Industrial Engineering and Operations Research',
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
        'Mathematics',
        'Physics',
    ],
    'Biological Sciences': [
        'Integrative Biology',
        'Molecular and Cell Biology',
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
        'Ethnic Studies',
        'Gender and Women’s Studies',
        'Geography',
        'Global Studies',
        'History',
        'Interdisciplinary Studies Field',
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
        'Comparative Literature',
        'East Asian Languages and Cultures',
        'English',
        'Film and Media',
        'French',
        'German',
        'Italian Studies',
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
    ],
}

MAJOR_NAMES = [m for majors in MAJOR_CATEGORIES.values() for m in majors]
_MAJOR_TO_CATEGORY = {m: cat for cat, majors in MAJOR_CATEGORIES.items() for m in majors}


def major_category(name):
    """Category (college/division) for a canonical major name, or '' if unknown."""
    return _MAJOR_TO_CATEGORY.get((name or '').strip(), '')


def is_known_major(name):
    return (name or '').strip() in _MAJOR_TO_CATEGORY
